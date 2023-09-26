# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
from functools import reduce
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime, timedelta
from typing import Optional, Union, Any, Callable, Dict, List

from collections import deque
from freqtrade.optimize.space import Categorical, Dimension, Integer, SKDecimal, Real

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IntParameter, IStrategy, merge_informative_pair,informative,informative_decorator, stoploss_from_absolute)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import pandas_ta as pta
from technical import qtpylib
from freqtrade.persistence import Trade
import freqtrade.vendor.qtpylib.indicators as qtpylib

class Div_V1(IStrategy):
    minimal_roi = {"0": 0.05}
    stoploss = -0.05
    timeframe = '15m'
    startup_candle_count = 200
    process_only_new_candles = True
    trailing_stop = True
    trailing_stop_positive = 0.001
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        # Divergence
        dataframe = find_divergence(dataframe, 'rsi', 60)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["regular_bear_div_rsi"] == False) &
                (dataframe['rsi'] > 50) &
                (dataframe["volume"] > 0)
            ), 'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe


def find_divergence(dataframe: pd.DataFrame, indicator, lookback) -> pd.DataFrame:
        dataframe[indicator] = dataframe[indicator].fillna(0)
        #hp - highest price
        #lp - lowest price
        #hi - highest indicator
        #li - lowest indicator
        #hp_iv - indicator value on highest price
        #lp_iv - indicator value on lowest price

        #hi_pv - price value on highest indicator
        #li_pv - price value on lowest indicator

        dataframe['hp'] = dataframe['high'].rolling(lookback).max().fillna(dataframe['high'])
        dataframe['lp'] = dataframe['low'].rolling(lookback).min().fillna(dataframe['low'])
        dataframe['hi'] = dataframe[indicator].rolling(lookback).max().fillna(dataframe[indicator])
        dataframe['li'] = dataframe[indicator].rolling(lookback).min().fillna(dataframe[indicator])

        max_detect_price = (dataframe['high'] > dataframe['hp'].shift(1))
        min_detect_price = (dataframe['low'] < dataframe['lp'].shift(1))
        max_detect_indicator= (dataframe[indicator] > dataframe['hi'].shift(1))
        min_detect_indicator= (dataframe[indicator] < dataframe['li'].shift(1))

        dataframe.loc[max_detect_price, 'hp_iv'] = dataframe[indicator]
        dataframe.loc[min_detect_price, 'lp_iv'] = dataframe[indicator]
        dataframe.loc[max_detect_indicator, 'hi_pv'] =dataframe['high']
        dataframe.loc[min_detect_indicator, 'li_pv'] = dataframe['low']

        dataframe['hp_iv'] = dataframe['hp_iv'].fillna(method='ffill')
        dataframe['lp_iv'] = dataframe['lp_iv'].fillna(method='ffill')
        dataframe['hi_pv'] = dataframe['hi_pv'].fillna(method='ffill')
        dataframe['li_pv'] = dataframe['li_pv'].fillna(method='ffill')


        regular_bear_div_condition = (dataframe['high'] > dataframe['hp'].shift(1)) & (dataframe['hp_iv'].shift(1) > dataframe[indicator])
        regular_bull_div_condition = (dataframe['low'] < dataframe['lp'].shift(1)) & (dataframe['lp_iv'].shift(1) > dataframe[indicator])

        hidden_bear_div_condition = (dataframe[indicator] > dataframe['hi'].shift(1)) & (dataframe['hi_pv'].shift(1) < dataframe['high'])
        hidden_bull_div_condition = (dataframe[indicator] < dataframe['li'].shift(1)) & (dataframe['li_pv'].shift(1) < dataframe['low'])

        dataframe.loc[regular_bear_div_condition, f'regular_bear_div_{indicator}'] = True
        dataframe.loc[regular_bull_div_condition, f'regular_bull_div_{indicator}'] = True
        dataframe.loc[hidden_bear_div_condition, f'hidden_bear_div_{indicator}'] = True
        dataframe.loc[hidden_bull_div_condition, f'hidden_bull_div_{indicator}'] = True

        for i in range(len(dataframe)):
            if i > 0 and dataframe.at[dataframe.index[i - 1], f'regular_bear_div_{indicator}'] == True and (dataframe.at[dataframe.index[i], indicator ] > dataframe.at[dataframe.index[i - 1], indicator]):
                dataframe.at[dataframe.index[i], f'regular_bear_div_{indicator}'] = True

        for i in range(len(dataframe)):
            if i > 0 and dataframe.at[dataframe.index[i - 1], f'regular_bull_div_{indicator}'] == True and (dataframe.at[dataframe.index[i], indicator ] < dataframe.at[dataframe.index[i - 1], indicator]):
                dataframe.at[dataframe.index[i], f'regular_bull_div_{indicator}'] = True

        for i in range(len(dataframe)):
            if i > 0 and dataframe.at[dataframe.index[i - 1], f'hidden_bear_div_{indicator}'] == True and (dataframe.at[dataframe.index[i], indicator ] > dataframe.at[dataframe.index[i - 1], indicator]):
                dataframe.at[dataframe.index[i], f'hidden_bear_div_{indicator}'] = True

        for i in range(len(dataframe)):
            if i > 0 and dataframe.at[dataframe.index[i - 1], f'hidden_bull_div_{indicator}'] == True and (dataframe.at[dataframe.index[i], indicator ] < dataframe.at[dataframe.index[i - 1], indicator]):
                dataframe.at[dataframe.index[i], f'hidden_bull_div_{indicator}'] = True

        return dataframe

