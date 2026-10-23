"""A row predicts its index month using information strictly before that month."""
import numpy as np
import pandas as pd

FEATURE_SETS = {
    'lags': ['lag1', 'mean3', 'mean6'],
    'calendar': ['lag1', 'mean3', 'mean6', 'month_sin', 'month_cos'],
}


def make_features(series):
    prior = series.shift(1)
    x = pd.DataFrame(index=series.index)
    x['lag1'] = prior
    x['mean3'] = prior.rolling(3, min_periods=3).mean()
    x['mean6'] = prior.rolling(6, min_periods=6).mean()
    x['month_sin'] = np.sin(2*np.pi*x.index.month/12)
    x['month_cos'] = np.cos(2*np.pi*x.index.month/12)
    return x


def next_features(history, month, columns):
    extended = pd.concat([history, pd.Series([np.nan], index=pd.DatetimeIndex([month]))])
    return make_features(extended).loc[[month], columns]


def time_split(index):
    """Six validation and six untouched test target months; no entity-specific dates."""
    usable = index[6:]
    return usable[:-12], usable[-12:-6], usable[-6:]
