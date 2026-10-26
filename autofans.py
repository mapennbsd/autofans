#!/usr/bin/env python3
"""Temperature-driven rack cooling on dawg; policy is testable without I2C."""

import argparse
import json
import logging
import math
import os
import time

LOG = logging.getLogger(__name__)
INTERVAL_SECONDS = 60
HEARTBEAT_SECONDS = 3600
HYSTERESIS_F = 1.0
# Explicit equivalents of the original integer-truncated Fahrenheit bands.
THRESHOLDS_F = (75, 81, 83, 85, 87, 89)
SPEEDS = (25, 50, 60, 70, 80, 90, 100)
# The last sample, for monitoring (underdog's fans check): rewritten every
# loop, so its age says whether the loop is alive.  The runtime directory
# goes when the service stops, and the file with it.
STATE_PATH = "/run/autofans/state"


def select_speed(temp_f, previous=None):
    """Raise immediately; lower only below the crossed boundary minus 1 F."""
    if not math.isfinite(temp_f):
        raise ValueError("Temperature must be finite")
    target = sum(temp_f >= threshold for threshold in THRESHOLDS_F)
    if previous is None or SPEEDS[target] >= previous:
        return SPEEDS[target]
    current = SPEEDS.index(previous)
    while current > target and temp_f < THRESHOLDS_F[current - 1] - HYSTERESIS_F:
        current -= 1
    return SPEEDS[current]


def full_speed(controller):
    """Best effort only: a disconnected controller cannot be commanded."""
    try:
        controller.manual_fan_speed = 100
        LOG.warning("Commanded full fan speed")
        return True
    except Exception:
        LOG.exception("Cannot command full speed: fan controller is unreachable or failed")
        return False


def write_state(path, temp_f, pwm, rpm, error):
    """Replace the state file in one step, so a reader never sees half of it.
    True when written; a failure is the caller's to report, never fatal."""
    state = {
        "time": round(time.time(), 3),
        "temperature_c": (round((temp_f - 32) * 5 / 9, 3)
                          if temp_f is not None and math.isfinite(temp_f) else None),
        "pwm": pwm,
        "rpm": rpm,
        "error": error,
    }
    tmp = path + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(state, f)
            f.write("\n")
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def run(controller, sensor_factory, sleep=time.sleep, monotonic=time.monotonic,
        state_path=None):
    # Write before constructing or reading the temperature sensor.
    if not full_speed(controller):
        raise RuntimeError("Initial full-speed command failed")
    LOG.info("Fan control started; commanded PWM: 100%")
    previous = None
    commanded = 100
    sensor = None
    failed = False
    last_status = monotonic()
    state_failed = False
    while True:
        old_command = commanded
        temp_f = rpm = error = None
        try:
            if sensor is None:
                sensor = sensor_factory()
            temp_f = sensor.temperature * 9 / 5 + 32
            speed = select_speed(temp_f, previous)
            if speed != previous:
                controller.manual_fan_speed = speed
            commanded = speed
            previous = speed
        except Exception as exc:
            LOG.exception("Temperature control failed; retrying in %s seconds", INTERVAL_SECONDS)
            error = "temperature control failed: %s" % (exc,)
            commanded = 100 if full_speed(controller) else None
            previous = None
            sensor = None
            failed = True
        else:
            # Read RPM every sample even when quiet, preserving fault detection.
            rpm_failed = False
            try:
                rpm = controller.fan_speed
            except Exception as exc:
                LOG.exception("RPM read failed; retrying in %s seconds", INTERVAL_SECONDS)
                rpm_failed = True
                error = "RPM read failed: %s" % (exc,)
            shown = "unavailable" if rpm is None else rpm
            now = monotonic()
            if old_command != speed:
                LOG.info("Speed change: temperature %.2f F; PWM %s%% -> %s%%; "
                         "RPM immediately after command (not settled): %s",
                         temp_f, old_command if old_command is not None else "unknown", speed, shown)
                last_status = now
            if rpm_failed:
                commanded = 100 if full_speed(controller) else None
                previous = None
                failed = True
            elif failed:
                LOG.info("Fan control recovered: temperature %.2f F; PWM %s%%; RPM %s",
                         temp_f, speed, shown)
                failed = False
                last_status = now
            elif now - last_status >= HEARTBEAT_SECONDS:
                LOG.info("Heartbeat: temperature %.2f F; PWM %s%%; RPM %s", temp_f, speed, shown)
                last_status = now
        if state_path is not None:
            if write_state(state_path, temp_f, commanded, rpm, error):
                if state_failed:
                    LOG.info("State file %s written again", state_path)
                state_failed = False
            elif not state_failed:
                LOG.warning("Cannot write the state file %s; fan control goes on", state_path)
                state_failed = True
        sleep(INTERVAL_SECONDS)


def main():
    parser = argparse.ArgumentParser(description="Monitor temperature and control fan speed.")
    parser.add_argument("--check", action="store_true",
                        help="print current fan RPM without running the control loop")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # Import hardware drivers only when actually running on the Raspberry Pi.
    import board
    from adafruit_emc2101 import EMC2101
    import adafruit_mcp9808

    i2c = board.I2C()
    controller = EMC2101(i2c)
    if args.check:
        print("Current fan RPM:", controller.fan_speed, flush=True)
        return
    run(controller, lambda: adafruit_mcp9808.MCP9808(i2c),
        state_path=os.environ.get("AUTOFANS_STATE", STATE_PATH))


if __name__ == "__main__":
    main()
