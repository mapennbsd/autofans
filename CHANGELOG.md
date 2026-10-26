# Changelog

## 1.3.0 — 2026-10-26

- Write the last sample to `/run/autofans/state` (JSON: time, temperature,
  commanded PWM, RPM, error) after every reading, atomically, for underdog's
  `fans` check and the racks dashboard. A failed write is logged once and
  never stops fan control.
- No change to the control policy; 3 new tests (16 in all).

## 1.2.0 — 2026-10-25

- Rebuild for dawg on Debian 13 trixie (arm64, Python 3.13).
- Add `requirements.txt`: current drivers (Blinka 9.2.0, EMC2101 1.2.15,
  MCP9808 3.3.32) pinned with PyPI hashes, installed `--no-deps` into a venv
  with `--system-site-packages`. `RPi.GPIO` comes from apt's
  `python3-rpi-lgpio`, so nothing compiles.
- Service: add the `gpio` group (rpi-lgpio opens `/dev/gpiochip0`), and a
  runtime directory for lgpio's notify FIFO via `LG_WD` (`/opt` is read-only
  under `ProtectSystem=strict`).
- Install is now the ansible repo's `dawg.yaml`; the README's manual steps
  are replaced by it.
- No change to the control program.

## 1.1.0 — 2026-09-13

- Command full fan speed before temperature sensor initialization, fixing hot startup.
- Retry hardware errors with a best-effort full-speed fallback and recovery logging.
- Preserve temperature bands and add 1°F cooling hysteresis.
- Log speed changes with temperature, previous/new PWM, and unsettled RPM;
  report an hourly heartbeat during steady operation.
- Replace background launching with a systemd service that restarts after failure.
- Add 13 hardware-free tests and deployment and rollback instructions.

### Migration

Install the systemd service and its Python environment as described in README.md.
Remove the old rc.local startup entry and stop the old controller before starting
this service. `startfans.sh` now invokes `sudo systemctl start autofans.service`
and requires the service to be installed.

### Validation

All 13 tests passed on spaceghost and dawg. On dawg, verified live readings,
manual restart, automatic restart after process termination, and quiet logging
through a subsequent sampling interval. Hourly heartbeat timing was tested with
a simulated clock. Reboot and physical airflow checks were not performed.

## 1.0.0 — 2026-08-29

- Initial tagged release with temperature-based fan control, RPM check mode,
  background launcher, and Raspberry Pi setup instructions.
