#!/bin/bash

# Directories and paths
LOG_DIR="./trader_logs"
PID_DIR="./pids"
SCRIPT_DIR="traders"
PYTHON_BIN="python3"
CRON_SCHEDULE="0 0 * * *"  # Daily at midnight for get_status.py
SCRIPT_PATH="./scripts/get_status.py"
STATUS_LOG_FILE="./stats/status.log"
CRON_JOB="$CRON_SCHEDULE $PYTHON_BIN $SCRIPT_PATH >> $STATUS_LOG_FILE 2>&1"

# Ensure directories exist
mkdir -p "$LOG_DIR" "$PID_DIR"

# Function to check if an array contains a value
contains_element () {
  local e match="$1"
  shift
  for e; do [[ "$e" == "$match" ]] && return 0; done
  return 1
}

# Start a specific script
start_script() {
  script_name=$(basename "$1")
  out_file="$LOG_DIR/${script_name%.*}.out"
  touch "$out_file"
  echo "Starting $script_name..."
  module_path="${1%.py}"
  module_name="${module_path//\//.}"
  nohup $PYTHON_BIN -u -m $module_name >> $out_file 2>&1 &
  echo $! > "$PID_DIR/${script_name%.*}.pid"
  printf "%s started with PID %s.\n\n" "$script_name" "$(cat "$PID_DIR/${script_name%.*}.pid")"
}

# Stop a specific script
stop_script() {
  script_name=$(basename "$1")
  pid_file="$PID_DIR/${script_name%.*}.pid"
  if [ -f "$pid_file" ]; then
    PID=$(cat "$pid_file")
    echo "Stopping script with PID $PID..."
    kill "$PID"
    rm "$pid_file"
    printf "Script %s stopped.\n\n" "$script_name"
  else
    echo "PID file for $script_name does not exist. Script is not running or was already stopped."
  fi
}


# Start all scripts, excluding specified exceptions
start_scripts() {
  echo "Starting scripts in $SCRIPT_DIR"
  for script in $SCRIPT_DIR/*.py; do
    script_name=$(basename "$script" .py)
    if contains_element "$(basename "$script_name")" "$@"; then
      echo "Skipping $(basename "$script")"
      continue
    fi
    start_script "$script"
  done
}

# Stop all scripts, excluding specified exceptions
stop_scripts() {
  echo "Stopping scripts, excluding specified exceptions..."
  for pid_file in $PID_DIR/*.pid; do
    script_name="${pid_file#$PID_DIR/}"
    script_name="${script_name%.pid}.py"
    if contains_element "$script_name" "$@"; then
      echo "Skipping stop for $script_name"
      continue
    fi
    stop_script "$SCRIPT_DIR/$script_name"
  done
}

# Restart all scripts, excluding specified exceptions
restart_scripts() {
  stop_scripts "$@"
  start_scripts "$@"
}

# Cron job management for get_status.py
manage_cron_job() {
  action="$1"
  case "$action" in
    start)
      echo "Setting up daily cron job for get_status.py..."
      (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
      echo "Cron job added."
      ;;
    stop)
      echo "Removing cron job for get_status.py..."
      crontab -l | grep -v "$SCRIPT_PATH" | crontab -
      echo "Cron job removed."
      ;;
    *)
      echo "Invalid action for manage_cron_job: $action"
      exit 1
      ;;
  esac
}

# Main command handling
case "$1" in
  start)
    shift
    if [ "$1" == "get_status" ]; then
      manage_cron_job start
    else
      start_scripts "$@"
    fi
    ;;
  stop)
    shift
    if [ "$1" == "get_status" ]; then
      manage_cron_job stop
    else
      stop_scripts "$@"
    fi
    ;;
  restart)
    shift
    if [ "$1" == "get_status" ]; then
      manage_cron_job stop
      manage_cron_job start
    else
      restart_scripts "$@"
    fi
    ;;
  -s) # Start a specific script
    shift
    start_script "$SCRIPT_DIR/$1.py"
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|-s script_name} [exceptions...]"
    exit 1
    ;;
esac
