# -*- coding: GBK -*-
from futu import *

from modules.indicators import *
from modules.tools import *

from typing import Optional
import logging

class MACDBaseStrat(MACD):
    def __init__(self, trade_env: TrdEnv, trade_context: OpenSecTradeContext, quote_context: OpenQuoteContext, symbol: str, trading_period: KLType, proportion: float = 0.1, short_window: int = 12, long_window: int = 26, signal_window: int = 9, threshold: float = 0.0, trader_logger: Optional[logging.Logger]=None, event_logger: Optional[logging.Logger]=None, trans_log_path: Optional[str]=None, trader_name: Optional[str]=None):
        super().__init__(quote_context, symbol, trading_period, short_window, long_window, signal_window, logger)
        self.trade_env = trade_env
        self.trade_context = trade_context
        self.quote_context = quote_context
        self.trader_name = trader_name
        self.trans_log_path = trans_log_path
        self.proportion = proportion
        self.threshold = threshold
        if trader_logger is not None:
            self.trader_logger = trader_logger
        if event_logger is not None:
            self.event_logger = event_logger

        self.seen_first_death_cross = False
 
    def strategy(self):
        holding_position = get_holding_position(self.symbol, self.trade_context, self.trade_env, self.trader_logger)
        shares_per_lot = get_lot_size(self.symbol, self.quote_context, self.trader_logger)
        total_cash = get_cash(self.trade_context, self.trade_env, self.trader_logger)
        total_budget = total_cash*self.proportion
        self.trader_logger.info(f"[ALLOCATE] {self.proportion} of {total_cash} allocated to {self.symbol}")
        lots_can_buy = total_budget // (get_lot_size(self.symbol, self.quote_context, self.trader_logger) * get_ask_and_bid(self.symbol, self.quote_context, self.trader_logger)[0])
    
        macd_tdy = self.indicators['macd_tdy']
        macd_ytd = self.indicators['macd_ytd']
        macd_signal_tdy = self.indicators['macd_signal_tdy']
        macd_signal_ytd = self.indicators['macd_signal_ytd']

        if holding_position == 0:
            if macd_tdy > self.threshold and macd_ytd < self.threshold: # 上水 and position == 0
                self.trader_logger.info("[BUY] MACD > 0, buying half of allocated budget.")
                self.event_logger.info(f"[BUY] {self.symbol} MACD 上水")
                open_position(self.trade_context, self.quote_context, self.trade_env, code=self.symbol, open_quantity=lots_can_buy // 2 * shares_per_lot, trader_logger=self.trader_logger, trans_log_path=self.trans_log_path, trader_name=self.trader_name) # buy first half of budget
        else:
            if macd_tdy < -self.threshold:                                       # position > 0 and 水下
                self.trader_logger.info("[SELL] MACD < 0, selling all of allocated budget.")
                if macd_ytd > -self.threshold:
                    self.event_logger.info(f"{self.symbol} MACD 落水")
                close_position(self.trade_context, self.quote_context, self.trade_env, self.symbol, quantity=holding_position, trader_logger=self.trader_logger, trans_log_path=self.trans_log_path, trader_name=self.trader_name) # sell all
                self.seen_first_death_cross = False
            else:                                                                # position > 0 and above water
                if (macd_ytd < macd_signal_ytd) and (macd_tdy > macd_signal_tdy): # MACD 金叉, buy half
                    self.trader_logger.info("[BUY] MACD > 0 and golden cross. Buying second half of allocated budget")
                    self.event_logger.info(f"[BUY] {self.symbol} MACD > 0 and 金叉")
                    open_position(self.trade_context, self.quote_context, self.trade_env, code = self.symbol, open_quantity=lots_can_buy // 2 * shares_per_lot, trader_logger=self.trader_logger, trans_log_path=self.trans_log_path, trader_name=self.trader_name) # buy first half of budget
                if (macd_ytd > macd_signal_ytd) and (macd_tdy < macd_signal_tdy): # MACD 死叉
                    if self.seen_first_death_cross == 0:                               # first time seeing death cross, do nothing
                        self.seen_first_death_cross = 1
                        self.event_logger.info(f"[SIGHTING] {self.symbol} 水上第一个死叉")
                    else:                                                         # second time seeing death cross, sell half
                        self.trader_logger.info("[SELL] Death cross after first sighting. Selling second half of allocated budget")
                        self.event_logger.info(f"[SELL] {self.symbol} 水上死叉（非第一个）")
                        close_position(self.trade_context, self.quote_context, self.trade_env, self.symbol, quantity=lots_can_buy // 2 * shares_per_lot, trader_logger=self.trader_logger, trans_log_path=self.trans_log_path, trader_name=self.trader_name)
        