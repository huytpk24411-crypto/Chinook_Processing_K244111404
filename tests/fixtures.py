"""Small artificial fixtures for tests ONLY. The application never imports tests."""
import numpy as np
import pandas as pd
from repositories.chinook import Snapshot
from services.data import Filters, build_data


def snapshot_fixture(months=42):
    dates = pd.date_range('2018-01-01', periods=months, freq='MS')
    invoices, lines = [], []
    for i, date in enumerate(dates):
        amounts = [20+3*np.sin(i), (7 if i % 4 == 0 else 0), (2 if i % 3 == 0 else 0)]
        invoices.append({'InvoiceId': i+1, 'InvoiceDate': date+pd.Timedelta(days=2), 'Total': sum(amounts)})
        for track_id, amount in zip([1, 2, 4], amounts):
            if amount > 0:
                lines.append({'InvoiceLineId': len(lines)+1, 'InvoiceId': i+1,
                              'TrackId': track_id, 'UnitPrice': amount, 'Quantity': 1})
    tracks = pd.DataFrame({'TrackId': [1, 2, 3, 4, 5], 'Name': ['One', 'Two', 'Never sold', 'Unassigned', 'Never sold too'],
                           'AlbumId': [1, 1, 2, None, 3]})
    albums = pd.DataFrame({'AlbumId': [1, 2, 3], 'Title': ['Album One', 'Empty album', 'Empty album too']})
    schema = pd.DataFrame(columns=['TABLE_NAME', 'COLUMN_NAME', 'COLUMN_TYPE', 'IS_NULLABLE', 'COLUMN_KEY'])
    relations = pd.DataFrame(columns=['TABLE_NAME', 'COLUMN_NAME', 'REFERENCED_TABLE_NAME', 'REFERENCED_COLUMN_NAME'])
    return Snapshot(pd.DataFrame(invoices), pd.DataFrame(lines), tracks, albums, schema, relations,
                    {'invoice': months, 'invoiceline': len(lines), 'track': 5, 'album': 3}, {}, 'test-fixture')


def revenue_fixture(months=42):
    snapshot = snapshot_fixture(months)
    dates = pd.to_datetime(snapshot.invoices.InvoiceDate)
    return build_data(snapshot, Filters(str(dates.min().date()), str(dates.max().date()), True))
