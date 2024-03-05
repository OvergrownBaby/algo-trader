# -*- coding: GBK -*-

### Todo
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

TRADING_ENVIRONMENT = TrdEnv.SIMULATE  # Trading environment: REAL / SIMULATE
TRADING_MARKET = TrdMarket.HK  # Transaction market authority, used to filter accounts
TRADING_PERIOD = KLType.K_1M  # Underlying trading time period

LOG_FILENAME = 'log/trader_log.csv'
LOG_PATH = os.path.join(DIR, LOG_FILENAME)

############################ Model Parameters ############################

TRADING_SECURITIES = ['HK.01099', 'HK.00700']
FAST_MOVING_AVERAGE = 12
SLOW_MOVING_AVERAGE = 26
MACD_THRESHOLD = 0.003


#Create context objects
quote_context = OpenQuoteContext(host=FUTU_OPEND_ADDRESS, port=FUTU_OPEND_PORT)  # Quotation context
quote_context.subscribe(TRADING_SECURITIES, [SubType.QUOTE, TRADING_PERIOD, SubType.ORDER_BOOK])
trade_context = OpenSecTradeContext(filter_trdmarket=TRADING_MARKET, host=FUTU_OPEND_ADDRESS, port=FUTU_OPEND_PORT, security_firm=SecurityFirm.FUTUSECURITIES)  # Trading context. It must be consistent with the underlying varieties.

# Unlock trade
def unlock_trade():
    if TRADING_ENVIRONMENT == TrdEnv.REAL:
        ret, data = trade_context.unlock_trade(TRADING_PWD)
        if ret != RET_OK:
            logging.error(f'Unlock trade failed: {data}')
            # print('Unlock trade failed: ', data)
            return False
        logging.info('Unlock Trade Success!')
        # print('Unlock Trade success!')
    return True


# Check if it is regular trading time for underlying security
def is_normal_trading_time(code):
    ret, data = quote_context.get_market_state([code])
    if ret != RET_OK:
        logging.error(f'Get market state failed: {data}')
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
    logging.info('It is not regular trading hours.')
    # print('It is not regular trading hours.')
    return False


# Get positions
def get_holding_position(code):
    holding_position = 0
    ret, data = trade_context.position_list_query(code=code, trd_env=TRADING_ENVIRONMENT)
    if ret != RET_OK:
        # print('获取持仓数据失败：', data)
        logging.error(f'Get holding position failed: {data}')
        return None
    else:
        for qty in data['qty'].values.tolist():
            holding_position += qty
        # print('[STATUS] {} 的持仓数量为：{}'.format(code, holding_position))
        logging.info(f'Holding position of {code} is {holding_position}')
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
            logging.info('[Signal] Long signal. Open long positions.')
            open_position(code, 1)
        else:
            # print('[Signal] Short signal. Do not open short positions.')
            logging.info('[Signal] Short signal. Do not open short positions.')
    elif holding_position > 0:
        if bull_or_bear == -1:
            # print('[Signal] Short signal. Close positions.')
            logging.info('[Signal] Short signal. Close positions.')
            close_position(code, holding_position)
        else:
            # print('[Signal] Long signal. Do not add positions.')
            logging.info('[Signal] Long signal. Do not add positions.')

    def calculate_bull_bear(code, fast_param, slow_param):
        if fast_param <= 0 or slow_param <= 0:
            return 0
        if fast_param > slow_param:
            return calculate_bull_bear(code, slow_param, fast_param)
        ret, data = quote_context.get_cur_kline(code=code, num=slow_param + 1, ktype=TRADING_PERIOD)
        if ret != RET_OK:
            # print('Get candlestick value failed: ', data)
            logging.error(f'Get candlestick value failed: {data}')
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
def macd_strat(code, fast_param, slow_param, signal_param):
    # print("[STRATEGY] Executing MACD strategy.")
    logging.info("[STRATEGY] Executing MACD strategy.")
    if not is_normal_trading_time(code):
        return

    if fast_param > slow_param:
        tmp = fast_param
        slow_param = fast_param
        fast_param = tmp
    ret, data = quote_context.get_cur_kline(code=code, num=slow_param + 1, ktype=TRADING_PERIOD)
    if ret != RET_OK:
        # print('[ERROR] Get candlestick value failed: ', data)
        logging.error(f'Get candlestick value failed: {data}')
        return 0
    
    # params are usually (6, 13, 5) or (12, 26, 9)

    seen_first_death_cross = 0
    
    # todo: add budget condition for determining death cross, account for if program starts running when MACD above water
        # solution: don't need to worry, because the if program starts when MACD < 0, issue doesn't exist; if program starts when MACD > 0, then it doesn't do anything until MACD < 0
    # todo: make a an abstract strat class to reuse and require functions such as get_indicators
    # todo: write a class for backtesting each strategy
    def execute_strat():
        nonlocal seen_first_death_cross
        proportion = 0.1
        holding_position = get_holding_position(code)
        shares_per_lot = get_lot_size(code)
        total_budget = get_cash()*proportion
        # print("[STRATEGY]", proportion, "of total cash allocated to", code)
        logging.info(f"[STRATEGY] {proportion} of total cash allocated to {code}")
        lots_can_buy = total_budget // (get_lot_size(code) * get_ask_and_bid(code)[0])
    
        macd_today = data.at[data.index[-1], 'diff']
        macd_ytd = data.at[data.index[-2], 'diff']
        macd_signal_today = data.at[data.index[-1], 'dea']
        macd_signal_ytd = data.at[data.index[-2], 'dea']

        if holding_position == 0:
            if macd_today > MACD_THRESHOLD and macd_ytd < -MACD_THRESHOLD: # 上水 and position == 0
                # print("[STRATEGY] MACD > 0, buying half of allocated budget.")
                logging.info("[STRATEGY] MACD > 0, buying half of allocated budget.")
                open_position(code, lots_can_buy // 2 * shares_per_lot) # buy first half of budget
        else:
            if macd_today < -MACD_THRESHOLD:                                       # position > 0 and 水下
                # print("[STRATEGY] MACD < 0, selling all of allocated budget.")
                logging.info("[STRATEGY] MACD < 0, selling all of allocated budget.")
                close_position(code, holding_position)               # sell everything
            else:                                                    # position > 0 and above water
                if (macd_ytd < macd_signal_ytd) and (macd_today > macd_signal_today): # MACD 金叉
                    # print("[STRATEGY] MACD > 0 and golden cross. Buying second half of allocated budget")
                    logging.info("[STRATEGY] MACD > 0 and golden cross. Buying second half of allocated budget")
                    open_position(code, lots_can_buy // 2 * shares_per_lot)
                if (macd_ytd > macd_signal_ytd) and (macd_today < macd_signal_today): # MACD 死叉
                    if seen_first_death_cross == 0:
                        seen_first_death_cross = 1
                    else:
                        # print("[STRATEGY] MACD < 0 and death cross. Selling second half of allocated budget")
                        logging.info("[STRATEGY] MACD < 0 and death cross. Selling second half of allocated budget")
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
        logging.error(f'Get order book failed: {data}')
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
                                              order_type=OrderType.NORMAL, trd_env=TRADING_ENVIRONMENT,
                                              remark='moving_average_strategy')
        data.to_csv(LOG_PATH, mode='a', sep=',', index=False)
        if ret != RET_OK:
            # print('Open position failed: ', data)
            logging.error(f'Open position failed: {data}')
    else:
        # print('Maximum quantity that can be bought less than transaction quantity.')
        logging.error('Maximum quantity that can be bought is less than transaction quantity.')


# Close position
def close_position(code, quantity):
    # Get order book data
    ask, bid = get_ask_and_bid(code)

    # Check quantity
    if quantity == 0:
        # print('Invalid order quantity.')
        logging.error('Invalid order quantity.')
        return False

    # Close position
    ret, data = trade_context.place_order(price=bid, qty=quantity, code=code, trd_side=TrdSide.SELL,
                   order_type=OrderType.NORMAL, trd_env=TRADING_ENVIRONMENT, remark='moving_average_strategy')
    
    if ret == RET_OK:
        data.to_csv(LOG_PATH, mode='a', sep=',', index=False)
    else:
        # print('[ERROR]', data)
        logging.error(f'Close position failed: {data}')

    if ret != RET_OK:
        # print('Close position failed: ', data)
        logging.error(f'Close position failed: {data}')
        return False
    return True


# Get size of lot
def get_lot_size(code):
    price_quantity = 0
    # Use minimum lot size
    ret, data = quote_context.get_market_snapshot([code])
    if ret != RET_OK:
        # print('Get market snapshot failed: ', data)
        logging.error(f'Get market snapshot failed: {data}')
        return price_quantity
    price_quantity = data['lot_size'][0]
    return price_quantity


# Check the buying power is enough for the quantity
def is_valid_quantity(code, quantity, price):
    ret, data = trade_context.acctradinginfo_query(order_type=OrderType.NORMAL, code=code, price=price,
                                                   trd_env=TRADING_ENVIRONMENT)
    if ret != RET_OK:
        # print('Get max long/short quantity failed: ', data)
        logging.error(f'Get max long/short quantity failed: {data}')
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
        logging.error(f'accinfo_query error: {data}')

# Show order status
def show_order_status(data):
    order_status = data['order_status'][0]
    order_info = dict()
    order_info['Code'] = data['code'][0]
    order_info['Price'] = data['price'][0]
    order_info['TradeSide'] = data['trd_side'][0]
    order_info['Quantity'] = data['qty'][0]
    # print('[OrderStatus]', order_status, order_info)
    logging.info(f'[OrderStatus] {order_status} {order_info}')


############################ Fill in the functions below to finish your trading strategy ############################
# Strategy initialization. Run once when the strategy starts
def on_init():
    # unlock trade (no need to unlock for paper trading)
    if not unlock_trade():
        # print("Failed to unlock trade.")
        logging.error('Failed to unlock trade.')
        return False
    # print('************  Strategy Starts ***********')
    logging.info('************  Strategy Starts ***********')
    # get_max_can_buy(TRADING_SECURITY, get_ask_and_bid(TRADING_SECURITY)[0])
    return True

# Run once for each tick. You can write the main logic of the strategy here
def on_tick():
    pass


# Run once for each new candlestick. You can write the main logic of the strategy here
def on_bar_open():
    # Print seperate line
    # print('*****************************************')
    logging.info('*****************************************')
    # ma_strat('HK.00700')
    
    for security in TRADING_SECURITIES:
        ret, data = quote_context.get_market_snapshot(security)
        if ret == RET_OK:
            time = data['update_time']
            price = data['last_price']
            # print(f'[{time}] New candlestick, current price of {security} is', price)
            logging.info(f'[{time}] New candlestick, current price of {security} is {price}')
        else:
            # print('[ERROR] getting market snapshot failed.')
            logging.error('getting market snapshot failed.')
        macd_strat(security, 12, 26, 9)


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
    trader_name = os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]
    log_dir = os.path.join(DIR, 'trader_logs')
    log_file_path = os.path.join(log_dir, f'{trader_name}.log')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(filename=log_file_path,
                        level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    # Also log to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)



# Main function
if __name__ == '__main__':
    # Strategy initialization
    setup_logging()
    if not on_init():
        logging.error('Strategy initialization failed, exit script!')
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

