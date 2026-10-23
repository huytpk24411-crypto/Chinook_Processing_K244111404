import numpy as np
import pandas as pd


def metrics(actual, predicted):
    a, p = np.asarray(actual, dtype=float), np.asarray(predicted, dtype=float)
    if not len(a):
        return {'n': 0, 'MAE': None, 'MSE': None, 'RMSE': None}
    error = p-a
    mse = float(np.mean(error**2))
    return {'n': int(a.size), 'MAE': float(np.mean(np.abs(error))),
            'MSE': mse, 'RMSE': float(np.sqrt(mse))}


def summarize(rows):
    summaries = []
    for (scope, method), frame in rows.groupby(['scope', 'method'], sort=False):
        for subset, part in [('all', frame), ('positive_actual', frame.loc[frame.actual > 0]),
                             ('seen_before', frame.loc[frame.seen_before])]:
            summaries.append({'scope': scope, 'method': method, 'subset': subset,
                              **metrics(part.actual, part.predicted)})
        active = frame.loc[frame.seen_before]
        entity_mae = active.assign(ae=(active.predicted-active.actual).abs()).groupby('entity').ae.mean()
        summaries.append({'scope': scope, 'method': method, 'subset': 'macro_seen_MAE',
                          'n': len(entity_mae), 'MAE': float(entity_mae.mean()) if len(entity_mae) else None,
                          'MSE': None, 'RMSE': None})
    return pd.DataFrame(summaries)
