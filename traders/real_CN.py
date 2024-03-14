# -*- coding: GBK -*-

### Todo
### allow for multiple markets
### backtest: figure out where trading context gets its data then replace with our own database or write a function to fetch data from our database instead
### figure out how to import, change password access to config file inside project directory but rmb to .gitignore it
### package dependencies so i don't need a venv and can just pip install

import os
from futu import *
import logging
import pandas as pd
import matplotlib.pyplot as plt
from modules import strategies_base


############################ Global Variables ############################
FUTU_OPEND_ADDRESS = '127.0.0.1'  # Futu OpenD listening address
FUTU_OPEND_PORT = 11111  # Futu OpenD listening port

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRADING_PWD = os.getenv('FUTU_TRD_PW')  # Trading password, used to unlock trading for real trading environment

TRADING_ENVIRONMENT = TrdEnv.REAL  # Trading environment: REAL / SIMULATE
TRADING_MARKET = TrdMarket.CN  # Transaction market authority, used to filter accounts
TRADING_PERIOD = KLType.K_DAY  # Underlying trading time period

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

TRADING_SECURITIES = ['SZ.002493']
FAST_MOVING_AVERAGE = 12
SLOW_MOVING_AVERAGE = 26
SIGNAL_PARAM = 9
MACD_THRESHOLD = 0.003
PROPORTION = 0.1


#Create context objects
quote_context = OpenQuoteContext(host=FUTU_OPEND_ADDRESS, port=FUTU_OPEND_PORT)  # Quotation context
quote_context.subscribe(TRADING_SECURITIES, [SubType.QUOTE, TRADING_PERIOD, SubType.ORDER_BOOK])
trade_context = OpenSecTradeContext(filter_trdmarket=TRADING_MARKET, host=FUTU_OPEND_ADDRESS, port=FUTU_OPEND_PORT, security_firm=SecurityFirm.FUTUSECURITIES)  # Trading context. It must be consistent with the underlying varieties.

# Unlock trade
def unlock_trade():
    if TRADING_ENVIRONMENT == TrdEnv.REAL:
        ret, data = trade_context.unlock_trade(TRADING_PWD)
        if ret != RET_OK:
            trader_logger.error(f'Unlock trade failed: {data}')
            # print('Unlock trade failed: ', data)
            return False
        trader_logger.info('Unlock Trade Success!')
        # print('Unlock Trade success!')
    return True


# Check if it is regular trading time for underlying security
def is_normal_trading_time(code):
    ret, data = quote_context.get_market_state([code])
    if ret != RET_OK:
        trader_logger.error(f'Get market state failed: {data}')
        # print('Get market state failed: ', data)
        return False
    market_state = data['market_state'][0]
    '''
    MarketState.MORNING            HK and A-share morning
    MarketState.AFTERNOON          HK and A-share afternoon, US opening hours
    MarketState.FUTURE_DAY_OPEN    HK, SG, JP futures day market open
    MarketState.FUTURE_OPEN        US futures open
    MarketState.FUTURE_BREAK_OVER  Trading hours of U.S. futures after break
    MarketState.NIGHT_OPEN         HK, SG, JP futures night market open
    '''
    if market_state == MarketState.MORNING or \
                    market_state == MarketState.AFTERNOON or \
                    market_state == MarketState.FUTURE_DAY_OPEN  or \
                    market_state == MarketState.FUTURE_OPEN  or \
                    market_state == MarketState.FUTURE_BREAK_OVER  or \
                    market_state == MarketState.NIGHT_OPEN:
        return True
    trader_logger.info('It is not regular trading hours.')
    # print('It is not regular trading hours.')
    return False


# Get positions
def get_holding_position(code):
    holding_position = 0
    ret, data = trade_context.position_list_query(code=code, trd_env=TRADING_ENVIRONMENT)
    if ret != RET_OK:
        # print('获取持仓数据失败：', data)
        trader_logger.error(f'Get holding position failed: {data}')
        return None
    else:
        for qty in data['qty'].values.tolist():
            holding_position += qty
        # print('[STATUS] {} 的持仓数量为：{}'.format(code, holding_position))
        trader_logger.info(f'[POSITION] Holding {holding_position} shares of {code}')
    return holding_position


def ma_strat(code):

    if not is_normal_trading_time(code):
        return

    # Query for candlesticks, and calculate moving average value
    bull_or_bear = calculate_bull_bear(code, FAST_MOVING_AVERAGE, SLOW_MOVING_AVERAGE)

    # Get positions
    holding_position = get_holding_position(code)

    # Trading signals
    if holding_position == 0:
        if bull_or_bear == 1:
            # print('[Signal] Long signal. Open long positions.')
            trader_logger.info('[Signal] Long signal. Open long positions.')
            open_position(code, 1)
        else:
            # print('[Signal] Short signal. Do not open short positions.')
            trader_logger.info('[Signal] Short signal. Do not open short positions.')
    elif holding_position > 0:
        if bull_or_bear == -1:
            # print('[Signal] Short signal. Close positions.')
            trader_logger.info('[Signal] Short signal. Close positions.')
            close_position(code, holding_position)
        else:
            # print('[Signal] Long signal. Do not add positions.')
            trader_logger.info('[Signal] Long signal. Do not add positions.')

    def calculate_bull_bear(code, fast_param, slow_param):
        if fast_param <= 0 or slow_param <= 0:
            return 0
        if fast_param > slow_param:
            return calculate_bull_bear(code, slow_param, fast_param)
        ret, data = quote_context.get_cur_kline(code=code, num=slow_param + 1, ktype=TRADING_PERIOD)
        if ret != RET_OK:
            # print('Get candlestick value failed: ', data)
            trader_logger.error(f'Get candlestick value failed: {data}')
            return 0
        candlestick_list = data['close'].values.tolist()[::-1]
        fast_value = None
        slow_value = None
        if len(candlestick_list) > fast_param:
            fast_value = sum(candlestick_list[1: fast_param + 1]) / fast_param
        if len(candlestick_list) > slow_param:
            slow_value = sum(candlestick_list[1: slow_param + 1]) / slow_param
        if fast_value is None or slow_value is None:
            return 0
        return 1 if fast_value >= slow_value else -1


# todo: make a class for each strategy
# todo: strategy_execution for multiple stocks: write a function to create a dict stocks{key: stock, value: [strats]}, then execute(strat) for strat in stock.values for stock in stocks
# todo: stock selection
# if the program starts running after MACD > 0 and after first death cross, first death cross doesn't get updated, is this ok
def macd_strat(code, proportion, fast_param, slow_param, signal_param):
    # print("[STRATEGY] Executing MACD strategy.")
    trader_logger.info("[STRATEGY] MACD")
    if not is_normal_trading_time(code):
        return

    if fast_param > slow_param:
        tmp = fast_param
        slow_param = fast_param
        fast_param = tmp
    ret, data = quote_context.get_cur_kline(code=code, num=slow_param + 1, ktype=TRADING_PERIOD)
    if ret != RET_OK:
        # print('[ERROR] Get candlestick value failed: ', data)
        trader_logger.error(f'Get candlestick value failed: {data}')
        return 0
    
    # params are usually (6, 13, 5) or (12, 26, 9)

    seen_first_death_cross = 0
    
    def execute_strat():
        nonlocal seen_first_death_cross
        holding_position = get_holding_position(code)
        shares_per_lot = get_lot_size(code)
        total_cash = get_cash()
        total_budget = total_cash*proportion
        # print("[STRATEGY]", proportion, "of total cash allocated to", code)
        trader_logger.info(f"[ALLOCATE] {proportion} of {total_cash} allocated to {code}")
        lots_can_buy = total_budget // (get_lot_size(code) * get_ask_and_bid(code)[0])
    
        macd_tdy = data.at[data.index[-1], 'diff']
        macd_ytd = data.at[data.index[-2], 'diff']
        macd_signal_tdy = data.at[data.index[-1], 'dea']
        macd_signal_ytd = data.at[data.index[-2], 'dea']

        if holding_position == 0:
            if macd_tdy > MACD_THRESHOLD and macd_ytd < MACD_THRESHOLD: # 上水 and position == 0
                trader_logger.info("[BUY] MACD > 0, buying half of allocated budget.")
                event_logger.info(f"[BUY] {code} MACD 上水")
                open_position(code, lots_can_buy // 2 * shares_per_lot) # buy first half of budget
        else:
            if macd_tdy < -MACD_THRESHOLD:                                       # position > 0 and 水下
                trader_logger.info("[SELL] MACD < 0, selling all of allocated budget.")
                event_logger.info(f"[SELL] {code} MACD 落水")
                close_position(code, holding_position)
            else:                                                                # position > 0 and above water
                if (macd_ytd < macd_signal_ytd) and (macd_tdy > macd_signal_tdy): # MACD 金叉, buy half
                    trader_logger.info("[BUY] MACD > 0 and golden cross. Buying second half of allocated budget")
                    event_logger.info(f"[BUY] {code} MACD > 0 and 金叉")
                    open_position(code, lots_can_buy // 2 * shares_per_lot)
                if (macd_ytd > macd_signal_ytd) and (macd_tdy < macd_signal_tdy): # MACD 死叉
                    if seen_first_death_cross == 0:                               # first time seeing death cross, do nothing
                        seen_first_death_cross = 1
                        event_logger.info(f"[SIGHTING] {code} 水上第一个死叉")
                    else:                                                         # second time seeing death cross, sell half
                        trader_logger.info("[SELL] Death cross after first sighting. Selling second half of allocated budget")
                        event_logger.info(f"[SELL] {code} 水上死叉（非第一个）")
                        close_position(code, lots_can_buy // 2 * shares_per_lot)

    def get_macd():
        data.at[0, 'slow_ema'] = data.at[0, 'close']
        data.at[0, 'fast_ema'] = data.at[0, 'close']

        slow_multiplier = 2 / (1 + slow_param)
        fast_multiplier = 2 / (1 + fast_param)

        for i in range(1, len(data)):
            data.at[i, 'slow_ema'] = (data.at[i, 'close'] - data.at[i - 1, 'slow_ema']) * slow_multiplier + data.at[i - 1, 'slow_ema']
            data.at[i, 'fast_ema'] = (data.at[i, 'close'] - data.at[i - 1, 'fast_ema']) * fast_multiplier + data.at[i - 1, 'fast_ema']
            
        data['diff'] = data['fast_ema'] - data['slow_ema']
        
        signal_multiplier = 2 / (1 + signal_param)

        # Initialize the first value of 'dea' based on the first 'macd' value.
        data.at[0, 'dea'] = data.at[0, 'diff']

        # Calculate 'dea' for the rest of the DataFrame.
        for i in range(1, len(data)):
            data.at[i, 'dea'] = (data.at[i, 'diff'] - data.at[i - 1, 'dea']) * signal_multiplier + data.at[i - 1, 'diff']

    def plot_macd():
        # plot k line and ema lines
        plt.figure(figsize=(10, 6))  # Optional: specifies the figure size
        plt.plot(data['close'], label='close', marker='o')  # Plot Column1 with markers
        plt.plot(data['slow_ema'], label='slow_ema', marker='s')  # Plot Column2 with a different marker
        plt.plot(data['fast_ema'], label='fast_ema', marker='^')

        # Adding plot title and labels
        plt.xlabel('Index')
        plt.ylabel('Value')
        plt.legend()
        plt.show()

    get_macd()
    # plot_macd()
    execute_strat()
            
            

# Get ask1 and bid1 from order book
def get_ask_and_bid(code):
    ret, data = quote_context.get_order_book(code, num=1)
    if ret != RET_OK:
        # print('Get order book failed: ', data)
        trader_logger.error(f'Get order book failed: {data}')
        return None, None
    return data['Ask'][0][0], data['Bid'][0][0]


# Open long positions
def open_position(code, open_quantity):
    # Get order book data
    ask, bid = get_ask_and_bid(code)

    # Check whether buying power is enough
    if is_valid_quantity(code, open_quantity, ask):
        # Place order
        ret, data = trade_context.place_order(price=ask, qty=open_quantity, code=code, trd_side=TrdSide.BUY,
                                              order_type=OrderType.NORMAL, trd_env=TRADING_ENVIRONMENT
                                            #   , remark='moving_average_strategy'
                                            )
        if ret != RET_OK:
            # print('Open position failed: ', data)
            trader_logger.error(f'Open position failed: {data}')
        else:
            data.to_csv(TRANS_LOG_PATH, mode='a', sep=',', index=False)
    else:
        # print('Maximum quantity that can be bought less than transaction quantity.')
        trader_logger.error('Maximum quantity that can be bought is less than transaction quantity.')


# Close position
def close_position(code, quantity):
    # Get order book data
    ask, bid = get_ask_and_bid(code)

    # Check quantity
    if quantity == 0:
        # print('Invalid order quantity.')
        trader_logger.error('Invalid order quantity.')
        return False

    # Close position
    ret, data = trade_context.place_order(price=bid, qty=quantity, code=code, trd_side=TrdSide.SELL,
                   order_type=OrderType.NORMAL, trd_env=TRADING_ENVIRONMENT, remark='moving_average_strategy')
    
    if ret == RET_OK:
        data.to_csv(TRANS_LOG_PATH, mode='a', sep=',', index=False)
    elif ret != RET_OK:
        # print('[ERROR]', data)
        trader_logger.error(f'Close position failed: {data}')
        return False
    return True


# Get size of lot
def get_lot_size(code):
    price_quantity = 0
    # Use minimum lot size
    ret, data = quote_context.get_market_snapshot([code])
    if ret != RET_OK:
        # print('Get market snapshot failed: ', data)
        trader_logger.error(f'Get market snapshot failed: {data}')
        return price_quantity
    price_quantity = data['lot_size'][0]
    return price_quantity


# Check the buying power is enough for the quantity
def is_valid_quantity(code, quantity, price):
    ret, data = trade_context.acctradinginfo_query(order_type=OrderType.NORMAL, code=code, price=price,
                                                   trd_env=TRADING_ENVIRONMENT)
    if ret != RET_OK:
        # print('Get max long/short quantity failed: ', data)
        trader_logger.error(f'Get max long/short quantity failed: {data}')
        return False
    max_can_buy = data['max_cash_buy'][0]
    max_can_sell = data['max_sell_short'][0]
    if quantity > 0:
        return quantity < max_can_buy
    elif quantity < 0:
        return abs(quantity) < max_can_sell
    else:
        return False
    
def get_max_can_buy(code, price):
    ret, data = trade_context.acctradinginfo_query(order_type=OrderType.NORMAL, code=code, price=price,
                                                   trd_env=TRADING_ENVIRONMENT)
    max_can_buy = data['max_cash_buy'][0]
    return max_can_buy

def get_cash():
    ret, data = trade_context.accinfo_query(trd_env=TRADING_ENVIRONMENT)
    if ret == RET_OK:
        return data.cash[0]
        # print([col for col in data.columns if data[col][0] != 'N/A' and data[col][0] != 0])
    else:
        # print('accinfo_query error: ', data)
        trader_logger.error(f'accinfo_query error: {data}')

# Show order status
def show_order_status(data):
    order_status = data['order_status'][0]
    order_info = dict()
    order_info['Code'] = data['code'][0]
    order_info['Price'] = data['price'][0]
    order_info['TradeSide'] = data['trd_side'][0]
    order_info['Quantity'] = data['qty'][0]
    # print('[OrderStatus]', order_status, order_info)
    trader_logger.info(f'[OrderStatus] {order_status} {order_info}')


############################ Fill in the functions below to finish your trading strategy ############################
# Strategy initialization. Run once when the strategy starts
def on_init():
    # unlock trade (no need to unlock for paper trading)
    if not unlock_trade():
        # print("Failed to unlock trade.")
        trader_logger.error('Failed to unlock trade.')
        return False
    # print('************  Strategy Starts ***********')
    trader_logger.info('************  Trader Starts ***********')
    # get_max_can_buy(TRADING_SECURITY, get_ask_and_bid(TRADING_SECURITY)[0])
    return True

# Run once for each tick. You can write the main logic of the strategy here
def on_tick():
    pass


# Run once for each new candlestick. You can write the main logic of the strategy here
def on_bar_open():
    # Print seperate line
    # print('*****************************************')
    trader_logger.info('*****************************************')
    # ma_strat('HK.00700')
    
    for security in TRADING_SECURITIES:
        trader_logger.info(f'[TICKER] {security}')
        ret, data = quote_context.get_market_snapshot(security)
        if ret == RET_OK:
            time = data['update_time']
            price = data['last_price'][0]
            # print(f'[{time}] New candlestick, current price of {security} is', price)
            trader_logger.info(f'[UPDATE] {security} price: {price}')
        else:
            # print('[ERROR] getting market snapshot failed.')
            trader_logger.error('getting market snapshot failed.')
        macd_strat(security, PROPORTION, FAST_MOVING_AVERAGE, SLOW_MOVING_AVERAGE, SIGNAL_PARAM)
        trader_logger.info('\n')


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



# Main function
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

