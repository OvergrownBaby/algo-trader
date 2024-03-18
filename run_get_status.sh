#!/bin/bash

# Script to manage a get_status.py script as a daily cron job

CRON_SCHEDULE="0 0 * * *"  # Daily at midnight
SCRIPT_PATH="./scripts/get_status.py"
LOG_FILE="./stats/status.log"
PYTHON_BIN="python3"
CRON_JOB="$CRON_SCHEDULE $PYTHON_BIN $SCRIPT_PATH >> $LOG_FILE 2>&1"

start_script() {
  echo "Running $SCRIPT_PATH once..."
  $PYTHON_BIN $SCRIPT_PATH
  echo "Setting up daily cron job for get_status.py..."
  (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
  echo "Cron job added:"
  crontab -l | grep "$SCRIPT_PATH"
}

stop_script() {
  echo "Removing cron job for get_status.py..."
  crontab -l | grep -v "$SCRIPT_PATH" | crontab -
  echo "Cron job removed."
}

restart_script() {
  stop_script
  start_script
}

case "$1" in
  start)
    start_script
    ;;
  stop)
    stop_script
    ;;
  restart)
    restart_script
    ;;
  *)
    echo "Usage: $0 {start|stop|restart}"
    exit 1
    ;;
esac
