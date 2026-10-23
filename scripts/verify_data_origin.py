"""Independent, read-only SQL -> service -> HTTP reconciliation. No fixture imports."""
import argparse
import csv
from datetime import datetime, timezone
import io
import json
import urllib.parse
import urllib.request
import numpy as np
import pandas as pd
from config.settings import ARTIFACTS, DatabaseConfig
from connectors.mysql import AppError, read_connection
from repositories.chinook import ChinookRepository, identifier, query
from services.data import Filters, audit, build_data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    base = f'http://127.0.0.1:{args.port}'

    def http(path):
        with opener.open(base+path, timeout=45) as response:
            return response.read()

    state = json.loads(http('/api/state'))
    if not state['ready']:
        raise RuntimeError('Connect the local application to MySQL first')
    config = DatabaseConfig.from_env()
    snapshot = ChinookRepository(config).load()
    report = audit(snapshot)
    data = build_data(snapshot, Filters(**state['filters']))
    if state.get('source', {}).get('name') != snapshot.source:
        raise RuntimeError('HTTP and .env refer to different sources; align settings first')
    # Table names are discovered from actual metadata, rather than assuming case.
    tables = {str(name).lower(): identifier(name) for name in snapshot.schema.TABLE_NAME.unique()}
    inv, line, track, album = [tables[name] for name in ('invoice','invoiceline','track','album')]
    params = (data.total.index[0].to_pydatetime(),
              (data.total.index[-1]+pd.offsets.MonthBegin()).to_pydatetime())
    where = ' WHERE i.InvoiceDate >= %s AND i.InvoiceDate < %s '
    join = f' FROM {line} l JOIN {inv} i ON i.InvoiceId=l.InvoiceId '
    with read_connection(config) as db:
        identity = query(db, 'SELECT DATABASE() AS db, VERSION() AS version, @@port AS port').iloc[0].to_dict()
        raw_invoice = float(query(db, f'SELECT SUM(Total) AS revenue FROM {inv}').iloc[0,0])
        raw_line = float(query(db, f'SELECT SUM(UnitPrice*Quantity) AS revenue FROM {line}').iloc[0,0])
        monthly = query(db, "SELECT DATE_FORMAT(i.InvoiceDate, '%Y-%m-01') AS month, "
                        f'SUM(i.Total) AS revenue FROM {inv} i'+where+'GROUP BY month', params)
        sql_total = monthly.set_index(pd.to_datetime(monthly.month)).revenue.astype(float).reindex(data.total.index, fill_value=0)
        np.testing.assert_allclose(sql_total, data.total, atol=.005, rtol=0)
        panels = {}
        for scope, entity, extra in [
            ('track', 'CAST(l.TrackId AS CHAR)', ''),
            ('album', "COALESCE(CAST(a.AlbumId AS CHAR), 'unassigned')",
             f' JOIN {track} t ON t.TrackId=l.TrackId LEFT JOIN {album} a ON a.AlbumId=t.AlbumId ')]:
            rows = query(db, "SELECT DATE_FORMAT(i.InvoiceDate, '%Y-%m-01') AS month, "
                         f'{entity} AS entity, SUM(l.UnitPrice*l.Quantity) AS revenue'+join+extra+where+
                         'GROUP BY month, entity', params)
            rows['month'] = pd.to_datetime(rows.month)
            rows['revenue'] = rows.revenue.astype(float)
            expected = getattr(data, scope)
            panel = rows.pivot(index='month',columns='entity',values='revenue').reindex(
                index=expected.index, columns=expected.columns, fill_value=0).fillna(0)
            np.testing.assert_allclose(panel, expected, atol=.005, rtol=0)
            panels[scope] = panel
    np.testing.assert_allclose(raw_invoice, raw_line, atol=.005, rtol=0)
    revision = state['revision']
    overview = json.loads(http('/api/overview?'+urllib.parse.urlencode({'revision':revision})))
    np.testing.assert_allclose([row['value'] for row in overview['history']], sql_total, atol=.005, rtol=0)
    for scope, panel in panels.items():
        raw = http('/api/download/ranking.csv?'+urllib.parse.urlencode({'scope':scope,'revision':revision}))
        ranking = pd.DataFrame(list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))))
        actual = ranking.set_index('id').revenue.astype(float).sort_index()
        expected = panel.sum().sort_index()
        assert set(actual.index) == set(expected.index), 'Catalog omitted entities'
        np.testing.assert_allclose(actual.reindex(expected.index), expected, atol=.005, rtol=0)
    record = {
        'checked_utc':datetime.now(timezone.utc).isoformat(), 'status':'passed',
        'source':snapshot.source, 'server':identity, 'table_counts':snapshot.counts,
        'raw_invoice_revenue':raw_invoice, 'raw_line_revenue':raw_line,
        'date_min':report['date_min'], 'date_max':report['date_max'],
        'filtered':{'start':str(data.total.index[0].date()),'end':str(data.total.index[-1].date()),
                    'months':len(data.total),'revenue':float(data.total.sum())},
        'max_monthly_difference':float(data.reconciliation().difference.abs().max()),
        'checks':['Independent SQL matches service for every month and every track/album',
                  'HTTP history matches SQL month by month',
                  'HTTP CSV catalog matches SQL totals for every ID, including never sold',
                  'Invoice totals queried separately from detail joins; no multiplied revenue'],
        'source_read_at':state['source']['read_at'],
    }
    folder = ARTIFACTS/'verification'; folder.mkdir(exist_ok=True)
    (folder/'data_origin.json').write_text(json.dumps(record,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps(record,ensure_ascii=False,indent=2,default=str))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except AppError as exc:
        print(f'Verification failed: {exc.key} (code {exc.detail})')
        raise SystemExit(1)
