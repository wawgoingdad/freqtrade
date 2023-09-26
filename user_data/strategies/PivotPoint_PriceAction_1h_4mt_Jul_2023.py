# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
from functools import reduce
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from typing import Optional, Union

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IntParameter, IStrategy, merge_informative_pair)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import pandas_ta as pta
from technical import qtpylib


class PivotPoint_PriceAction_1h_4mt_Jul_2023(IStrategy):
    
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 3


    '''
    *****

    THIS STRATEGY WORKS ON 4 MAX OPEN TRADES WITH STAKING AMOUNT OF 200USDT PER TRADE
    
    AND 
    
    3 MAX OPEN TRADES BOTH WITH STAKING AMOUNT 300USDT PER TARDE, 
    
    ALSO IF STOPLOSS IS HITTING TOO FREQUENTLY, YOU CAN USE -0.163, OR -0.34 OR -0.489 (PRESENT ONE) 
    
    *****
       
    '''

    # Optimal timeframe for the strategy.
    timeframe = '1h'

    # Can this strategy go short?
    can_short: bool = True

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
        "0": 0.198,
      "397": 0.14200000000000002,
      "800": 0.029,
      "1167": 0
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.12

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.02
    # trailing_stop_positive_offset = 0.017
    trailing_stop_positive_offset = 0.03
    trailing_only_offset_is_reached = True

    
    #leverage here
    leverage_optimize = True
    leverage_num = IntParameter(low=1, high=5, default=5, space='buy', optimize=leverage_optimize)

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    # Strategy parameters

    timeperiod_check = IntParameter(10,350, default=271, space="buy")
    volume_check = IntParameter(10,50, default=36, space="buy")

    atr_period = IntParameter(2,15, default=12, space='sell')
    sl_l_period = DecimalParameter(0.1,5.0, default=2.7, decimals=1, space='sell')
    sl_s_period = DecimalParameter(0.1,5.0, default=1.3, decimals=1, space='sell')
    tp_l_period = DecimalParameter(0.1,5.0, default=4.6, decimals=1, space='sell')
    tp_s_period = DecimalParameter(0.1,6.0, default=5.6, decimals=1, space='sell')

    
    # protect_optimize = False
    # # cooldown_lookback = IntParameter(1, 240, default=6, space="protection", optimize=protect_optimize)
    # max_drawdown_lookback = IntParameter(1, 288, default=6, space="protection", optimize=protect_optimize)
    # max_drawdown_trade_limit = IntParameter(1, 20, default=1, space="protection", optimize=protect_optimize)
    # max_drawdown_stop_duration = IntParameter(1, 288, default=6, space="protection", optimize=protect_optimize)
    # max_allowed_drawdown = DecimalParameter(0.10, 0.50, default=0.07, decimals=2, space="protection",
    #                                         optimize=protect_optimize)
    # stoploss_guard_lookback = IntParameter(1, 288, default=6, space="protection", optimize=protect_optimize)
    # stoploss_guard_trade_limit = IntParameter(1, 20, default=1, space="protection", optimize=protect_optimize)
    # stoploss_guard_stop_duration = IntParameter(1, 288, default=12, space="protection", optimize=protect_optimize)

    # @property
    # def protections(self):
    #     return [
    #         # {
    #         #     "method": "CooldownPeriod",
    #         #     "stop_duration_candles": self.cooldown_lookback.value
    #         # },
    #         {
    #             "method": "MaxDrawdown",
    #             "lookback_period_candles": self.max_drawdown_lookback.value,
    #             "trade_limit": self.max_drawdown_trade_limit.value,
    #             "stop_duration_candles": self.max_drawdown_stop_duration.value,
    #             "max_allowed_drawdown": self.max_allowed_drawdown.value
    #         },
    #         {
    #             "method": "StoplossGuard",
    #             "lookback_period_candles": self.stoploss_guard_lookback.value,
    #             "trade_limit": self.stoploss_guard_trade_limit.value,
    #             "stop_duration_candles": self.stoploss_guard_stop_duration.value,
    #             "only_per_pair": False
    #         }
    #     ]



    # Optional order type mapping.
    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'entry': 'GTC',
        'exit': 'GTC'
    }
    
    @property
    def plot_config(self):
        return {
            # Main plot indicators (Moving averages, ...)
            'main_plot': {
                'tema': {},
                'sar': {'color': 'white'},
            },
            'subplots': {
                # Subplots - each dict defines one additional plot
                "MACD": {
                    'macd': {'color': 'blue'},
                    'macdsignal': {'color': 'orange'},
                },
                "RSI": {
                    'rsi': {'color': 'red'},
                }
            }
        }

    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("ETH/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        

        # # Calculate the CPR indicator
        # dataframe['CPR'] = ((dataframe['high'].rolling(self.timeperiod_check.value).mean().shift(1) + dataframe['low'].rolling(self.timeperiod_check.value).mean().shift(1) + 2 * dataframe['close'].rolling(self.timeperiod_check.value).mean().shift(1)) / 4) - dataframe['low'].rolling(self.timeperiod_check.value).mean().shift(1)
        
        # ATR
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=self.atr_period.value)

        # pivot
        dataframe['pivot'] = (dataframe['low'].rolling(self.timeperiod_check.value).mean().shift(1)+dataframe['high'].rolling(self.timeperiod_check.value).mean().shift(1)+dataframe['close'].rolling(self.timeperiod_check.value).mean().shift(1))/3

        # Calculate the support levels using the CPR indicator
        dataframe['Support1'] = dataframe['pivot'] - (dataframe['high'].rolling(self.timeperiod_check.value).mean().shift(1) - dataframe['pivot'])
        dataframe['Support2'] = dataframe['pivot'] - 2 * (dataframe['high'].rolling(self.timeperiod_check.value).mean().shift(1) - dataframe['pivot'])
        dataframe['Support3'] = dataframe['pivot'] - 3 * (dataframe['high'].rolling(self.timeperiod_check.value).mean().shift(1) - dataframe['pivot'])
        dataframe['Support4'] = dataframe['pivot'] - 4 * (dataframe['high'].rolling(self.timeperiod_check.value).mean().shift(1) - dataframe['pivot'])
        dataframe['Support5'] = dataframe['pivot'] - 5 * (dataframe['high'].rolling(self.timeperiod_check.value).mean().shift(1) - dataframe['pivot'])

        # Calculate the resistance levels using the CPR indicator
        dataframe['Resistance1'] = dataframe['pivot'] + (dataframe['pivot'] - dataframe['low'].rolling(self.timeperiod_check.value).mean().shift(1))
        dataframe['Resistance2'] = dataframe['pivot'] + 2 * (dataframe['pivot'] - dataframe['low'].rolling(self.timeperiod_check.value).mean().shift(1))
        dataframe['Resistance3'] = dataframe['pivot'] + 3 * (dataframe['pivot'] - dataframe['low'].rolling(self.timeperiod_check.value).mean().shift(1))
        dataframe['Resistance4'] = dataframe['pivot'] + 4 * (dataframe['pivot'] - dataframe['low'].rolling(self.timeperiod_check.value).mean().shift(1))
        dataframe['Resistance5'] = dataframe['pivot'] + 5 * (dataframe['pivot'] - dataframe['low'].rolling(self.timeperiod_check.value).mean().shift(1))

        # stoploss and take profit for long and short
        dataframe['sl_s'] = dataframe['close'] + (dataframe['atr']*self.sl_s_period.value)
        dataframe['tp_s'] = dataframe['close'] - (dataframe['atr']*self.tp_s_period.value)
        
        dataframe['sl_l'] = dataframe['close'] - (dataframe['atr']*self.sl_l_period.value)
        dataframe['tp_l'] = dataframe['close'] + (dataframe['atr']*self.tp_l_period.value)



        

        

        dataframe['volume_mean_10'] = dataframe['volume'].rolling(self.volume_check.value).mean().shift(1)


        # Retrieve best bid and best ask from the orderbook
        # ------------------------------------
        """
        # first check if dataprovider is available
        if self.dp:
            if self.dp.runmode.value in ('live', 'dry_run'):
                ob = self.dp.orderbook(metadata['pair'], 1)
                dataframe['best_bid'] = ob['bids'][0][0]
                dataframe['best_ask'] = ob['asks'][0][0]
        """

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        

        conditions_long = []
        conditions_short = []
        dataframe.loc[:, 'enter_tag'] = ''

        fomc_days = [
            "2021-01-27", "2021-03-17", "2021-04-28", "2021-06-16", "2021-07-28", "2021-09-22", "2021-11-03", "2021-12-15",
            "2022-01-26", "2022-03-16", "2022-04-27", "2022-06-15", "2022-07-27", "2022-09-21", "2022-11-02", "2022-12-14",
            "2023-01-25", "2023-02-01" "2023-03-15", "2022-03-22", "2023-04-26", "2023-06-14", "2023-07-26", "2023-09-20", "2023-11-01", "2023-12-13",
            "2023-05-03"
            # Add more FOMC days for the desired time period
        ]
        #Ignore fomc days
        dataframe = dataframe[~dataframe['date'].dt.strftime('%Y-%m-%d').isin(fomc_days)]

        buy_1 = (
                (dataframe['volume'] > dataframe['volume_mean_10']) & # Make sure Volume is not 0
                ((dataframe['high'] > dataframe['Resistance1'])) &
                ((dataframe['close'] < dataframe['Resistance1'])) &
                ((dataframe['close'] < dataframe['open']))  &
                ((dataframe['open'] - dataframe['close'] > dataframe['high'] - dataframe['open'])) &
                ((dataframe['Resistance1'] - dataframe['close'] > dataframe['high'] - dataframe['Resistance1'])) 


        )

        buy_2 = (
                (dataframe['volume'] > dataframe['volume_mean_10']) & # Make sure Volume is not 0
                ((dataframe['high'] > dataframe['Resistance2'])) &
                ((dataframe['close'] < dataframe['Resistance2'])) &
                ((dataframe['close'] < dataframe['open']))  &
                ((dataframe['open'] - dataframe['close'] > dataframe['high'] - dataframe['open'])) &
                ((dataframe['Resistance2'] - dataframe['close'] > dataframe['high'] - dataframe['Resistance2'])) 
        )

        buy_2_3 = (
                (dataframe['volume'] > dataframe['volume_mean_10']) & # Make sure Volume is not 0
                ((dataframe['high'] > dataframe['Resistance3'])) &
                ((dataframe['close'] < dataframe['Resistance3'])) &
                ((dataframe['close'] < dataframe['open']))  &
                ((dataframe['open'] - dataframe['close'] > dataframe['high'] - dataframe['open'])) &
                ((dataframe['Resistance3'] - dataframe['close'] > dataframe['high'] - dataframe['Resistance3'])) 
        )

        buy_2_4 = (
                (dataframe['volume'] > dataframe['volume_mean_10']) & # Make sure Volume is not 0
                ((dataframe['high'] > dataframe['Resistance4'])) &
                ((dataframe['close'] < dataframe['Resistance4'])) &
                ((dataframe['close'] < dataframe['open']))  &
                ((dataframe['open'] - dataframe['close'] > dataframe['high'] - dataframe['open'])) &
                ((dataframe['Resistance4'] - dataframe['close'] > dataframe['high'] - dataframe['Resistance4'])) 
        )

        buy_2_5 = (
                (dataframe['volume'] > dataframe['volume_mean_10']) & # Make sure Volume is not 0
                ((dataframe['high'] > dataframe['Resistance5'])) &
                ((dataframe['close'] < dataframe['Resistance5'])) &
                ((dataframe['close'] < dataframe['open']))  &
                ((dataframe['open'] - dataframe['close'] > dataframe['high'] - dataframe['open'])) &
                ((dataframe['Resistance5'] - dataframe['close'] > dataframe['high'] - dataframe['Resistance5'])) 
        )

        # long below

        buy_3 = (
                (dataframe['volume'] > dataframe['volume_mean_10']) & # Make sure Volume is not 0
                ((dataframe['close'] > dataframe['Support5'])) &
                ((dataframe['low'] < dataframe['Support5'])) &
                ((dataframe['close'] > dataframe['open']))  &
                ((dataframe['close'] - dataframe['open'] > dataframe['open'] - dataframe['low'])) &
                ((dataframe['close'] - dataframe['Support5'] > dataframe['Support5'] - dataframe['low'])) 

        )

        buy_4 = (
                (dataframe['volume'] > dataframe['volume_mean_10']) & # Make sure Volume is not 0
                ((dataframe['close'] > dataframe['Support1'])) &
                ((dataframe['low'] < dataframe['Support1'])) &
                ((dataframe['close'] > dataframe['open']))  &
                ((dataframe['close'] - dataframe['open'] > dataframe['open'] - dataframe['low'])) &
                ((dataframe['close'] - dataframe['Support1'] > dataframe['Support1'] - dataframe['low']))
        )

        buy_5 = (
                (dataframe['volume'] > dataframe['volume_mean_10']) & # Make sure Volume is not 0
                ((dataframe['close'] > dataframe['Support2'])) &
                ((dataframe['low'] < dataframe['Support2']))  &
                ((dataframe['close'] > dataframe['open']))  &
                ((dataframe['close'] - dataframe['open'] > dataframe['open'] - dataframe['low'])) &
                ((dataframe['close'] - dataframe['Support2'] > dataframe['Support2'] - dataframe['low']))
        )

        buy_6 = (
                (dataframe['volume'] > dataframe['volume_mean_10']) & # Make sure Volume is not 0
                ((dataframe['close'] > dataframe['Support3'])) &
                ((dataframe['low'] < dataframe['Support3'])) &
                ((dataframe['close'] > dataframe['open']))  &
                ((dataframe['close'] - dataframe['open'] > dataframe['open'] - dataframe['low'])) &
                ((dataframe['close'] - dataframe['Support3'] > dataframe['Support3'] - dataframe['low']))
        )

        buy_7 = (
                (dataframe['volume'] > dataframe['volume_mean_10']) & # Make sure Volume is not 0
                ((dataframe['close'] > dataframe['Support4'])) &
                ((dataframe['low'] < dataframe['Support4'])) &
                ((dataframe['close'] > dataframe['open'])) &
                ((dataframe['close'] - dataframe['open'] > dataframe['open'] - dataframe['low'])) &
                ((dataframe['close'] - dataframe['Support4'] > dataframe['Support4'] - dataframe['low']))
        )

        conditions_long.append(buy_3)
        dataframe.loc[buy_3, 'enter_tag'] = 'Support1'

        conditions_long.append(buy_4)
        dataframe.loc[buy_4, 'enter_tag'] = 'Support2'

        conditions_long.append(buy_5)
        dataframe.loc[buy_5, 'enter_tag'] = 'Support3'

        conditions_long.append(buy_6)
        dataframe.loc[buy_6, 'enter_tag'] = 'Support4'

        conditions_long.append(buy_7)
        dataframe.loc[buy_7, 'enter_tag'] = 'Support5'


        # short below

        conditions_short.append(buy_1)
        dataframe.loc[buy_1, 'enter_tag'] = 'Resistance1'

        conditions_short.append(buy_2)
        dataframe.loc[buy_2, 'enter_tag'] = 'Resistance2'

        conditions_short.append(buy_2_3)
        dataframe.loc[buy_2_3, 'enter_tag'] = 'Resistance3'

        conditions_short.append(buy_2_4)
        dataframe.loc[buy_2_4, 'enter_tag'] = 'Resistance4'

        conditions_short.append(buy_2_5)
        dataframe.loc[buy_2_5, 'enter_tag'] = 'Resistance5'

        if conditions_long:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions_long),
                'enter_long'] = 1

        if conditions_short:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions_short),
                'enter_short'] = 1
        

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions_long = []
        conditions_short = []
        dataframe.loc[:, 'exit_tag'] = ''

        sell_1 = (
                (dataframe['sl_s'] <= dataframe['close'] ) &
                (dataframe['volume'] > 0)
        )

        sell_2 = (
                (dataframe['tp_s'] >= dataframe['close'] ) &
                (dataframe['volume'] > 0)
        )

        sell_3 = (
                (dataframe['sl_l'] >= dataframe['close'] ) &
                
                (dataframe['volume'] > 0)
        )

        sell_4 = (
                (dataframe['tp_l'] <= dataframe['close'] ) &

                (dataframe['volume'] > 0)
        )

        conditions_long.append(sell_3)
        dataframe.loc[sell_3, 'exit_tag'] += 'SL_L'

        conditions_long.append(sell_4)
        dataframe.loc[sell_4, 'exit_tag'] += 'TP_L'

        conditions_short.append(sell_1)
        dataframe.loc[sell_1, 'exit_tag'] += 'SL_S'

        conditions_short.append(sell_2)
        dataframe.loc[sell_2, 'exit_tag'] += 'TP_S'

        if conditions_long:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions_long),
                'exit_long'] = 1

        if conditions_short:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions_short),
                'exit_short'] = 1
        

        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, side: str,
                 **kwargs) -> float:

        return self.leverage_num.value
    