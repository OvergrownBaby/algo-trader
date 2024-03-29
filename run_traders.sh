#!/bin/bash

# Directories and paths
LOG_DIR="./trader_logs"
PID_DIR="./pids"
SCRIPT_DIR="traders"
PYTHON_BIN="python3"

# Ensure log and PID directories exist
mkdir -p "$PID_DIR"

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
  log_file="$LOG_DIR/${script_name%.*}.log"
  pid_file="$PID_DIR/${script_name%.*}.pid"
  out_file="$LOG_DIR/${script_name%.*}.out"
  touch "$log_file" "$pid_file" "$out_file"
  echo "Starting $script_name..."
  module_path="${1%.py}"
  module_name="${module_path//\//.}"
  # nohup $PYTHON_BIN -u -m $module_name >> "$log_file" 2>&1 & # Use if log without logging module
  nohup $PYTHON_BIN -u -m $module_name >> $out_file 2>&1 &
  echo $! > "$pid_file"
  printf "%s started with PID %s.\n\n" "$script_name" "$(cat "$pid_file")"
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

# Determine action based on command-line argument
case "$1" in
  start)
    shift
    start_scripts "$@"
    ;;
  stop)
    shift
    stop_scripts "$@"
    ;;
  restart)
    shift
    restart_scripts "$@"
    ;;
  -s) # Start a specific script
    if [ -n "$2" ]; then
      specific_script="$SCRIPT_DIR/$2.py"
      if [ -f "$specific_script" ]; then
        start_script "$specific_script"
      else
        echo "Specified script does not exist: $specific_script"
        exit 1
      fi
    else
      echo "No script specified. Usage: $0 -s script_name.py"
      exit 1
    fi
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|-s script_name.py} [exceptions...]"
    exit 1
    ;;
esac
