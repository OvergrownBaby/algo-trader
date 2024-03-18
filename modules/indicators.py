from abc import ABC, abstractmethod
from futu import *
import modules.tools as tools
import logging
from typing import Optional
from matplotlib import pyplot as plt

class MACD(ABC):
    """
    Base class for MACD indicator. Create a strategy class and inherit this class if your strategy is uses MACD.
    """
    def __init__(self, trader_name: str, quote_context: OpenQuoteContext, symbol: str, trading_period: KLType, logger: Optional[logging.Logger]=None, short_window: int=12, long_window: int=26, signal_window: int=9, threshold: float=0.0):
        self.trader_name = trader_name
        self.quote_context = quote_context
        self.symbol = symbol
        self.trading_period = trading_period
        self.short_window = short_window
        self.long_window = long_window
        self.signal_window = signal_window  
        self.threshold = threshold
        self.data = None
        self.seen_first_death_cross = False
        self.proportion = 0.1

        if logger is not None:
            self.logger = logger


    def get_data(self):
        if not tools.is_normal_trading_time(self.symbol, self.quote_context):
            return

        if fast_param > slow_param:
            tmp = fast_param
            slow_param = fast_param
            fast_param = tmp

        ret, self.data = self.quote_context.get_cur_kline(code=self.symbol, num=self.short_window + 1, ktype=self.trading_period)
        if ret != RET_OK:
            self.logger.error(f'Get candlestick value failed: {self.data}')
            return 0
        
    def get_indicators(self):
        if self.data is None:
            return
        holding_position = tools.get_holding_position(self.symbol, logger)
        shares_per_lot = tools.get_lot_size(self.symbol, self.quote_context, logger)
        total_cash = tools.get_cash()
        total_budget = total_cash*self.proportion
        self.logger.info(f"[ALLOCATE] {self.proportion} of {total_cash} allocated to {self.symbol}")
        lots_can_buy = total_budget // (tools.get_lot_size(self.symbol) * tools.get_ask_and_bid(self.symbol)[0])
    
        macd_tdy = self.data.at[self.data.index[-1], 'diff']
        macd_ytd = self.data.at[self.data.index[-2], 'diff']
        macd_signal_tdy = self.data.at[self.data.index[-1], 'dea']
        macd_signal_ytd = self.data.at[self.data.index[-2], 'dea']

    def plot_indicators(self):
        # plot k line and ema lines
        plt.figure(figsize=(10, 6))  # Optional: specifies the figure size
        plt.plot(self.data['close'], label='close', marker='o')  # Plot Column1 with markers
        plt.plot(self.data['slow_ema'], label='slow_ema', marker='s')  # Plot Column2 with a different marker
        plt.plot(self.data['fast_ema'], label='fast_ema', marker='^')

        # Adding plot title and labels
        plt.xlabel('Index')
        plt.ylabel('Value')
        plt.legend()
        plt.show()

    @abstractmethod
    def strategy(self):
        pass

    def execute(self):
        self.strategy()
        

if __name__ == '__main__':
    class MACDStrategy1(MACD):
        pass

    myMACD = MACDStrategy1(0, 'HK.00700', 1)
    myMACD.log()