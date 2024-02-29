# algo-trader
An algo trading script based on FutuAPI

# Algo-Trader Script Management

This repository contains shell scripts designed for managing the execution of Python scripts related to algorithmic trading, automating the processes of starting, stopping, and restarting trading bots and utility scripts.

## Features

#### Global Script Management
- Start, stop, or restart all trading scripts within the `./traders` directory, with options to exclude specific scripts.

#### Individual Script Management
- Provides capabilities to manage the `get_status.py` script individually, facilitating control over its execution.

## Prerequisites

- Bash shell
- Python environment set up at the specified path
- Trading scripts located within the `./traders` directory for global management

## Setup

Ensure the Python virtual environment is properly set up and accessible from the specified paths in the scripts.

## Usage

### Managing All Trading Scripts

To manage all trading scripts, use the `run_traders.sh` script with the following commands:

- **To Start All Scripts:**

./run_traders.sh start

- Exclusions can be specified as additional arguments.

- **To Restart All Scripts:**

./run_traders.sh stop

- Exclusions can be specified as additional arguments.

- **To Restart All Scripts:**

./run_traders.sh restart

- Exclusions can be specified as additional arguments.

- **To Start a Specific Script:**

./run_traders.sh -s script_name.py


### Managing `get_status.py`

For individual management of the `get_status.py` script, use the `run_get_status.sh` script with these options:

- **Start `get_status.py`:**

./run_get_status.sh start


- **Stop `get_status.py`:**

./run_get_status.sh stop


- **Restart `get_status.py`:**

./run_get_status.sh restart


## Directories and Files

- **Logs Directory**: Output and error logs are saved in `./logs`.

LOG_DIR="./logs"

- **PID Directory**: Process IDs are tracked in `./pids` for global script management and in `./script.pid` for `get_status.py`.

PID_DIR="./pids"


## Customization

Modify the variables `LOG_DIR`, `PID_DIR`, and `SCRIPT_DIR` in `run_traders.sh`, and adjust paths in `run_get_status.sh` as needed to fit your directory structure and setup.

## Contributing

Contributions are welcome! Please fork the repository and submit pull requests with any enhancements or fixes.

## License

MIT
