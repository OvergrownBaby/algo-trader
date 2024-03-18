
from futu import *
import logging
from typing import Optional

# Todo: migrate all tool functions from paper_HK.py to this file so trader files are just strategy implementations

def log_info(msg: str, logger: Optional[logging.Logger]=None):
    """Logs a message at INFO level."""
    if logger and logger.isEnabledFor(logging.INFO):
        logger.info(msg)
    else:
        print(msg)

def log_error(msg: str, logger: Optional[logging.Logger]=None):
    """Logs a message at ERROR level."""
    if logger and logger.isEnabledFor(logging.ERROR):
        logger.error(msg)
    else:
        print(msg)

# Check if it is regular trading time for underlying security
def is_normal_trading_time(code: str, quote_context: OpenQuoteContext, logger: Optional[logging.Logger]=None) -> bool:
    """
    Checks if the market is open for trading for the specified code.

    :param code: The trading symbol to check.
    :param quote_context: The context to use for fetching market state.
    :param logger: Optional logger for logging messages.
    :return: True if the market is open, False otherwise.
    """
    ret, data = quote_context.get_market_state([code])
    if ret != RET_OK:
        log_error(f'Get market state failed: {data}', logger)
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
    log_info('It is not regular trading hours.', logger)
    return False

def get_holding_position(code: str, trade_context: OpenSecTradeContext, trd_env: TrdEnv, trader_logger: Optional[logging.Logger]=None) -> Optional[int]:
    holding_position = 0
    ret, data = trade_context.position_list_query(code=code, trd_env=trd_env)
    if ret != RET_OK:
        log_error(f'[ERROR] Get holding position failed: {data}', trader_logger)
        return None
    else:
        for qty in data['qty'].values.tolist():
            holding_position += qty
        log_info(f'[POSITION] Holding {holding_position} shares of {code}', trader_logger)
    return holding_position

# Get size of lot
def get_lot_size(code: str, quote_context: OpenQuoteContext, trader_logger: Optional[logging.Logger]=None) -> int:
    """
    Get the size of a lot for the specified code.

    :param code: The trading symbol to get the lot size for.
    :param quote_context: The context to use for fetching market snapshot.
    :param trader_logger: Optional logger for logging messages.
    :return: The size of a lot for the specified code.
    """
    lot_size = 0
    ret, data = quote_context.get_market_snapshot([code])
    if ret != RET_OK:
        log_error(f'Get market snapshot failed: {data}', trader_logger)
        return lot_size
    lot_size = data['lot_size'][0]
    log_info(f'Lot size for {code} is {lot_size}', trader_logger)
    return lot_size

def get_cash(trade_context: OpenSecTradeContext, trd_env: TrdEnv, trader_logger: Optional[logging.Logger]=None) -> Optional[float]:
    """
    Get the available cash in the trading account.

    :param trade_context: The trading context to use for querying account information.
    :param trader_logger: Optional logger for logging messages.
    :return: The available cash in the trading account.
    """
    ret, data = trade_context.accinfo_query(trd_env=trd_env)
    if ret == RET_OK:
        cash = data.cash[0]
        log_info(f'Available cash: {cash}', trader_logger)
        return cash
    else:
        log_error(f'accinfo_query error: {data}', trader_logger)
        return None
    
def get_lot_size(code: str, quote_context: OpenQuoteContext, trader_logger: Optional[logging.Logger]=None) -> int:
    """
    Get the size of a lot for the specified code.

    :param code: The trading symbol to get the lot size for.
    :param quote_context: The context to use for fetching market snapshot.
    :param trader_logger: Optional logger for logging messages.
    :return: The size of a lot for the specified code.
    """
    lot_size = 0
    ret, data = quote_context.get_market_snapshot([code])
    if ret != RET_OK:
        log_error(f'Get market snapshot failed: {data}', trader_logger)
        return lot_size
    lot_size = data['lot_size'][0]
    log_info(f'Lot size for {code} is {lot_size}', trader_logger)
    return lot_size

def get_ask_and_bid(code: str, quote_context: OpenQuoteContext, trader_logger: Optional[logging.Logger]=None) -> Tuple[Optional[float], Optional[float]]:
    """
    Get the ask and bid prices for the specified code.

    :param code: The trading symbol to get the ask and bid prices for.
    :param quote_context: The context to use for fetching order book.
    :param trader_logger: Optional logger for logging messages.
    :return: A tuple containing the ask price and bid price.
    """
    ret, data = quote_context.get_order_book(code, num=1)
    if ret != RET_OK:
        log_error(f'Get order book failed: {data}', trader_logger)
        return None, None
    return data['Ask'][0][0], data['Bid'][0][0]
