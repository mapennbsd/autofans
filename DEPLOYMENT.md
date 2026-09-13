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
