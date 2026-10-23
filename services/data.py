"""Shared aggregation and filters for every screen and all forecasting scopes."""
from dataclasses import dataclass
from hashlib import sha256
import json
import numpy as np
import pandas as pd
from connectors.mysql import AppError

UNASSIGNED = 'unassigned'


def normalize(snapshot):
    snapshot.invoices = snapshot.invoices.copy()
    snapshot.invoices['InvoiceDate'] = pd.to_datetime(snapshot.invoices.InvoiceDate, errors='coerce')
    for frame, columns in [(snapshot.invoices, ['Total']),
                           (snapshot.lines, ['UnitPrice', 'Quantity'])]:
        for column in columns:
            frame[column] = pd.to_numeric(frame[column], errors='coerce').astype(float)
    return snapshot


def audit(snapshot):
    s = normalize(snapshot)
    inv, lines, tracks, albums = s.invoices, s.lines, s.tracks, s.albums
    report = {'source': s.source, 'source_read_at': s.read_at, 'table_counts': s.counts,
              'schema': s.schema.to_dict('records'), 'relations': s.relations.to_dict('records'),
              'declared_foreign_keys_missing': s.foreign_key_checks,
              'currency': 'Unverified data currency; no conversion',
              'boundary_completeness': 'Unknown: transaction dates do not prove extract coverage.'}
    report['nulls'] = {name: {c: int(n) for c, n in frame.isna().sum().items()}
                       for name, frame in [('invoice', inv), ('invoiceline', lines),
                                           ('track', tracks), ('album', albums)]}
    report['duplicate_primary_keys'] = {
        name: int(frame.duplicated(key).sum()) for name, frame, key in
        [('invoice', inv, 'InvoiceId'), ('invoiceline', lines, 'InvoiceLineId'),
         ('track', tracks, 'TrackId'), ('album', albums, 'AlbumId')]}
    report['identical_line_values'] = int(lines.duplicated(
        ['InvoiceId', 'TrackId', 'UnitPrice', 'Quantity']).sum())
    report['missing_line_invoice'] = int((~lines.InvoiceId.isin(inv.InvoiceId)).sum())
    report['missing_line_track'] = int((~lines.TrackId.isin(tracks.TrackId)).sum())
    report['tracks_without_album'] = int(tracks.AlbumId.isna().sum())
    report['missing_track_album'] = int((tracks.AlbumId.notna() & ~tracks.AlbumId.isin(albums.AlbumId)).sum())
    revenue = lines.UnitPrice * lines.Quantity
    sums = revenue.groupby(lines.InvoiceId).sum()
    per_invoice = inv.Total.to_numpy() - inv.InvoiceId.map(sums).fillna(0).to_numpy()
    report['invoice_revenue'] = float(inv.Total.sum())
    report['line_revenue'] = float(revenue.sum())
    report['difference'] = report['invoice_revenue'] - report['line_revenue']
    report['invoice_mismatches'] = int((np.abs(per_invoice) > 0.005).sum())
    report['negative_values'] = int((inv.Total < 0).sum() + (lines.UnitPrice < 0).sum() + (lines.Quantity < 0).sum())
    required_nulls = sum(int(inv[c].isna().sum()) for c in inv.columns)
    required_nulls += sum(int(lines[c].isna().sum()) for c in lines.columns)
    required_nulls += int(tracks.TrackId.isna().sum()) + int(albums.AlbumId.isna().sum())
    report['safe_for_forecast'] = not (
        required_nulls or any(report['duplicate_primary_keys'].values()) or
        report['missing_line_invoice'] or report['missing_line_track'] or
        report['invoice_mismatches'] or report['negative_values'])
    if len(inv) and inv.InvoiceDate.notna().any():
        lo, hi = inv.InvoiceDate.min(), inv.InvoiceDate.max()
        months = pd.period_range(lo.to_period('M'), hi.to_period('M'), freq='M')
        observed = inv.InvoiceDate.dt.to_period('M').unique()
        report.update(date_min=str(lo), date_max=str(hi), calendar_months=len(months),
                      observed_months=len(observed),
                      months_without_invoices=[str(m) for m in months if m not in observed])
    if (len(inv) and inv.InvoiceDate.notna().all() and
            not any(report['duplicate_primary_keys'].values())):
        joined = lines.merge(inv[['InvoiceId', 'InvoiceDate']], on='InvoiceId', validate='many_to_one')
        joined['month'] = joined.InvoiceDate.dt.to_period('M')
        positive = joined.loc[joined.UnitPrice * joined.Quantity > 0]
        track_active = positive.groupby('TrackId').month.nunique().reindex(tracks.TrackId, fill_value=0)
        assigned = positive.merge(tracks[['TrackId', 'AlbumId']], on='TrackId', validate='many_to_one')
        album_active = assigned.groupby('AlbumId').month.nunique().reindex(albums.AlbumId, fill_value=0)
        report.update(never_sold_tracks=int((track_active == 0).sum()),
                      never_sold_albums=int((album_active == 0).sum()),
                      track_positive_months_median=float(track_active.median()),
                      album_positive_months_median=float(album_active.median()),
                      track_zero_fraction=float(1-track_active.sum()/max(1, len(months)*len(tracks))),
                      album_zero_fraction=float(1-album_active.sum()/max(1, len(months)*len(albums))))
    return report


@dataclass(frozen=True)
class Filters:
    start: str
    end: str
    include_boundaries: bool = False
    confirm_coverage: bool = False

    def __post_init__(self):
        # A month filter has the same identity regardless of which day was supplied.
        for field in ('start', 'end'):
            raw = getattr(self, field)
            if not isinstance(raw, str) or not raw.strip():
                raise ValueError('A valid month is required')
            value = pd.Timestamp(raw)
            if pd.isna(value):
                raise ValueError('A valid month is required')
            value = value.to_period('M').to_timestamp()
            object.__setattr__(self, field, value.strftime('%Y-%m-%d'))
        if self.start > self.end:
            raise ValueError('Start month must not follow end month')


@dataclass
class RevenueData:
    total: pd.Series
    track: pd.DataFrame
    album: pd.DataFrame
    tracks: pd.DataFrame
    albums: pd.DataFrame
    track_album: pd.Series
    signature: str
    filters: Filters
    source: str

    def history(self, scope, entity=None):
        if scope == 'total':
            return self.total
        return getattr(self, scope)[entity]

    def reconciliation(self):
        return pd.DataFrame({'month': self.total.index, 'invoice': self.total.values,
                             'track': self.track.sum(axis=1).values,
                             'album': self.album.sum(axis=1).values,
                             'difference': self.total.values-self.track.sum(axis=1).values})


def build_data(snapshot, filters):
    report = audit(snapshot)
    if snapshot.invoices.empty:
        raise AppError('no_data')
    if not report['safe_for_forecast']:
        raise AppError('quality_block')
    inv = snapshot.invoices.copy()
    inv['month'] = inv.InvoiceDate.dt.to_period('M').dt.to_timestamp()
    first, last = inv.month.min(), inv.month.max()
    start, end = pd.Timestamp(filters.start).to_period('M').to_timestamp(), pd.Timestamp(filters.end).to_period('M').to_timestamp()
    if not filters.include_boundaries:
        start, end = max(start, first + pd.offsets.MonthBegin()), min(end, last - pd.offsets.MonthBegin())
    else:
        start, end = max(start, first), min(end, last)
    if start > end:
        raise AppError('no_data')
    index = pd.date_range(start, end, freq='MS', name='month')
    selected = inv.loc[inv.month.between(start, end)]
    missing = index.difference(selected.month.unique())
    if len(missing) and not filters.confirm_coverage:
        raise AppError('coverage_error', ', '.join(missing.strftime('%Y-%m')))
    total = selected.groupby('month').Total.sum().reindex(index, fill_value=0).astype(float)
    lines = snapshot.lines.merge(selected[['InvoiceId', 'month']], on='InvoiceId', validate='many_to_one')
    lines['revenue'] = lines.UnitPrice * lines.Quantity
    tracks = snapshot.tracks.copy()
    # String IDs are keys only, never ordinal regression inputs.
    tracks['TrackId'] = tracks.TrackId.map(lambda x: str(int(x)))
    album_ids = set(snapshot.albums.AlbumId.dropna().map(lambda x: str(int(x))))
    tracks['AlbumId'] = tracks.AlbumId.map(lambda x: str(int(x)) if pd.notna(x) and str(int(x)) in album_ids else UNASSIGNED)
    albums = snapshot.albums.copy()
    albums['AlbumId'] = albums.AlbumId.map(lambda x: str(int(x)))
    if UNASSIGNED in set(tracks.AlbumId):
        albums = pd.concat([albums, pd.DataFrame([{'AlbumId': UNASSIGNED, 'Title': None}])], ignore_index=True)
    lines['TrackId'] = lines.TrackId.map(lambda x: str(int(x)))
    panel = lines.pivot_table(index='month', columns='TrackId', values='revenue', aggfunc='sum').reindex(
        index=index, columns=tracks.TrackId, fill_value=0).fillna(0).astype(float)
    mapping = tracks.set_index('TrackId').AlbumId
    album = panel.T.groupby(mapping).sum().T.reindex(columns=albums.AlbumId, fill_value=0)
    if not np.allclose(total.values, panel.sum(axis=1).values, atol=0.005, rtol=0):
        raise AppError('quality_block')
    digest = sha256()
    for frame in [snapshot.invoices, snapshot.lines, tracks, albums]:
        digest.update(pd.util.hash_pandas_object(frame, index=False).values.tobytes())
    digest.update(json.dumps(filters.__dict__, sort_keys=True).encode())
    digest.update(snapshot.source.encode())
    return RevenueData(total, panel, album, tracks, albums, mapping, digest.hexdigest(), filters, snapshot.source)
