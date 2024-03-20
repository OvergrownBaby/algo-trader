from abc import ABC, abstractmethod
from futu import *
import modules.tools as tools
import logging
from typing import Optional
from matplotlib import pyplot as plt

class MACD(ABC):
    """
    Base class for MACD indicator. Create a strategy class and inherit this class if your strategy uses MACD.

    Methods:
    get_data: Get candlestick data from Futu API.
    get_indicators: Calculate MACD and signal lines.
    plot_indicators: Plot the candlestick chart with MACD and signal lines.
    strategy: Define your strategy here.
    execute: Execute the strategy.
    """
    def __init__(self, quote_context: OpenQuoteContext, symbol: str, trading_period: KLType, short_window: int=12, long_window: int=26, signal_window: int=9, logger: Optional[logging.Logger]=None):
        self.quote_context = quote_context
        self.symbol = symbol
        self.trading_period = trading_period
        self.short_window = short_window
        self.long_window = long_window
        self.signal_window = signal_window  
        if logger is not None:
            self.logger = logger

        self.data = None
        self.indicators = None


    def get_data(self):
        if not tools.is_normal_trading_time(self.symbol, self.quote_context):
            return

        if self.short_window > self.long_window:
            tmp = self.short_window
            self.long_window = self.short_window
            self.short_window = tmp

        ret, self.data = self.quote_context.get_cur_kline(code=self.symbol, num=self.short_window + 1, ktype=self.trading_period)
        if ret != RET_OK:
            self.logger.error(f'Get candlestick value failed: {self.data}')
            return 0
        
    def get_indicators(self):
        """
        Calculates self.indicators {macd_tdy, macd_ytd, macd_signal_tdy, and macd_signal_ytd}.
        """
        if self.data is None:
            return

        self.data.at[0, 'slow_ema'] = self.data.at[0, 'close']
        self.data.at[0, 'fast_ema'] = self.data.at[0, 'close']

        slow_multiplier = 2 / (1 + self.long_window)
        fast_multiplier = 2 / (1 + self.short_window)

        for i in range(1, len(self.data)):
            self.data.at[i, 'slow_ema'] = (self.data.at[i, 'close'] - self.data.at[i - 1, 'slow_ema']) * slow_multiplier + self.data.at[i - 1, 'slow_ema']
            self.data.at[i, 'fast_ema'] = (self.data.at[i, 'close'] - self.data.at[i - 1, 'fast_ema']) * fast_multiplier + self.data.at[i - 1, 'fast_ema']

        self.data['diff'] = self.data['fast_ema'] - self.data['slow_ema']

        signal_multiplier = 2 / (1 + self.signal_window)

        # Initialize the first value of 'dea' based on the first 'macd' value.
        self.data.at[0, 'dea'] = self.data.at[0, 'diff']

        # Calculate 'dea' for the rest of the DataFrame.
        for i in range(1, len(self.data)):
            self.data.at[i, 'dea'] = (self.data.at[i, 'diff'] - self.data.at[i - 1, 'dea']) * signal_multiplier + self.data.at[i - 1, 'diff']

        self.indicators = {
            'macd_tdy' : self.data.at[self.data.index[-1], 'diff'],
            'macd_ytd' : self.data.at[self.data.index[-2], 'diff'],
            'macd_signal_tdy' : self.data.at[self.data.index[-1], 'dea'],
            'macd_signal_ytd' : self.data.at[self.data.index[-2], 'dea']
        }

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
        self.get_data()
        self.get_indicators()
        self.strategy()