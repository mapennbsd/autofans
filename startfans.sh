#!/bin/sh
#
# Starts the autofans control loop in the background, rotating any
# existing log first. Safe to re-run: refuses to start a second copy
# if one is already running.

set -eu

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
LOGDIR="$SCRIPT_DIR/log"
LOGFILE="$LOGDIR/faninfo.log"
PIDFILE="$SCRIPT_DIR/autofans.pid"
RUNFILE="$SCRIPT_DIR/autofans.py"

mkdir -p "$LOGDIR"

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "autofans is already running (pid $(cat "$PIDFILE"))" >&2
    exit 1
fi

if [ -f "$LOGFILE" ]; then
    mv "$LOGFILE" "$LOGFILE.$(date +%Y%m%d-%H%M%S)"
fi

touch "$LOGFILE"

nohup python3 "$RUNFILE" > "$LOGFILE" 2>&1 &
echo $! > "$PIDFILE"

exit 0
