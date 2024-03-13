#!/bin/bash

# Script to start or restart a get_status.py script using nohup

PID_FILE="./pids/get_status.pid"
LOG_FILE="./status/status.log"
SCRIPT="get_status"
PYTHON_BIN="python3"

start_script() {
  echo "Starting get_status.py..."
  nohup $PYTHON_BIN -u -m $SCRIPT >> $LOG_FILE 2>&1 &
  echo $! > $PID_FILE
  echo "Script started with PID $(cat $PID_FILE)"
}

stop_script() {
  if [ -f $PID_FILE ]; then
    PID=$(cat $PID_FILE)
    echo "Stopping script with PID $PID..."
    kill $PID
    rm $PID_FILE
    echo "Script stopped."
  else
    echo "Script is not running or PID file is missing."
  fi
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
