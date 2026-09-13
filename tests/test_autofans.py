import unittest
from unittest.mock import Mock, PropertyMock, patch

import autofans


class StopLoop(BaseException):
    pass


class FanTests(unittest.TestCase):
    def test_boundaries(self):
        for boundary, below, above in zip(autofans.THRESHOLDS_F,
                                          autofans.SPEEDS, autofans.SPEEDS[1:]):
            with self.subTest(boundary=boundary):
                self.assertEqual(autofans.select_speed(boundary - .01), below)
                self.assertEqual(autofans.select_speed(boundary), above)
                self.assertEqual(autofans.select_speed(boundary, below), above)
                self.assertEqual(autofans.select_speed(boundary - 1, above), above)
                self.assertEqual(autofans.select_speed(boundary - 1.01, above), below)

    def test_large_changes_and_invalid_readings(self):
        self.assertEqual(autofans.select_speed(100, 25), 100)
        self.assertEqual(autofans.select_speed(70, 100), 25)
        for value in (float('nan'), float('inf'), -float('inf')):
            with self.assertRaises(ValueError):
                autofans.select_speed(value)

    def exercise(self, temperatures, rpm_failure=False, write_failures=None):
        controller = Mock()
        writes = PropertyMock(side_effect=write_failures)
        type(controller).manual_fan_speed = writes
        type(controller).fan_speed = PropertyMock(
            side_effect=OSError('tachometer') if rpm_failure else None, return_value=500)
        sensor = Mock()
        type(sensor).temperature = PropertyMock(side_effect=temperatures)
        def make_sensor():
            self.assertEqual(writes.call_args_list[0].args, (100,))
            return sensor
        sleeps = Mock(side_effect=[None] * (len(temperatures) - 1) + [StopLoop()])
        with patch.object(autofans, 'LOG'):
            with self.assertRaises(StopLoop):
                autofans.run(controller, make_sensor, sleeps)
        self.assertTrue(all(call.args == (60,) for call in sleeps.call_args_list))
        return [call.args[0] for call in writes.call_args_list]

    def test_hot_start(self):
        self.assertEqual(self.exercise([32]), [100, 100])

    def test_sensor_failure_and_recovery(self):
        self.assertEqual(self.exercise([22, OSError('sensor'), 22]), [100, 25, 100, 25])

    def test_rpm_failure_still_applies_temperature_then_fallback(self):
        self.assertEqual(self.exercise([22], rpm_failure=True), [100, 25, 100])

    def test_write_failure_recovers(self):
        self.assertEqual(self.exercise([22, 22], write_failures=[None, OSError(), None, None]),
                         [100, 25, 100, 25])

    def test_initial_controller_failure_exits_for_restart(self):
        controller = Mock()
        type(controller).manual_fan_speed = PropertyMock(side_effect=OSError())
        factory = Mock()
        with patch.object(autofans, 'LOG'), self.assertRaises(RuntimeError):
            autofans.run(controller, factory)
        factory.assert_not_called()

    def test_sensor_initialization_failure_retries(self):
        controller = Mock()
        sensor = Mock(temperature=22)
        factory = Mock(side_effect=[OSError(), sensor])
        with patch.object(autofans, 'LOG'), self.assertRaises(StopLoop):
            autofans.run(controller, factory, Mock(side_effect=[None, StopLoop()]))
        self.assertEqual(factory.call_count, 2)
        self.assertEqual(controller.manual_fan_speed, 25)


class LoggingTests(unittest.TestCase):
    def run_samples(self, temperatures, times, rpms=None):
        controller = Mock()
        tachometer = PropertyMock(side_effect=rpms, return_value=500)
        type(controller).fan_speed = tachometer
        sensor = Mock()
        type(sensor).temperature = PropertyMock(side_effect=temperatures)
        with self.assertLogs(autofans.LOG, level='INFO') as logs:
            with self.assertRaises(StopLoop):
                autofans.run(controller, lambda: sensor,
                             Mock(side_effect=[None] * (len(temperatures) - 1) + [StopLoop()]),
                             Mock(side_effect=times))
        return logs.output, tachometer.call_count

    def test_quiet_samples_and_hourly_heartbeat(self):
        logs, reads = self.run_samples([22] * 4, [0, 0, 60, 3599, 3600])
        self.assertEqual(reads, 4)
        self.assertEqual(sum('Speed change:' in line for line in logs), 1)
        self.assertEqual(sum('Heartbeat:' in line for line in logs), 1)
        self.assertEqual(len(logs), 4)  # full speed, startup, change, heartbeat
        self.assertTrue(any('PWM 100% -> 25%' in line for line in logs))
        self.assertTrue(any('not settled' in line for line in logs))

    def test_hot_start_is_not_logged_as_speed_change(self):
        logs, _ = self.run_samples([32, 32], [0, 0, 60])
        self.assertFalse(any('Speed change:' in line for line in logs))
        self.assertTrue(any('started' in line for line in logs))

    def test_change_resets_heartbeat(self):
        logs, _ = self.run_samples([22, 28, 28, 28], [0, 0, 3500, 3600, 7100])
        self.assertEqual(sum('Speed change:' in line for line in logs), 2)
        self.assertEqual(sum('Heartbeat:' in line for line in logs), 1)

    def test_sensor_failure_and_recovery_are_logged(self):
        logs, _ = self.run_samples([32, OSError('sensor'), 32, 32], [0, 0, 120, 180])
        self.assertTrue(any('Temperature control failed' in line for line in logs))
        self.assertEqual(sum('recovered:' in line for line in logs), 1)
        self.assertFalse(any('Speed change:' in line for line in logs))

    def test_rpm_failure_during_quiet_sample_and_recovery(self):
        logs, reads = self.run_samples([32] * 3, [0, 0, 60, 120], [500, OSError('rpm'), 500])
        self.assertEqual(reads, 3)
        self.assertTrue(any('RPM read failed' in line for line in logs))
        self.assertEqual(sum('recovered:' in line for line in logs), 1)


if __name__ == '__main__':
    unittest.main()
