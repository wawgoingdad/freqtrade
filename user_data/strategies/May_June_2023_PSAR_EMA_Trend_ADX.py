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


from freqtrade.persistence import Trade

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, stoploss_from_open, DecimalParameter,
                                IntParameter, IStrategy, merge_informative_pair)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import pandas_ta as pta
from technical import qtpylib

# custom indicators
# #############################################################################################################################################################################################



def determine_trend(df):
    df['trend'] = 0
    for i in range(2, len(df)):
        if df['high'].iloc[i] > df['high'].iloc[i-1] and df['low'].iloc[i] > df['low'].iloc[i-1]:
            df.at[i, 'trend'] = 1
        elif df['high'].iloc[i] < df['high'].iloc[i-1] and df['low'].iloc[i] < df['low'].iloc[i-1]:
            df.at[i, 'trend'] = -1
    return df


# ############################################################################################################################################################################################

class June_2023_PSAR_EMA_Trend_ADX_short(IStrategy):

    
    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 3

    # Optimal timeframe for the strategy.
    timeframe = '15m'

    # Can this strategy go short?
    can_short = True


    '''

    docker-compose run freqtrade backtesting --strategy June_2023_PSAR_EMA_Trend_ADX -i 15m --export trades --breakdown month --timerange 20210101-20230525

=========================================================== ENTER TAG STATS ============================================================
|   TAG |   Entries |   Avg Profit % |   Cum Profit % |   Tot Profit USDT |   Tot Profit % |   Avg Duration |    Win  Draw  Loss  Win% |
|-------+-----------+----------------+----------------+-------------------+----------------+----------------+--------------------------|
| TOTAL |    116831 |           0.63 |       73136.28 |         72865.532 |        7286.55 |        0:33:00 | 65911     0  50920  56.4 |
======================================================= EXIT REASON STATS ========================================================
|        Exit Reason |   Exits |   Win  Draws  Loss  Win% |   Avg Profit % |   Cum Profit % |   Tot Profit USDT |   Tot Profit % |
|--------------------+---------+--------------------------+----------------+----------------+-------------------+----------------|
| trailing_stop_loss |   73351 |  64090     0  9261  87.4 |           4.21 |      309125    |        308078     |       38640.6  |
|          exit_long |   23034 |   109     0  22925   0.5 |          -6.57 |     -151437    |       -150973     |      -18929.6  |
|         exit_short |   17616 |   119     0  17497   0.7 |          -5.42 |      -95486.7  |        -95137.2   |      -11935.8  |
|                roi |    1594 |   1593     0     1  99.9 |          28.4  |       45264.7  |         45134.9   |        5658.09 |
|          stop_loss |    1217 |      0     0  1217     0 |         -27.12 |      -33007.9  |        -32915.9   |       -4125.99 |
|        liquidation |      15 |      0     0    15     0 |         -87.63 |       -1314.43 |         -1312.67  |        -164.3  |
|         force_exit |       4 |      0     0     4     0 |          -1.94 |          -7.77 |            -7.775 |          -0.97 |
======================= MONTH BREAKDOWN ========================
|      Month |   Tot Profit USDT |   Wins |   Draws |   Losses |
|------------+-------------------+--------+---------+----------|
| 31/01/2021 |           1885.05 |   2328 |       0 |     1703 |
| 28/02/2021 |           3356.54 |   2412 |       0 |     1589 |
| 31/03/2021 |           2488.65 |   2738 |       0 |     1965 |
| 30/04/2021 |           3633.15 |   2782 |       0 |     1899 |
| 31/05/2021 |           4684.89 |   2735 |       0 |     1764 |
| 30/06/2021 |           1268.09 |   2074 |       0 |     1428 |
| 31/07/2021 |           1595.22 |   2188 |       0 |     1513 |
| 31/08/2021 |           1087.86 |   2207 |       0 |     1652 |
| 30/09/2021 |           1764.97 |   2283 |       0 |     1637 |
| 31/10/2021 |           3100.12 |   2557 |       0 |     2014 |
| 30/11/2021 |           4049.3  |   2805 |       0 |     2039 |
| 31/12/2021 |           2659    |   2457 |       0 |     1757 |
| 31/01/2022 |           3092.33 |   2478 |       0 |     1660 |
| 28/02/2022 |           2228.12 |   2183 |       0 |     1491 |
| 31/03/2022 |           3498.75 |   2312 |       0 |     1811 |
| 30/04/2022 |           3047.34 |   2296 |       0 |     1663 |
| 31/05/2022 |           4478.61 |   2335 |       0 |     1411 |
| 30/06/2022 |           3943.11 |   2311 |       0 |     1544 |
| 31/07/2022 |           2617.76 |   2268 |       0 |     1744 |
| 31/08/2022 |           1464.17 |   2029 |       0 |     1766 |
| 30/09/2022 |           1281.92 |   2002 |       0 |     1770 |
| 31/10/2022 |           1404.3  |   1903 |       0 |     2011 |
| 30/11/2022 |           3393.86 |   2423 |       0 |     1970 |
| 31/12/2022 |           1167.66 |   1802 |       0 |     2130 |
| 31/01/2023 |           2193.53 |   2141 |       0 |     1936 |
| 28/02/2023 |           2921.05 |   2482 |       0 |     1939 |
| 31/03/2023 |           1811.15 |   2169 |       0 |     1748 |
| 30/04/2023 |           1511.57 |   1902 |       0 |     1973 |
| 31/05/2023 |           1237.44 |   1309 |       0 |     1393 |
=================== SUMMARY METRICS ====================
| Metric                      | Value                  |
|-----------------------------+------------------------|
| Backtesting from            | 2021-01-01 07:30:00    |
| Backtesting to              | 2023-05-25 00:00:00    |
| Max open trades             | 8                      |
|                             |                        |
| Total/Daily Avg Trades      | 116831 / 133.83        |
| Starting balance            | 1000 USDT              |
| Final balance               | 73865.532 USDT         |
| Absolute profit             | 72865.532 USDT         |
| Total profit %              | 7286.55%               |
| CAGR %                      | 504.22%                |
| Sortino                     | 284.75                 |
| Sharpe                      | 192.62                 |
| Calmar                      | 5929.91                |
| Profit factor               | 1.23                   |
| Expectancy                  | 0.10                   |
| Trades per day              | 133.83                 |
| Avg. daily profit %         | 8.35%                  |
| Avg. stake amount           | 99.66 USDT             |
| Total trade volume          | 11643376.171 USDT      |
|                             |                        |
| Long / Short                | 70246 / 46585          |
| Total profit Long %         | 5289.37%               |
| Total profit Short %        | 1997.18%               |
| Absolute profit Long        | 52893.742 USDT         |
| Absolute profit Short       | 19971.79 USDT          |
|                             |                        |
| Best Pair                   | FLM/USDT:USDT 2040.43% |
| Worst Pair                  | ONT/USDT:USDT -233.74% |
| Best trade                  | RVN/USDT:USDT 35.93%   |
| Worst trade                 | SAND/USDT:USDT -91.84% |
| Best day                    | 1079.856 USDT          |
| Worst day                   | -336.304 USDT          |
| Days win/draw/lose          | 605 / 0 / 270          |
| Avg. Duration Winners       | 0:23:00                |
| Avg. Duration Loser         | 0:46:00                |
| Rejected Entry signals      | 1674670                |
| Entry/Exit Timeouts         | 0 / 40108              |
|                             |                        |
| Min balance                 | 851.015 USDT           |
| Max balance                 | 73941.37 USDT          |
| Max % of account underwater | 19.39%                 |
| Absolute Drawdown (Account) | 2.69%                  |
| Absolute Drawdown           | 841.737 USDT           |
| Drawdown high               | 30301.85 USDT          |
| Drawdown low                | 29460.113 USDT         |
| Drawdown Start              | 2021-12-04 05:15:00    |
| Drawdown End                | 2021-12-06 15:45:00    |
| Market change               | 35.09%                 |
========================================================

Backtested 2021-01-01 07:30:00 -> 2023-05-25 00:00:00 | Max open trades : 8
====================================================================================== STRATEGY SUMMARY =====================================================================================
|                             Strategy |   Entries |   Avg Profit % |   Cum Profit % |   Tot Profit USDT |   Tot Profit % |   Avg Duration |    Win  Draw  Loss  Win% |            Drawdown |
|--------------------------------------+-----------+----------------+----------------+-------------------+----------------+----------------+--------------------------+---------------------|
| June_2023_PSAR_EMA_Trend_ADX_short |    116831 |           0.63 |       73136.28 |         72865.532 |        7286.55 |        0:33:00 | 65911     0  50920  56.4 | 841.737 USDT  2.69% |
=============================================================================================================================================================================================


    
    '''

    # Minimal ROI designed for the strategy.
    minimal_roi = {
        # '0': 0.20, '10': 0.15, '15': 0.13, '20': 0.125, '25': 0.12, '51': 0.11, '75': 0.065, '132': 0.04, '150': 0.031, '200': 0.02, '222': 0.01
        "0": 0.347,
        "91": 0.07,
        "195": 0.018,
        "539": 0
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.27

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.029
    trailing_only_offset_is_reached = True

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    #leverage here
    leverage_optimize = True
    leverage_num = IntParameter(low=1, high=5, default=5, space='buy', optimize=leverage_optimize)

    # Strategy parameters
    parameters_yes = True
    parameters_no = False

    ema_period = IntParameter(22, 200, default=81, space="buy", optimize= parameters_yes)
    adx_period_range = IntParameter(25, 45, default=29, space="buy", optimize= parameters_yes)
    volume_check = IntParameter(15, 45, default=19, space="buy", optimize= parameters_yes)

    sell_shift = IntParameter(1, 6, default=3, space="sell", optimize= parameters_yes)


    protect_optimize = False
    cooldown_lookback = IntParameter(1, 40, default=4, space="protection", optimize=protect_optimize)
    max_drawdown_lookback = IntParameter(1, 50, default=1, space="protection", optimize=protect_optimize)
    max_drawdown_trade_limit = IntParameter(1, 3, default=8, space="protection", optimize=protect_optimize)
    max_drawdown_stop_duration = IntParameter(1, 50, default=8, space="protection", optimize=protect_optimize)
    max_allowed_drawdown = DecimalParameter(0.05, 0.30, default=0.10, decimals=2, space="protection",
                                            optimize=protect_optimize)
    stoploss_guard_lookback = IntParameter(1, 50, default=8, space="protection", optimize=protect_optimize)
    stoploss_guard_trade_limit = IntParameter(1, 3, default=1, space="protection", optimize=protect_optimize)
    stoploss_guard_stop_duration = IntParameter(1, 50, default=10, space="protection", optimize=protect_optimize)

    @property
    def protections(self):
        return [
            {
                "method": "CooldownPeriod",
                "stop_duration_candles": self.cooldown_lookback.value
            },
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": self.max_drawdown_lookback.value,
                "trade_limit": self.max_drawdown_trade_limit.value,
                "stop_duration_candles": self.max_drawdown_stop_duration.value,
                "max_allowed_drawdown": self.max_allowed_drawdown.value
            },
            {
                "method": "StoplossGuard",
                "lookback_period_candles": self.stoploss_guard_lookback.value,
                "trade_limit": self.stoploss_guard_trade_limit.value,
                "stop_duration_candles": self.stoploss_guard_stop_duration.value,
                "only_per_pair": False
            }
        ]


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
        
        return []


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        


        L_determine_trend_strategy = determine_trend(df = dataframe)
        dataframe['trend'] = L_determine_trend_strategy['trend']


        # ADX
        dataframe['adx'] = ta.ADX(dataframe)
        
        # Parabolic SAR
        dataframe['sar'] = ta.SAR(dataframe)
        
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe)

        # EMA
        dataframe['ema'] = ta.EMA(dataframe['close'], timeperiod=self.ema_period.value)

        # Volume Weighted
        dataframe['volume_mean'] = dataframe['volume'].rolling(self.volume_check.value).mean().shift(1)


        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        dataframe.loc[
            (
                        (dataframe['adx'] > self.adx_period_range.value) & 
                        (dataframe['adx'] > dataframe['adx'].shift(1)) & 
                        (dataframe['sar'] < dataframe['close']) & 
                        (dataframe['ema'] < dataframe['close']) & 
                        (dataframe['trend'] == 1) &
                        (dataframe['rsi'] > 50) &
                        (dataframe['volume'] > dataframe['volume'].shift(1)) &
                        (dataframe['volume'] > dataframe['volume_mean'])

            ),
            'enter_long'] = 1

        dataframe.loc[
            (
                        (dataframe['adx'] > self.adx_period_range.value) & # trend strength confirmation
                        (dataframe['adx'] > dataframe['adx'].shift(1)) & 
                        (dataframe['sar'] > dataframe['close']) & # trend reversal confirmation
                        (dataframe['ema'] > dataframe['close']) & # trend confirmation
                        (dataframe['trend'] == -1) & 
                        (dataframe['rsi'] < 50) & # momentum indicator
                        (dataframe['volume'] > dataframe['volume'].shift(1)) &
                        (dataframe['volume'] > dataframe['volume_mean']) # volume weighted indicator
            ),
            'enter_short'] = 1
        
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        conditions_long = []
        conditions_short = []
        dataframe.loc[:, 'exit_tag'] = ''

        exit_long = (
                (dataframe['close'] < dataframe['low'].shift(self.sell_shift.value)) &
                (dataframe['volume'] > 0)
        )

        exit_short = (
                (dataframe['close'] > dataframe['high'].shift(self.sell_shift.value)) &
                (dataframe['volume'] > 0)
        )


        conditions_short.append(exit_short)
        dataframe.loc[exit_short, 'exit_tag'] += 'exit_short'


        conditions_long.append(exit_long)
        dataframe.loc[exit_long, 'exit_tag'] += 'exit_long'


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
    