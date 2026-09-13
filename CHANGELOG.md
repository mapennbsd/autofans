# Changelog

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
