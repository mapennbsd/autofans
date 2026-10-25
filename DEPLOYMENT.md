# dawg deployment — 2026-09-13

Installed `/opt/autofans/autofans.py` and `/etc/systemd/system/autofans.service`
on dawg (Raspbian 11, Python 3.9). The service runs as `autofans` with the `i2c`
supplementary group. It is enabled for boot. Removed the previous rc.local
startup entry and replaced `/home/mapenn/autofans/startfans.sh` with the systemd
wrapper. The old Python file remains in that directory; do not launch it directly.

Backup: `/var/backups/autofans-pre-systemd/` on dawg contains the original
repository, rc.local, and Python package inventory. The new virtual environment
retains the previous driver versions (EMC2101 1.2.1, MCP9808 3.3.19) and their
existing dependency versions. Installed python3-venv; building the existing
RPi.GPIO 0.7.0 required `CFLAGS=-fcommon` with dawg's compiler.

All eight mocked tests passed on dawg; systemd unit validation passed. A manual
service restart succeeded. Killing the main process with SIGKILL triggered an
automatic restart after 10 seconds, followed by a full-speed startup command and
valid readings (81.95°F, commanded 60%, approximately 1,017 RPM).

No reboot or physical airflow inspection was performed. The RPM reading is the
controller's tachometer measurement, not independent confirmation of both fans.

## Check status on dawg

```sh
sudo systemctl status autofans.service
sudo journalctl -u autofans.service -n 30 --no-pager
```

## Roll back on dawg if needed

Stop the new controller before restarting the old one:

```sh
sudo systemctl disable --now autofans.service
sudo cp -a /var/backups/autofans-pre-systemd/rc.local /etc/rc.local
sudo cp -a /var/backups/autofans-pre-systemd/autofans/startfans.sh /home/mapenn/autofans/startfans.sh
/home/mapenn/autofans/startfans.sh
tail -n 10 /home/mapenn/autofans/log/faninfo.log
```

Run the old launcher as `mapenn`. This restores the original boot mechanism;
the staged `/opt/autofans` files can remain in place while the service is disabled.

## Logging update — 2026-09-13

Deployed change-only routine logging plus a heartbeat after one hour without a
speed-change or recovery message. Startup, errors, and recovery remain logged;
hardware sampling remains every 60 seconds. RPM on change messages is explicitly
labelled as immediately after the command, before settling. All 13 tests passed
on both spaceghost and dawg, including simulated elapsed time for heartbeats.

The pre-update script is backed up on dawg at
`/var/backups/autofans-pre-logging/autofans.py`. To roll back only this update:

```sh
sudo cp /var/backups/autofans-pre-logging/autofans.py /opt/autofans/autofans.py
sudo systemctl restart autofans.service
```

# dawg rebuild on Debian 13 trixie — 2026-10-25

dawg's card was reimaged from Raspbian 11 (armv7l, Python 3.9) to Debian 13
trixie (arm64, Python 3.13). The old card's `/opt/autofans`, its venv and
`/var/backups` were not saved, so the 2026-09-13 install above is history; the
rollback steps in it no longer apply.

Installed v1.2.0 (f71937f) with the ansible repo's `dawg.yaml`, which is now
the rebuild runbook: I2C enabled with `raspi-config nonint do_i2c 0` (live, no
reboot), `/opt/autofans` a checkout of that commit, the venv built with
`--system-site-packages`, and `requirements.txt` installed `--no-deps` with
every hash required. The service runs as `autofans` with `i2c` and `gpio`;
lgpio's notify FIFO is in `/run/autofans`.

`i2cdetect -y 1` shows the MCP9808 at 0x18 and the EMC2101 at 0x4c. The
service started at 09:18:22 and commanded 100%. The first two samples were at
or above 88°F, so it stayed at 100% without logging; then:

```
09:20:22 Speed change: temperature 86.34 F; PWM 100% -> 90%; RPM 1427.44
09:21:22 Speed change: temperature 85.78 F; PWM 90% -> 80%; RPM 1308.46
```

Fans heard running. A direct register read of the MCP9808 agreed (30.50°C,
86.9°F at 09:19:50). I2C (`dtparam=i2c_arm=on`, `i2c-dev` in `/etc/modules`)
and the service are enabled for boot; no reboot was performed.

A start that logs only "Fan control started" is normal when the first reading
is 89°F or more: nothing is logged until the speed changes or the hourly
heartbeat.
