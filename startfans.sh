#!/bin/sh
# Compatibility entry point; systemd owns the sole background process and logs.
set -eu
exec sudo systemctl start autofans.service
