"""Coherent monthly total -> track allocation -> album sums.

Only the aggregate estimator is ML. Entity outputs are explicitly allocations.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib.metadata import version
import platform
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from connectors.mysql import AppError
from ml.features import FEATURE_SETS, make_features, next_features, time_split
from ml.evaluation import metrics, summarize

METHODS = ['linear', 'previous', 'mean3']
MIN_MONTHS = 30


def eligible(data):
    return len(data.total) >= MIN_MONTHS and int((data.total > 0).sum()) >= 12


def shares(track_history, window):
    historical = track_history if window == 0 else track_history.tail(window)
    weights = historical.sum(axis=0).clip(lower=0)
    if weights.sum() <= 0:
        weights = track_history.sum(axis=0).clip(lower=0)
    if weights.sum() <= 0:
        return pd.Series(1/max(1, len(weights)), index=weights.index)
    return weights/weights.sum()


def album_sum(track_values, data):
    return track_values.groupby(data.track_album).sum().reindex(data.album.columns, fill_value=0)


def baseline_track(history, method):
    return (history.iloc[-1] if method == 'previous' else history.tail(3).mean()).clip(lower=0)


@dataclass
class ModelBundle:
    estimator: LinearRegression
    features: list
    window: int
    signature: str
    metadata: dict
    evaluation: pd.DataFrame = field(default_factory=pd.DataFrame)
    scores: pd.DataFrame = field(default_factory=pd.DataFrame)


def train(data):
    if not eligible(data):
        raise AppError('insufficient_history', f'{len(data.total)} / {MIN_MONTHS}')
    x = make_features(data.total)
    train_dates, validation_dates, test_dates = time_split(data.total.index)
    validation = []
    for name, columns in FEATURE_SETS.items():
        estimator = LinearRegression().fit(x.loc[train_dates, columns], data.total.loc[train_dates])
        pred = np.maximum(0, estimator.predict(x.loc[validation_dates, columns]))
        validation.append({'feature_set': name, **metrics(data.total.loc[validation_dates], pred)})
    chosen = min(validation, key=lambda r: r['MAE'])['feature_set']
    columns = FEATURE_SETS[chosen].copy()
    # Allocation tuning uses validation only, and origin-specific past revenue.
    allocation_validation = []
    for window in (6, 12, 0):
        errors = []
        for month in validation_dates:
            past = data.track.loc[data.track.index < month]
            estimate = data.total.loc[data.total.index < month].tail(3).mean()
            predicted = shares(past, window)*estimate
            seen = past.sum() > 0
            if seen.any():
                errors.extend((predicted[seen]-data.track.loc[month, seen]).abs().tolist())
        allocation_validation.append({'window': window, 'seen_MAE': float(np.mean(errors)) if errors else 0.0})
    window = min(allocation_validation, key=lambda r: r['seen_MAE'])['window']
    pretest_dates = train_dates.append(validation_dates)
    frozen = LinearRegression().fit(x.loc[pretest_dates, columns], data.total.loc[pretest_dates])
    rows = []
    for month in test_dates:
        past = data.track.loc[data.track.index < month]
        total_pred = max(0.0, float(frozen.predict(x.loc[[month], columns])[0]))
        for method in METHODS:
            track_pred = (shares(past, window)*total_pred if method == 'linear' else baseline_track(past, method))
            scope_preds = {'track': track_pred, 'album': album_sum(track_pred, data),
                           'total': pd.Series({'total': float(track_pred.sum())})}
            for scope, predictions in scope_preds.items():
                actual = (pd.Series({'total': data.total.loc[month]}) if scope == 'total'
                          else getattr(data, scope).loc[month])
                seen = (pd.Series({'total': True}) if scope == 'total' else
                        (getattr(data, scope).loc[lambda f: f.index < month].sum() > 0))
                rows.append(pd.DataFrame({'month': month, 'scope': scope, 'entity': predictions.index,
                                          'method': method, 'actual': actual.reindex(predictions.index).values,
                                          'predicted': predictions.values, 'seen_before': seen.reindex(predictions.index).values}))
    evaluation = pd.concat(rows, ignore_index=True)
    evaluation['error'] = evaluation.predicted-evaluation.actual
    scores = summarize(evaluation)
    # After the frozen test report, refit the selected configuration for deployment.
    all_dates = x.dropna().index
    final = LinearRegression().fit(x.loc[all_dates, columns], data.total.loc[all_dates])
    metadata = {
        'format_version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'total_with_track_allocation_and_album_aggregation', 'entity_id': None,
        'features': columns, 'allocation_window': window, 'negative_policy': 'clip_at_zero_before_evaluation_and_use',
        'signature': data.signature, 'source': data.source,
        'history_start': str(data.total.index[0].date()), 'history_end': str(data.total.index[-1].date()),
        'split': {name: {'start': str(dates[0].date()), 'end': str(dates[-1].date()), 'n': len(dates)}
                  for name, dates in [('train', train_dates), ('validation', validation_dates), ('test', test_dates),
                                      ('frozen_fit', pretest_dates), ('deployment_fit', all_dates)]},
        'validation_candidates': validation, 'allocation_validation': allocation_validation,
        'selection': 'total validation MAE; allocation: validation MAE on previously sold tracks using mean3 total',
        'evaluation_mode': 'one_step_fixed_pretest_estimator_with_observed_prior_months',
        'consistency': 'total prediction * historical track shares; albums sum mapped tracks, including unassigned',
        'assumptions': ['Entity zero is recorded revenue, not proof of availability.',
                        'No launch dates known. Never-sold entities get zero allocation when past sales exist.',
                        'Recursive future shares frozen at origin; subsequent total lags use own predictions.',
                        'Boundary months excluded unless explicitly included; internal gaps need coverage confirmation.',
                        'Deployment refit includes test only after the frozen test evaluation; no retuning.'],
        'eligibility': {'minimum_months': MIN_MONTHS, 'minimum_positive_total_months': 12,
                        'track_individual_ML': False, 'album_individual_ML': False},
        'filters': data.filters.__dict__,
        'libraries': {n: version(n) for n in ['numpy', 'pandas', 'scikit-learn', 'PySide6', 'mysql-connector-python']},
        'python': platform.python_version(),
        'test_scores': scores.astype(object).where(scores.notna(), None).to_dict('records'),
        'intercept': float(final.intercept_), 'coefficients': final.coef_.tolist(),
    }
    return ModelBundle(final, columns, window, data.signature, metadata, evaluation, scores)


def forecast(data, bundle=None, method='linear', horizon=1):
    if horizon not in (1, 3, 6):
        raise AppError('invalid_horizon')
    if data.total.empty:
        raise AppError('no_data')
    if method not in METHODS:
        raise AppError('model_incompatible')
    if method == 'linear':
        if bundle is None:
            raise AppError('not_trained')
        if bundle.signature != data.signature:
            raise AppError('model_incompatible')
    total_history = data.total.copy()
    track_history = data.track.copy()
    weights = shares(track_history, bundle.window) if method == 'linear' else None
    frames = []
    for _ in range(horizon):
        month = total_history.index[-1] + pd.offsets.MonthBegin()
        if method == 'linear':
            x = next_features(total_history, month, bundle.features)
            total = max(0.0, float(bundle.estimator.predict(x)[0]))
            track = weights*total
        else:
            track = baseline_track(track_history, method)
            total = float(track.sum())
        album = album_sum(track, data)
        for scope, values in [('total', pd.Series({'total': total})), ('track', track), ('album', album)]:
            frames.append(pd.DataFrame({'month': month, 'scope': scope, 'entity': values.index,
                                        'predicted': values.values, 'method': method}))
        total_history.loc[month] = total
        track_history.loc[month] = track
    return pd.concat(frames, ignore_index=True)
