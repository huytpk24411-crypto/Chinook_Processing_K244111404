"""JSON views; all revenue comes from the shared RevenueData aggregation."""
import numpy as np
import pandas as pd
from connectors.mysql import AppError


def records(frame):
    result = frame.copy()
    for column in result.select_dtypes(include=['datetime64']).columns:
        result[column] = result[column].dt.strftime('%Y-%m')
    return result.astype(object).where(result.notna(), None).to_dict('records')


def history(series):
    return [{'month': month.strftime('%Y-%m'), 'value': float(value)} for month, value in series.items()]


def catalog(data, scope):
    if scope not in ('track', 'album'):
        raise AppError('invalid_input')
    frame = getattr(data, scope)
    items = data.tracks if scope == 'track' else data.albums
    id_column, name_column = ('TrackId', 'Name') if scope == 'track' else ('AlbumId', 'Title')
    names = items.set_index(id_column)[name_column]
    revenue = frame.sum()
    positive = (frame > 0).sum()
    result = pd.DataFrame({'id': revenue.index, 'name': names.reindex(revenue.index).values,
                           'revenue': revenue.values, 'positive_months': positive.reindex(revenue.index).values})
    return result.sort_values(['revenue', 'id'], ascending=[False, True]).reset_index(drop=True)


def select_entity(data, scope, entity=None):
    if scope == 'total':
        return data.total, {'id': 'total', 'name': None}
    if scope not in ('track', 'album') or entity not in getattr(data, scope).columns:
        raise AppError('entity_not_found')
    items = data.tracks if scope == 'track' else data.albums
    key, name = ('TrackId', 'Name') if scope == 'track' else ('AlbumId', 'Title')
    value = items.set_index(key).loc[entity, name]
    return getattr(data, scope)[entity], {'id': entity, 'name': None if pd.isna(value) else str(value)}


def entity_view(data, scope, entity=None):
    series, info = select_entity(data, scope, entity)
    return {**info, 'scope': scope, 'history': history(series), 'revenue': float(series.sum()),
            'positive_months': int((series > 0).sum()), 'months': len(series),
            'never_sold': bool(not (series > 0).any())}


def overview(data, report):
    return {'history': history(data.total), 'reconciliation': records(data.reconciliation()),
            'top_tracks': records(catalog(data, 'track').head(5)),
            'top_albums': records(catalog(data, 'album').head(5)),
            'summary': {'revenue': float(data.total.sum()), 'monthly_mean': float(data.total.mean()),
                        'months': len(data.total), 'start': data.total.index[0].strftime('%Y-%m'),
                        'end': data.total.index[-1].strftime('%Y-%m'),
                        'tracks': len(data.tracks), 'albums': len(data.albums),
                        'invoice': float(data.total.sum()), 'track': float(data.track.sum().sum()),
                        'album': float(data.album.sum().sum()),
                        'max_difference': float(np.max(np.abs(data.total.values-data.track.sum(axis=1).values)))},
            'quality': {key: report.get(key) for key in ['safe_for_forecast', 'invoice_mismatches',
                        'tracks_without_album', 'missing_track_album', 'track_zero_fraction', 'never_sold_tracks']}}


def model_view(bundle):
    if bundle is None:
        return None
    return {key: bundle.metadata.get(key) for key in ['created_utc', 'features', 'allocation_window',
            'split', 'negative_policy', 'validation_candidates', 'allocation_validation']}


def evaluation_view(data, bundle, scope, entity='total'):
    if bundle is None:
        raise AppError('not_trained')
    select_entity(data, scope, entity)
    rows = bundle.evaluation
    selected = rows.loc[(rows.scope == scope) & (rows.entity == entity)]
    return {'scores': records(bundle.scores.loc[bundle.scores.scope == scope]),
            'rows': records(selected), 'model': model_view(bundle)}


def forecast_view(data, rows, request):
    scope, entity = request['scope'], request['entity']
    detail = entity_view(data, scope, entity)
    selected = rows.loc[(rows.scope == scope) & (rows.entity == entity)]
    check = rows.groupby(['month', 'scope']).predicted.sum().unstack('scope')
    check['difference'] = check.total-check.track
    return {'request': request, 'entity': detail, 'rows': records(selected),
            'history': detail['history'], 'reconciliation': records(check.reset_index())}
