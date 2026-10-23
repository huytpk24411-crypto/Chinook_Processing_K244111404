"""Local HTTP and application tests; artificial data remains confined to tests."""
import json
import threading
import time
import unittest
import urllib.request
import urllib.error
from unittest.mock import patch
import pandas as pd
from config.settings import DatabaseConfig
from connectors.mysql import AppError
from ml.forecast import train
from services.data import audit
from tests.fixtures import snapshot_fixture, revenue_fixture
from web.application import WebApplication
from web.server import create_server
from web.views import records


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_bundle = train(revenue_fixture())

    def setUp(self):
        self.app = WebApplication()
        self.app.config = DatabaseConfig(password='unit_test_only')
        self.app.snapshot = snapshot_fixture()
        self.app.report = audit(self.app.snapshot)
        self.app.data = revenue_fixture()
        self.app.bundle = self.fixture_bundle
        self.app.revision = 7
        self.server = create_server(self.app, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        self.app.close()

    def request(self, path, payload=None, authorized=True):
        headers = {}
        if payload is not None:
            headers = {'Content-Type': 'application/json', 'Origin': self.url}
            if authorized: headers['X-Chinook-Token'] = self.server.token
        request = urllib.request.Request(self.url+path, json.dumps(payload).encode() if payload is not None else None, headers)
        try:
            with self.opener.open(request) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as exc:
            try: return exc.code, exc.read()
            finally: exc.close()

    def wait_job(self):
        deadline = time.monotonic()+10
        while self.app.state()['job']['status'] == 'running':
            if time.monotonic() > deadline: self.fail('Background job timed out')
            time.sleep(.02)
        self.assertEqual(self.app.state()['job']['status'], 'done', self.app.state()['job'])

    def test_static_only_serves_allowlisted_assets(self):
        for path in ['/', '/styles.css', '/app.js', '/i18n.js', '/charts.js', '/favicon.svg']:
            self.assertEqual(self.request(path)[0], 200)
        for path in ['/.env', '/config/settings.py', '/artifacts/revenue_model.json', '/../.env']:
            self.assertEqual(self.request(path)[0], 404)

    def test_second_server_cannot_share_the_port(self):
        with self.assertRaises(OSError):
            duplicate = create_server(self.app, self.server.server_port)
            duplicate.server_close()

    def test_state_does_not_return_password(self):
        status, body = self.request('/api/bootstrap')
        self.assertEqual(status, 200)
        self.assertNotIn(b'unit_test_only', body)
        config = json.loads(body)['config']
        self.assertTrue(config['password_configured'])
        self.assertNotIn('password', config)

    def test_post_requires_same_origin_and_token(self):
        self.assertEqual(self.request('/api/forecast', {'scope':'total'}, authorized=False)[0], 403)
        request = urllib.request.Request(self.url+'/api/forecast', b'{}',
            {'Content-Type':'application/json', 'Origin':'https://other.example', 'X-Chinook-Token':self.server.token})
        with self.assertRaises(urllib.error.HTTPError) as ctx: self.opener.open(request)
        self.assertEqual(ctx.exception.code, 403)
        ctx.exception.close()

    def test_overview_reconciles_all_levels(self):
        status, body = self.request('/api/overview?revision=7')
        self.assertEqual(status, 200)
        summary = json.loads(body)['summary']
        self.assertAlmostEqual(summary['invoice'], summary['track'])
        self.assertAlmostEqual(summary['invoice'], summary['album'])
        self.assertEqual(summary['months'], 42)

    def test_catalog_keeps_unsold_and_searches_id_and_name(self):
        status, body = self.request('/api/catalog?scope=track&q=Never')
        self.assertEqual(status, 200)
        result = json.loads(body)
        self.assertEqual(result['count'], 2)
        self.assertTrue(all(row['revenue'] == 0 for row in result['rows']))
        self.assertEqual(self.request('/api/entity?scope=track&entity=unknown')[0], 409)

    def test_forecast_has_request_ownership_and_all_scopes_match(self):
        for scope, entity in [('total','total'),('track','1'),('album','unassigned')]:
            status, body = self.request('/api/forecast', {'revision':7,'scope':scope,'entity':entity,'method':'linear','horizon':3})
            self.assertEqual(status, 202)
            request_id = json.loads(body)['request_id']; self.wait_job()
            status, result = self.request('/api/forecast?request_id='+request_id)
            self.assertEqual(status, 200)
            result = json.loads(result)
            self.assertEqual(len(result['rows']), 3)
            self.assertEqual(result['request']['entity'], entity)
            for row in result['reconciliation']:
                self.assertAlmostEqual(row['total'], row['track'])
                self.assertAlmostEqual(row['total'], row['album'])
            self.assertEqual(self.request('/api/forecast?request_id=old')[0], 409)

    def test_filter_change_invalidates_model_forecast_and_old_revision(self):
        self.app.forecast_rows = pd.DataFrame({'old':[1]})
        with patch('web.application.load_bundle', side_effect=AppError('model_incompatible')):
            status, _ = self.request('/api/filters', {'start':'2018-02','end':'2021-05','include_boundaries':True})
            self.assertEqual(status, 202);self.wait_job()
        self.assertIsNone(self.app.bundle)
        self.assertIsNone(self.app.forecast_rows)
        self.assertEqual(self.request('/api/overview?revision=7')[0], 409)

    def test_csv_model_download_and_sparse_metrics(self):
        status, body = self.request('/api/download/ranking.csv?scope=track&revision=7')
        self.assertEqual(status, 200)
        self.assertTrue(body.startswith(b'\xef\xbb\xbf'))
        status, body = self.request('/api/download/model.json?revision=7')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['metadata']['signature'], self.app.data.signature)
        result = json.loads(self.request('/api/evaluation?scope=track&entity=3')[1])
        self.assertIn('positive_actual', [row['subset'] for row in result['scores']])
        self.assertEqual(len(result['rows']), 18)

    def test_record_serialization_handles_datetime_and_missing_metrics(self):
        rows = records(pd.DataFrame({'month':pd.to_datetime(['2020-01-01']), 'MSE':[float('nan')]}))
        self.assertEqual(rows[0]['month'], '2020-01')
        self.assertIsNone(rows[0]['MSE'])

    def test_busy_job_does_not_start_another_connection(self):
        release = threading.Event()
        self.app._start('test', lambda: release.wait(3))
        try:
            self.assertEqual(self.request('/api/connect', {})[0], 409)
            self.assertEqual(self.app.revision, 7)
        finally:
            release.set(); self.wait_job()

    def test_failed_connection_clears_business_data_without_fallback(self):
        with patch('web.application.ChinookRepository.load', side_effect=AppError('connection_error','2003')):
            status, _ = self.request('/api/connect', {})
            self.assertEqual(status, 202)
            deadline = time.monotonic()+5
            while self.app.state()['job']['status'] == 'running':
                self.assertLess(time.monotonic(), deadline)
                time.sleep(.01)
        state = self.app.state()
        self.assertEqual(state['job']['error']['key'], 'connection_error')
        self.assertFalse(state['connected'] or state['ready'])
        self.assertIsNone(state['model'])
        self.assertIsNone(state['source'])
        self.assertEqual(self.request('/api/overview')[0], 409)
        self.assertEqual(self.request('/api/catalog?scope=track')[0], 409)

    def test_source_read_time_is_preserved_when_filtering(self):
        self.app.snapshot.read_at = '2026-10-23T01:00:00+00:00'
        with patch('web.application.load_bundle', side_effect=AppError('model_incompatible')):
            self.request('/api/filters', {'start':'2018-02','end':'2021-05','include_boundaries':True})
            self.wait_job()
        self.assertEqual(self.app.state()['source']['read_at'], '2026-10-23T01:00:00+00:00')
        self.assertNotEqual(self.app.state()['updated_at'], self.app.state()['source']['read_at'])

    def test_refresh_uses_saved_config_without_browser_credentials(self):
        saved = DatabaseConfig(host='saved-host', password='test_saved_only')
        with patch('web.application.DatabaseConfig.from_env', return_value=saved), patch(
                'web.application.ChinookRepository.load', return_value=snapshot_fixture()), patch(
                'web.application.write_audit'), patch('web.application.load_bundle', side_effect=AppError('model_incompatible')):
            status, _ = self.request('/api/refresh', {'host':'browser-host','password':'browser-value'})
            self.assertEqual(status, 202)
            self.wait_job()
        self.assertEqual(self.app.config, saved)
        self.assertTrue(self.app.state()['ready'])

    def test_web_startup_always_attempts_automatic_connection(self):
        from web_app import main
        with patch('sys.argv', ['main.py','--no-browser']), patch('web_app.WebApplication') as application, patch(
                'web_app.create_server') as create:
            application.return_value.config.password = ''
            create.return_value.server_port = 8766
            create.return_value.serve_forever.side_effect = KeyboardInterrupt
            self.assertEqual(main(), 0)
            application.return_value.connect.assert_called_once_with()
            application.return_value.close.assert_called_once_with()

    def test_refresh_reads_new_snapshot_and_preserves_applied_filters(self):
        snapshot = snapshot_fixture()
        snapshot.read_at = '2026-10-23T02:00:00+00:00'
        with patch('web.application.load_bundle', side_effect=AppError('model_incompatible')):
            self.request('/api/filters', {'start':'2019-02','end':'2020-05','include_boundaries':True})
            self.wait_job()
            before = self.app.state()
            with patch('web.application.ChinookRepository.load', return_value=snapshot) as load, patch('web.application.write_audit'):
                status, _ = self.request('/api/connect', {'preserve_filters':True})
                self.assertEqual(status, 202)
                self.wait_job()
                load.assert_called_once()
        after = self.app.state()
        self.assertEqual(after['filters'], before['filters'])
        self.assertEqual(after['source']['read_at'], snapshot.read_at)
        self.assertGreater(after['revision'], before['revision'])

    def test_invalid_filters_produce_actionable_error(self):
        for start in ('', 'NaT', None, 'invalid'):
            status, body = self.request('/api/filters', {'start':start,'end':'2021-05'})
            self.assertEqual(status, 409)
            self.assertEqual(json.loads(body)['error']['key'], 'invalid_input')
        self.assertEqual(self.app.revision, 7)
