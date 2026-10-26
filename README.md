# autofans

Version **1.3.0** — see [release notes](CHANGELOG.md).

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

## State file

After every sample the service replaces `/run/autofans/state` (`AUTOFANS_STATE`
overrides the path) with one line of JSON: `time` (Unix seconds),
`temperature_c`, `pwm` (the commanded percentage), `rpm` and `error`. A value
it could not read is `null`, and `error` says why; after a failure `pwm` is
the 100% fallback, or `null` if that command failed too. The file is written
to a temporary name and renamed, so a reader never sees half of it, and it
goes when the service stops (systemd removes the runtime directory). A failed
write is logged once and never stops fan control. underdog's `fans` check
reads it: an old file means the loop has stopped.

The current installation uses two Noctua 5V fans in an open rack, with the
sensor on the heatsink case of a fanless firewall. Tune `THRESHOLDS_F`, `SPEEDS`,
and `HYSTERESIS_F` in `autofans.py` to suit the sensor location.

## Install on dawg

dawg is built by `dawg.yaml` in the ansible repo, which is the runbook:

```sh
./play.sh dawg.yaml --check --diff -K
./play.sh dawg.yaml -K
```

It enables I2C (`raspi-config nonint do_i2c 0`), installs `i2c-tools`,
`python3-venv` and `python3-rpi-lgpio` from apt, creates the `autofans` system
account, checks out a pinned commit of this repository into `/opt/autofans`,
builds `/opt/autofans/.venv` with `--system-site-packages`, installs
`requirements.txt` there (wheels only, every hash required, PyPI only), runs
the tests, and installs and starts `autofans.service`.

Why a venv that sees the system packages: Debian 13 marks the system Python
externally managed (PEP 668), and Blinka on a Pi 3 imports `RPi.GPIO`. PyPI's
RPi.GPIO and lgpio have no wheels for this platform and would compile, so
`RPi.GPIO` comes from apt (`python3-rpi-lgpio`, a shim over `python3-lgpio`)
and everything else from the pinned wheels. See `requirements.txt`.

Check the wiring and device visibility with `i2cdetect -y 1`: the MCP9808 is
usually at 0x18 and the EMC2101 at 0x4c. Then confirm readings in the journal
and physically verify fan operation.

To deploy a change here: commit and push it, set `autofans_version` in
`dawg.yaml` to the new commit, and run the playbook. It restarts the service
when the program or unit changes.

## Operation on dawg

`startfans.sh` is only a wrapper for `sudo systemctl start autofans.service`,
kept for old habits; nothing calls it.

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

For updates, see "To deploy a change here" above.

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
