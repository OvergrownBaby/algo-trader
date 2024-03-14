# algo-trader
An algo trading module based on FutuAPI

## Prerequisites

- Bash shell
- Python environment set up at the specified path
- Trading scripts located within the `./traders` directory for global management

## Setup

`pip install futu-api` 

Ensure the Python virtual environment is properly set up and accessible from the specified paths in the scripts.

Store the trading password for your Futu account as an environment variable (for security reasons).
Linux/MacOS: `export FUTU_TRD_PW='your_password_here'`
Windows: `set FUTU_TRD_PW=your_password_here`

## Usage

### Running traders

- **To Start All Scripts:**

`./run_traders.sh start`

- **To start all but certain scripts**
`./run_traders.sh start real_CN paper_HK`

- **To start a specific script**
`./run_traders.sh -s real_CN`
or `python3 -m traders.paper_MA`

- **To Stop All Scripts:**

`./run_traders.sh stop`

- Exclusions can be specified as additional arguments just like `start`.

- **To Restart All Scripts:**

`./run_traders.sh restart`

- Exclusions can be specified as additional arguments.

### getting daily account status

To export the account status (cash, etc.) of each day to an individual .csv file, use the `run_get_status.sh` script with these options:

- **Start `get_status.py`:**

`./run_get_status.sh start`


- **Stop `get_status.py`:**

`./run_get_status.sh stop`


- **Restart `get_status.py`:**

`./run_get_status.sh restart`


## Directories and Files

- **Logs Directory**: Output and error logs are saved in `./trader_logs`. Inside, for each trader there are two logs, `{trader_name}.log` and `{trader_name}_events.log`. The first tracks everything including every price update, while the second only tracks certain events such as MACD becoming positive. Custom events can be added using `event_logger.info(...)` in the trader script.


- **Transactions log**: Logs for transactions only are in `./transactions`

- **PID Directory**: Process IDs are tracked in `./pids` for global script management and in `./script.pid` for `get_status.py`.


## Customization

Modify the variables `LOG_DIR`, `PID_DIR`, and `SCRIPT_DIR` in `run_traders.sh`, and adjust paths in `run_get_status.sh` as needed to fit your directory structure and setup. Additional model parameters can be adjusted as global variables.

## Contributing

Contributions are welcome! Please fork the repository and submit pull requests with any enhancements or fixes.

## License

MIT
