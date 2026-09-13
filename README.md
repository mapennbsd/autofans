# autofans

Version **1.1.0** — see [release notes](CHANGELOG.md).

Controls network rack fans on the Raspberry Pi **dawg**, reading an MCP9808
sensor and driving an EMC2101 controller over I2C. **spaceghost** is the
workstation for editing and running tests; do not install the service there.

## Control behavior

The controller is commanded to 100% before the temperature sensor is initialized.
A valid temperature then selects the fan setting. Readings are taken every 60
seconds. Routine logs are emitted only when the commanded PWM changes, with
temperature, previous/new PWM, and RPM immediately after the command (before
the fan settles). Startup, errors, and recovery are always logged. After an hour
without a speed-change or recovery log, a heartbeat reports temperature, PWM,
and RPM. Sensor and RPM checks still run every minute. These thresholds preserve the original integer-truncated behavior:

| Temperature (°F) | Fan PWM |
| --- | --- |
| Below 75 | 25% |
| 75 to below 81 | 50% |
| 81 to below 83 | 60% |
| 83 to below 85 | 70% |
| 85 to below 87 | 80% |
| 87 to below 89 | 90% |
| 89 and above | 100% |

Speed increases at the listed thresholds. While cooling, speed decreases only
below the relevant threshold minus 1°F. For example, 50% drops to 25% below
74°F. Large temperature drops can cross multiple bands in one sample. The first
valid reading after startup or a failure uses the table without hysteresis.

Temperature, RPM, or PWM access errors are logged and trigger an attempt to
command 100%, followed by another attempt after 60 seconds. RPM is read after
the temperature-based command so logging cannot prevent that command. If the
controller is unreachable, software cannot guarantee the actual fan setting.
Initialization failures exit so systemd can restart the process after 10 seconds.

The current installation uses two Noctua 5V fans in an open rack, with the
sensor on the heatsink case of a fanless firewall. Tune `THRESHOLDS_F`, `SPEEDS`,
and `HYSTERESIS_F` in `autofans.py` to suit the sensor location.

## Install on dawg

Copy this repository to dawg first. Run the following commands there from the
repository directory. The service uses `/opt/autofans` and a dedicated account.

1. Install prerequisites and enable I2C:

   ```sh
   sudo apt update
   sudo apt install python3-venv python3-pip i2c-tools
   sudo raspi-config
   ```

   Select **Interface Options → I2C**, enable it, and reboot if prompted.
   Check the wiring and device visibility with `i2cdetect -y 1`.

2. Create a service account (once) and install the program and drivers:

   ```sh
   sudo useradd --system --no-create-home --shell /usr/sbin/nologin autofans
   sudo install -d -m 755 /opt/autofans
   sudo install -m 644 autofans.py /opt/autofans/autofans.py
   sudo python3 -m venv /opt/autofans/.venv
   sudo /opt/autofans/.venv/bin/pip install adafruit-circuitpython-emc2101 adafruit-circuitpython-mcp9808
   ```

   The service grants the `i2c` supplementary group. Confirm that this group has
   access to dawg's `/dev/i2c-*` device before starting the service.

3. Migrate the old startup method before enabling the new service:

   Remove the old `startfans.sh` entry from `/etc/rc.local` and any equivalent
   cron startup entries. Find existing controllers with:

   ```sh
   pgrep -af '[a]utofans.py'
   ```

   Stop the identified old control process using `sudo kill <PID>`. Check the
   command line before selecting the PID; do not rely on an old PID file.
   Perform the next step promptly to resume temperature control.

4. Install and enable the service:

   ```sh
   sudo install -m 644 autofans.service /etc/systemd/system/autofans.service
   sudo systemctl daemon-reload
   sudo systemctl enable --now autofans.service
   sudo systemctl status autofans.service
   sudo journalctl -u autofans.service -n 30 --no-pager
   ```

   Confirm successful temperature readings and physically verify fan operation.
   Systemd manages one service process, restarts it after failure, and captures
   logs in the journal. Avoid launching additional control loops manually.
   `startfans.sh` is now a compatibility wrapper for
   `sudo systemctl start autofans.service`; repeated starts use the same service.

## Operation on dawg

```sh
sudo systemctl restart autofans.service
sudo systemctl stop autofans.service
sudo journalctl -u autofans.service -f
```

Stopping the service stops temperature adjustments; it does not command a new
fan setting. A successful service start alone does not confirm sensor health:
check the journal for readings and errors.

Read current RPM without starting a control loop or initializing the MCP9808:

```sh
sudo /opt/autofans/.venv/bin/python /opt/autofans/autofans.py --check
```

For updates, copy the revised Python file into `/opt/autofans` using the install
command above, then restart the service. Reinstall the unit and run
`systemctl daemon-reload` if the service definition changes.

If startup fails, inspect `systemctl status` and the journal. Check driver
installation in `/opt/autofans/.venv`, I2C enablement, permissions, board power,
and wiring. Repeated full-speed errors require checking the controller itself.

## Local tests on spaceghost

No hardware drivers or Raspberry Pi access are needed:

```sh
python3 -m unittest discover -s tests -v
sh -n startfans.sh
```

Tests cover startup, every temperature boundary, hysteresis, invalid readings,
and simulated sensor, controller, and tachometer failures. Hardware validation
and service installation must take place separately on dawg.
