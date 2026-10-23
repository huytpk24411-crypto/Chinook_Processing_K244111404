"""JSON stores estimator state + ordered features + metadata, without executable pickle."""
import json
from importlib.metadata import version
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from connectors.mysql import AppError
from ml.features import FEATURE_SETS, time_split
from ml.forecast import METHODS, ModelBundle
from ml.evaluation import summarize


def validate_evaluation(rows, data):
    """A matching signature alone cannot validate editable JSON report contents."""
    required = {'month','scope','entity','method','actual','predicted','seen_before','error'}
    if set(rows.columns) != required:
        raise ValueError('invalid evaluation columns')
    keys = ['month','scope','entity','method']
    if rows.duplicated(keys).any() or set(rows.method) != set(METHODS):
        raise ValueError('invalid evaluation keys')
    if not np.isfinite(rows[['actual','predicted','error']].to_numpy(dtype=float)).all():
        raise ValueError('non-finite evaluation')
    if (rows.predicted < 0).any() or not rows.seen_before.map(lambda x: isinstance(x, bool)).all():
        raise ValueError('invalid evaluation values')
    expected = []
    test_dates = time_split(data.total.index)[2]
    for scope, panel in [('total',data.total.to_frame('total')),('track',data.track),('album',data.album)]:
        for month in test_dates:
            actual = panel.loc[month]
            seen = panel.loc[panel.index < month].sum() > 0
            if scope == 'total':
                seen[:] = True
            expected.append(pd.DataFrame({'month':month,'scope':scope,'entity':actual.index,
                                          'actual_source':actual.values,'seen_source':seen.values}))
    expected = pd.concat(expected, ignore_index=True)
    if len(rows) != len(expected)*len(METHODS):
        raise ValueError('incomplete evaluation')
    checked = rows.merge(expected, on=['month','scope','entity'], how='left',validate='many_to_one')
    if checked.actual_source.isna().any() or not np.allclose(checked.actual, checked.actual_source, atol=1e-9, rtol=0):
        raise ValueError('evaluation does not match database history')
    if not (checked.seen_before == checked.seen_source).all():
        raise ValueError('invalid historical eligibility')
    if not np.allclose(rows.error, rows.predicted-rows.actual, atol=1e-9, rtol=0):
        raise ValueError('invalid evaluation errors')
    reconciliation = rows.groupby(['month','method','scope']).predicted.sum().unstack()
    if not np.allclose(reconciliation.total, reconciliation.track, atol=1e-8, rtol=0) or not np.allclose(
            reconciliation.total, reconciliation.album, atol=1e-8, rtol=0):
        raise ValueError('incoherent evaluation')
    return summarize(rows)


def save_bundle(bundle, path):
    payload = {'metadata': bundle.metadata,
               'evaluation': bundle.evaluation.assign(month=bundle.evaluation.month.astype(str)).to_dict('records')}
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False, indent=2), encoding='utf-8')


def load_bundle(path, data):
    try:
        payload = json.loads(Path(path).read_text(encoding='utf-8'))
        meta = payload['metadata']
        features = meta['features']
        if (meta['format_version'] != 1 or meta['signature'] != data.signature or
            meta['scope'] != 'total_with_track_allocation_and_album_aggregation' or
            features not in list(FEATURE_SETS.values()) or meta['allocation_window'] not in (0, 6, 12) or
            meta['negative_policy'] != 'clip_at_zero_before_evaluation_and_use' or
            meta['libraries']['scikit-learn'] != version('scikit-learn')):
            raise ValueError('incompatible')
        coef = np.asarray(meta['coefficients'], dtype=float)
        intercept = float(meta['intercept'])
        if coef.shape != (len(features),) or not np.isfinite(coef).all() or not np.isfinite(intercept):
            raise ValueError('invalid coefficients')
        estimator = LinearRegression()
        estimator.coef_, estimator.intercept_ = coef, intercept
        estimator.n_features_in_ = len(features)
        estimator.feature_names_in_ = np.asarray(features, dtype=object)
        evaluation = pd.DataFrame(payload['evaluation'])
        evaluation['month'] = pd.to_datetime(evaluation.month)
        scores = validate_evaluation(evaluation, data)
        sort = lambda frame: frame.sort_values(['scope','method','subset']).reset_index(drop=True)
        pd.testing.assert_frame_equal(sort(scores), sort(pd.DataFrame(meta['test_scores'])),
                                      check_dtype=False, atol=1e-9, rtol=1e-9)
        return ModelBundle(estimator, features, meta['allocation_window'], data.signature,
                           meta, evaluation, scores)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, AssertionError):
        raise AppError('model_incompatible') from None
