"""Check the running local web server against real MySQL data, without logging secrets."""
import argparse
import csv
from datetime import datetime, timezone
import io
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from config.settings import ARTIFACTS, DatabaseConfig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    base = f'http://127.0.0.1:{args.port}'
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    token = ''
    checks = []

    def request(path, body=None, origin=None):
        headers = {}
        if body is not None:
            headers = {'Content-Type':'application/json', 'Origin':origin or base, 'X-Chinook-Token':token}
        req = urllib.request.Request(base+path, json.dumps(body).encode() if body is not None else None, headers)
        try:
            with opener.open(req, timeout=60) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as exc:
            try: return exc.code, exc.read()
            finally: exc.close()

    def get(route, **params):
        status, body = request('/api/'+route+'?'+urllib.parse.urlencode(params))
        assert status == 200, f'GET {route}: {status}'
        return json.loads(body)

    def job(route, body):
        status, raw = request('/api/'+route, body)
        assert status == 202, f'POST {route}: {status}'
        result = json.loads(raw)
        deadline = time.monotonic()+90
        while True:
            state = get('state')
            assert state['job']['id'] == result['job_id']
            if state['job']['status'] != 'running':
                assert state['job']['status'] == 'done', state['job'].get('error',{}).get('key')
                return result, state
            assert time.monotonic() < deadline, 'Job timed out'
            time.sleep(.1)

    status, raw = request('/api/bootstrap')
    assert status == 200
    boot = json.loads(raw);token = boot['token']
    assert boot['ready'] and boot['connected']
    password = DatabaseConfig.from_env().password
    assert not password or password.encode() not in raw
    del password
    assert request('/.env')[0] == 404
    assert request('/api/train', {}, origin='https://other.example')[0] == 403
    checks.append('Static allowlist, same-origin POST and password redaction passed')

    overview = get('overview', revision=boot['revision'])
    summary = overview['summary']
    assert abs(summary['invoice']-summary['track']) < .005
    assert abs(summary['invoice']-summary['album']) < .005
    checks.append('Overview and monthly reconciliation use live MySQL revenue')

    # Exercise the actual asynchronous training route, not a mock estimator.
    _, state = job('train', {'revision':boot['revision']})
    assert state['model']
    score = get('evaluation', scope='total', entity='total', revision=state['revision'])
    assert len(score['rows']) == 18
    checks.append('HTTP training job and held-out evaluation passed on live data')

    catalogs = {}
    for scope in ('track','album'):
        status, raw = request('/api/download/ranking.csv?'+urllib.parse.urlencode({'scope':scope,'revision':state['revision']}))
        assert status == 200
        catalogs[scope] = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    selection = [('total','total'),('track',catalogs['track'][0]['id']),('album',catalogs['album'][0]['id'])]
    previous_request = None
    for scope, entity in selection:
        for method in ('linear','previous','mean3'):
            for horizon in (1,3,6):
                result, state = job('forecast', {'revision':state['revision'],'scope':scope,'entity':entity,'method':method,'horizon':horizon})
                view = get('forecast', request_id=result['request_id'], revision=state['revision'])
                assert len(view['rows']) == horizon
                assert view['request']['scope'] == scope and view['request']['entity'] == entity
                for row in view['reconciliation']:
                    assert abs(row['total']-row['track']) < 1e-9
                    assert abs(row['total']-row['album']) < 1e-9
                if previous_request:
                    assert request('/api/forecast?request_id='+previous_request)[0] == 409
                previous_request = result['request_id']
    checks.append('All 27 scope/method/horizon combinations and request ownership passed')

    unsold = next(row for row in catalogs['track'] if float(row['revenue']) == 0)
    result, state = job('forecast', {'revision':state['revision'],'scope':'track','entity':unsold['id'],'method':'linear','horizon':1})
    view = get('forecast', request_id=result['request_id'])
    assert view['entity']['never_sold'] and view['rows'][0]['predicted'] == 0
    status, raw = request('/api/download/forecast.csv?request_id='+result['request_id'])
    assert status == 200 and len(list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))) == 1
    checks.append('Never-sold track selection, honest zero allocation and CSV export passed')

    # JSON download -> upload verifies all coefficients, metadata and preprocessing contract.
    status, raw = request('/api/download/model.json')
    assert status == 200
    _, state = job('model/load', {'revision':state['revision'],'bundle':json.loads(raw)})
    assert state['model']
    checks.append('Model JSON download/upload and compatibility validation passed')

    original = boot['filters']; old_revision = state['revision']
    changed = {**original, 'start':overview['history'][12]['month']+'-01'}
    _, state = job('filters', changed)
    assert state['forecast_request'] is None
    assert request('/api/overview?revision='+str(old_revision))[0] == 409
    applied, source_read_at = state['filters'], state['source']['read_at']
    _, state = job('connect', {'preserve_filters':True})
    assert state['filters'] == applied
    assert state['source']['read_at'] != source_read_at
    checks.append('Reload reads a fresh SQL snapshot and preserves the applied filter range')
    _, state = job('filters', original)
    assert state['model']
    checks.append('Filter changes clear forecasts, reject stale revisions and reload only matching models')

    # Leave the server in its default month range with a simple total forecast.
    job('forecast', {'revision':state['revision'],'scope':'total','entity':'total','method':'linear','horizon':1})
    folder = ARTIFACTS/'verification';folder.mkdir(exist_ok=True)
    record = {'status':'passed','checked_utc':datetime.now(timezone.utc).isoformat(),
              'source':'live MySQL via localhost HTTP','checks':checks,
              'history':{'start':summary['start'],'end':summary['end'],'revenue':summary['revenue']},
              'catalog':{scope:len(rows) for scope,rows in catalogs.items()},
              'browser_qa':'Separate manual/Computer Use verification; this script checks HTTP, not browser rendering.'}
    (folder/'web_live_checks.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    for check in checks: print('PASS:',check)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
