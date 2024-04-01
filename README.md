# algo-trader
An algo trading module based on FutuAPI

## Prerequisites

- Bash shell with `crontab` installed

## Setup

`pip install futu-api` 

Store the trading password for your Futu account as an environment variable (for security reasons).
Linux/MacOS: `export FUTU_TRD_PW='your_password_here'`
Windows: `set FUTU_TRD_PW=your_password_here`

## Usage

### Start Trading Scripts
To start all trading scripts:
```./algo-trader.sh start```

To start a specific trading script:
```./algo-trader.sh -s script_name```

To stop all trading scripts:
```./algo-trader.sh stop```

To stop a specific trading script:
```./algo-trader.sh stop script_name```

To restart all trading scripts:
```./algo-trader.sh restart```

To start the daily cron job for get_status.py:
```./algo-trader.sh start get_status```

To stop the cron job:
```./algo-trader.sh stop get_status```

## Contributing

Contributions are welcome! Please fork the repository and submit pull requests with any enhancements or fixes.

## License

MIT
