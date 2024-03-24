# -*- coding: GBK -*-

### Todo
### backtest with joint quant
### create (maybe with a function) a list of traders, the trader.execute() for trader in traders
### figure out how to import, change password access to config file inside project directory but rmb to .gitignore it
### package dependencies so i don't need a venv and can just pip install, then just use PATH variable to run stuff
### one trader per trd_env, market and period. multiple strategies per trader

import os
from futu import *
import logging
from modules.strategies import MACDBaseStrat
from modules.tools import unlock_trade

############################ Global Variables ############################
FUTU_OPEND_ADDRESS = '127.0.0.1'  # Futu OpenD listening address
FUTU_OPEND_PORT = 11111  # Futu OpenD listening port

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRADING_PWD = os.getenv('FUTU_TRD_PW')  # Trading password, used to unlock trading for real trading environment

TRADING_ENVIRONMENT = TrdEnv.SIMULATE  # Trading environment: REAL / SIMULATE
TRADING_MARKET = TrdMarket.HK  # Transaction market authority, used to filter accounts
TRADING_PERIOD = KLType.K_1M  # Underlying trading time period

TRADER_NAME = os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]  # Trader name

############################ Paths ############################
TRANS_LOG_PATH = os.path.join(DIR, 'transactions/transactions.csv') # transaction log path
if not os.path.exists(os.path.dirname(TRANS_LOG_PATH)):
    os.makedirs(os.path.dirname(TRANS_LOG_PATH), exist_ok=True)

TRADER_LOG_DIR = os.path.join(DIR, 'trader_logs')
if not os.path.exists(TRADER_LOG_DIR):
    os.makedirs(TRADER_LOG_DIR, exist_ok=True)

############################ Loggers ############################
    
trader_logger = logging.getLogger(TRADER_NAME)
event_logger = logging.getLogger(f'{TRADER_NAME}_event')

############################ Model Parameters ############################

TRADING_SECURITIES = ['HK.01099', 'HK.00700']
FAST_MOVING_AVERAGE = 12
SLOW_MOVING_AVERAGE = 26
SIGNAL_PARAM = 9
MACD_THRESHOLD = 0.003
PROPORTION = 1/len(TRADING_SECURITIES)

#Create context objects
quote_context = OpenQuoteContext(host=FUTU_OPEND_ADDRESS, port=FUTU_OPEND_PORT)  # Quotation context
quote_context.subscribe(TRADING_SECURITIES, [SubType.QUOTE, TRADING_PERIOD, SubType.ORDER_BOOK])
trade_context = OpenSecTradeContext(filter_trdmarket=TRADING_MARKET, host=FUTU_OPEND_ADDRESS, port=FUTU_OPEND_PORT, security_firm=SecurityFirm.FUTUSECURITIES)  # Trading context. It must be consistent with the underlying varieties.

# strategies
myMACD = MACDBaseStrat(TRADING_ENVIRONMENT, trade_context, quote_context, 'HK.00700', KLType.K_1M, proportion = 0.3, trader_logger=trader_logger, event_logger=event_logger, trans_log_path=TRANS_LOG_PATH, trader_name=TRADER_NAME)

############################ Fill in the functions below to finish your trading strategy ############################
# Strategy initialization. Run once when the strategy starts
def on_init():
    # unlock trade (no need to unlock for paper trading)
    if not unlock_trade(trade_context, TRADING_ENVIRONMENT, trader_logger):
        trader_logger.error('Failed to unlock trade.')
        return False
    trader_logger.info('************  Trader Starts ***********')
    return True

# Run once for each tick. You can write the main logic of the strategy here
def on_tick():
    pass

# Run once for each new candlestick. You can write the main logic of the strategy here
def on_bar_open():
    trader_logger.info('*****************************************')
    myMACD.execute()
    myMACD.strategy()
    
    # for security in TRADING_SECURITIES:
    #     trader_logger.info(f'[TICKER] {security}')
    #     ret, data = quote_context.get_market_snapshot(security)
    #     if ret == RET_OK:
    #         time = data['update_time']
    #         price = data['last_price'][0]
    #         # print(f'[{time}] New candlestick, current price of {security} is', price)
    #         trader_logger.info(f'[UPDATE] {security} price: {price}')
    #     else:
    #         # print('[ERROR] getting market snapshot failed.')
    #         trader_logger.error('getting market snapshot failed.')
    #     macd_strat(security, PROPORTION, FAST_MOVING_AVERAGE, SLOW_MOVING_AVERAGE, SIGNAL_PARAM)
    #     trader_logger.info('')

# Run once when an order is filled
def on_fill(data):
    pass

# Run once when the status of an order changes
def on_order_status(data):
    if data['code'][0] in TRADING_SECURITIES:
        show_order_status(data)


############################### Framework code, which can be ignored ###############################
class OnTickClass(TickerHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        on_tick()


class OnBarClass(CurKlineHandlerBase):
    last_time = None
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(OnBarClass, self).on_recv_rsp(rsp_pb)
        if ret_code == RET_OK:
            cur_time = data['time_key'][0]
            if cur_time != self.last_time and data['k_type'][0] == TRADING_PERIOD:
                if self.last_time is not None:
                    on_bar_open()
                self.last_time = cur_time


class OnOrderClass(TradeOrderHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret, data = super(OnOrderClass, self).on_recv_rsp(rsp_pb)
        if ret == RET_OK:
            on_order_status(data)


class OnFillClass(TradeDealHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret, data = super(OnFillClass, self).on_recv_rsp(rsp_pb)
        if ret == RET_OK:
            on_fill(data)


def setup_logging():
    # normal trader log
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
    
    log_file_path = os.path.join(TRADER_LOG_DIR, f'{TRADER_NAME}.log')
    logger = logging.getLogger(TRADER_NAME)
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # important event log
    event_log_file_path = os.path.join(TRADER_LOG_DIR, f'{TRADER_NAME}_event.log')
    event_logger = logging.getLogger(f'{TRADER_NAME}_event')
    event_logger.setLevel(logging.INFO)

    file_handler2 = logging.FileHandler(event_log_file_path)
    file_handler2.setFormatter(formatter)
    event_logger.addHandler(file_handler2)

    console2 = logging.StreamHandler()
    console2.setLevel(logging.INFO)
    console2.setFormatter(formatter)
    event_logger.addHandler(console2)

if __name__ == '__main__':
    # Strategy initialization
    setup_logging()
    if not on_init():
        trader_logger.error('Strategy initialization failed, exit script!')
        # print('Strategy initialization failed, exit script!')
        quote_context.close()
        trade_context.close()
    else:
        # Set up callback functions
        quote_context.set_handler(OnTickClass())
        quote_context.set_handler(OnBarClass())
        trade_context.set_handler(OnOrderClass())
        trade_context.set_handler(OnFillClass())

        # Subscribe tick-by-tick, candlestick and order book of the underlying trading security
        quote_context.subscribe(code_list=TRADING_SECURITIES, subtype_list=[SubType.TICKER, SubType.ORDER_BOOK, TRADING_PERIOD])

