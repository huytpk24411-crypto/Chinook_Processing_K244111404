"""Application state for one local workspace. Long tasks run on a background worker."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timezone
from functools import wraps
import json
import threading
import uuid
from config.settings import ARTIFACTS, ROOT, DatabaseConfig
from connectors.mysql import AppError
from repositories.chinook import ChinookRepository
from services.data import Filters, audit, build_data
from services.audit_report import write_audit
from services.model_report import write_model_report
from ml.forecast import train, forecast, eligible
from ml.persistence import load_bundle, save_bundle
from web import views


def serialized_mutation(function):
    """Reserve state and the job atomically when two browser tabs submit together."""
    @wraps(function)
    def call(self, *args, **kwargs):
        with self.lock:
            return function(self, *args, **kwargs)
    return call


class WebApplication:
    def __init__(self):
        self.config = DatabaseConfig.from_env()
        self.snapshot = self.report = self.data = self.bundle = None
        self.forecast_rows = self.forecast_request = None
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='chinook-web')
        self.revision = 0
        self.job = None
        self.model_notice = None
        self.updated_at = None

    def state(self):
        with self.lock:
            return {'connected': self.snapshot is not None, 'ready': self.data is not None,
                    'revision': self.revision, 'job': self.job.copy() if self.job else None,
                    'filters': self.data.filters.__dict__ if self.data else None,
                    'bounds': {'start': self.report.get('date_min', '')[:7], 'end': self.report.get('date_max', '')[:7]} if self.report else None,
                    'model': views.model_view(self.bundle), 'model_notice': self.model_notice,
                    'eligible': eligible(self.data) if self.data is not None else False,
                    'updated_at': self.updated_at,
                    'source': {'name': self.snapshot.source, 'read_at': self.snapshot.read_at}
                              if self.snapshot is not None else None,
                    'config': {'host': self.config.host, 'port': self.config.port,
                               'user': self.config.user, 'database': self.config.database,
                               'password_configured': bool(self.config.password)},
                    'forecast_request': self.forecast_request}

    def _need_data(self, revision=None):
        if self.data is None:
            raise AppError('not_connected')
        if revision is not None and int(revision) != self.revision:
            raise AppError('stale')
        return self.data

    def _busy(self):
        return self.job and self.job['status'] == 'running'

    def _start(self, kind, function, invalidate=False):
        with self.lock:
            if self._busy():
                raise AppError('busy')
            if invalidate:
                self.revision += 1
                self.data = self.bundle = self.forecast_rows = self.forecast_request = None
            job_id = uuid.uuid4().hex
            self.job = {'id': job_id, 'kind': kind, 'status': 'running', 'error': None}

        def run():
            try:
                function()
                with self.lock:
                    self.job.update(status='done')
            except AppError as exc:
                with self.lock:
                    self.job.update(status='error', error={'key': exc.key, 'detail': exc.detail})
            except Exception:
                # No exception text, connection configuration or secrets in responses/logs.
                with self.lock:
                    self.job.update(status='error', error={'key': 'unexpected_error', 'detail': ''})
        self.executor.submit(run)
        return {'job_id': job_id}

    @serialized_mutation
    def refresh(self, payload=None):
        if self._busy():
            raise AppError('busy')
        self.config = DatabaseConfig.from_env()
        return self.connect({'preserve_filters':True})

    @serialized_mutation
    def connect(self, values=None):
        with self.lock:
            if self._busy():
                raise AppError('busy')
            previous_filters = (self.data.filters if self.data is not None and values
                                and values.get('preserve_filters') is True else None)
            if values is not None:
                try:
                    port = int(values.get('port', self.config.port))
                    if not 1 <= port <= 65535:
                        raise ValueError()
                    fields = {key: str(values.get(key, getattr(self.config, key))).strip()
                              for key in ('host', 'user', 'database')}
                    password = values.get('password')
                    if values.get('clear_password'):
                        password = ''
                    elif password in (None, ''):
                        password = self.config.password
                    self.config = replace(self.config, **fields, port=port, password=str(password))
                except (TypeError, ValueError):
                    raise AppError('invalid_input') from None
            config = self.config
            self.snapshot = self.report = None
            self.model_notice = None

        def work():
            snapshot = ChinookRepository(config).load()
            report = audit(snapshot)
            write_audit(report)
            with self.lock:
                self.snapshot, self.report = snapshot, report
            if snapshot.invoices.empty:
                raise AppError('no_data')
            dates = snapshot.invoices.InvoiceDate
            data = build_data(snapshot, previous_filters or Filters(str(dates.min().date()), str(dates.max().date())))
            self._set_data(data, auto_load=True)
        return self._start('connect', work, invalidate=True)

    def _set_data(self, data, auto_load=False):
        bundle = None
        notice = None
        if auto_load:
            for path in (ARTIFACTS/'web_revenue_model.json', ARTIFACTS/'revenue_model.json'):
                if path.is_file():
                    try:
                        bundle = load_bundle(path, data)
                        notice = None
                        break
                    except AppError:
                        notice = 'model_incompatible'
        with self.lock:
            self.data, self.bundle, self.model_notice = data, bundle, notice
            self.updated_at = datetime.now(timezone.utc).isoformat()

    @serialized_mutation
    def apply_filters(self, payload):
        with self.lock:
            if self.snapshot is None:
                raise AppError('not_connected')
            snapshot = self.snapshot
        try:
            filters = Filters(payload['start'], payload['end'],
                              payload.get('include_boundaries') is True,
                              payload.get('confirm_coverage') is True)
        except (KeyError, ValueError, TypeError):
            raise AppError('invalid_input') from None
        return self._start('filters', lambda: self._set_data(build_data(snapshot, filters), auto_load=True), invalidate=True)

    @serialized_mutation
    def train(self, payload):
        with self.lock:
            data = self._need_data(payload.get('revision'))
            if self._busy():
                raise AppError('busy')
            self.forecast_rows = self.forecast_request = None

        def work():
            bundle = train(data)
            write_model_report(bundle)
            save_bundle(bundle, ARTIFACTS/'web_revenue_model.json')
            with self.lock:
                self.bundle, self.model_notice = bundle, None
        return self._start('train', work)

    @serialized_mutation
    def predict(self, payload):
        with self.lock:
            data = self._need_data(payload.get('revision'))
            bundle = self.bundle
            scope, entity = payload.get('scope', 'total'), str(payload.get('entity', 'total'))
            views.select_entity(data, scope, entity)
            method = payload.get('method', 'linear')
            if method == 'linear' and bundle is None:
                raise AppError('not_trained' if eligible(data) else 'insufficient_history')
            try:
                horizon = int(payload.get('horizon', 1))
            except (ValueError, TypeError):
                raise AppError('invalid_horizon') from None
            request = {'scope': scope, 'entity': entity, 'method': method, 'horizon': horizon,
                       'revision': self.revision, 'id': uuid.uuid4().hex}
            if self._busy():
                raise AppError('busy')
            self.forecast_rows = self.forecast_request = None

        def work():
            rows = forecast(data, bundle, method, horizon)
            with self.lock:
                self.forecast_rows, self.forecast_request = rows, request
        result = self._start('forecast', work)
        result['request_id'] = request['id']
        return result

    @serialized_mutation
    def load_model(self, payload):
        with self.lock:
            data = self._need_data(payload.get('revision'))
            if self._busy():
                raise AppError('busy')
            self.forecast_rows = self.forecast_request = None
        def work():
            if 'bundle' not in payload:
                self._set_data(data, auto_load=True)
                if self.bundle is None:
                    raise AppError('model_incompatible')
                return
            folder = ROOT/'.tmp'
            folder.mkdir(exist_ok=True)
            path = folder/f'web-model-{uuid.uuid4().hex}.json'
            try:
                path.write_text(json.dumps(payload['bundle'], ensure_ascii=False), encoding='utf-8')
                bundle = load_bundle(path, data)
                with self.lock:
                    self.bundle, self.model_notice = bundle, None
                    self.forecast_rows = self.forecast_request = None
            finally:
                path.unlink(missing_ok=True)
        return self._start('load_model', work)

    def get(self, route, params):
        with self.lock:
            if route == 'state':
                return self.state()
            if route == 'audit':
                if self.report is None:
                    raise AppError('not_connected')
                return self.report
            data = self._need_data(params.get('revision'))
            scope, entity = params.get('scope', 'total'), params.get('entity', 'total')
            if route == 'overview':
                return views.overview(data, self.report)
            if route == 'entity':
                return views.entity_view(data, scope, entity)
            if route == 'catalog':
                frame = views.catalog(data, scope)
                text = str(params.get('q', '')).strip().casefold()
                if text:
                    search = frame.id.astype(str)+' '+frame.name.fillna('').astype(str)
                    frame = frame.loc[search.str.casefold().str.contains(text, regex=False)]
                offset = max(0, int(params.get('offset', 0)))
                limit = min(100, max(1, int(params.get('limit', 25))))
                return {'rows': views.records(frame.iloc[offset:offset+limit]), 'count': len(frame), 'offset': offset}
            if route == 'evaluation':
                return views.evaluation_view(data, self.bundle, scope, entity)
            if route == 'forecast':
                if self.forecast_rows is None or params.get('request_id') != self.forecast_request['id']:
                    raise AppError('stale')
                return views.forecast_view(data, self.forecast_rows, self.forecast_request)
            raise AppError('not_found')

    def download(self, name, params):
        with self.lock:
            data = self._need_data(params.get('revision'))
            scope, entity = params.get('scope', 'total'), params.get('entity', 'total')
            if name == 'model.json':
                if self.bundle is None:
                    raise AppError('not_trained')
                bundle = self.bundle
                payload = {'metadata': bundle.metadata, 'evaluation': bundle.evaluation.assign(
                    month=bundle.evaluation.month.astype(str)).to_dict('records')}
                return json.dumps(payload, ensure_ascii=False, allow_nan=False).encode(), 'application/json'
            if name == 'ranking.csv':
                frame = views.catalog(data, scope)
            elif name == 'history.csv':
                series, _ = views.select_entity(data, scope, entity)
                frame = series.rename('revenue').rename_axis('month').reset_index()
            elif name == 'reconciliation.csv':
                frame = data.reconciliation()
            elif name == 'evaluation.csv':
                if self.bundle is None:
                    raise AppError('not_trained')
                frame = self.bundle.scores.loc[self.bundle.scores.scope == scope]
            elif name == 'evaluation_rows.csv':
                if self.bundle is None:
                    raise AppError('not_trained')
                frame = self.bundle.evaluation.loc[(self.bundle.evaluation.scope == scope) & (self.bundle.evaluation.entity == entity)]
            elif name in ('forecast.csv', 'forecast_reconciliation.csv'):
                if self.forecast_rows is None or params.get('request_id') != self.forecast_request['id']:
                    raise AppError('stale')
                req = self.forecast_request
                frame = self.forecast_rows.loc[(self.forecast_rows.scope == req['scope']) & (self.forecast_rows.entity == req['entity'])]
                if name == 'forecast_reconciliation.csv':
                    frame = self.forecast_rows.groupby(['month','scope']).predicted.sum().unstack().reset_index()
            else:
                raise AppError('not_found')
            return frame.to_csv(index=False).encode('utf-8-sig'), 'text/csv; charset=utf-8'

    def close(self):
        self.executor.shutdown(wait=True)
