import json
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from connectors.mysql import AppError
from config.settings import ROOT
from ml.features import make_features, next_features, time_split
from ml.forecast import train, forecast, shares, eligible
from ml.persistence import save_bundle, load_bundle
from tests.fixtures import revenue_fixture


class MLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = revenue_fixture()
        cls.bundle = train(cls.data)

    def test_features_do_not_see_target_or_future(self):
        y = self.data.total.copy(); x = make_features(y)
        y.iloc[20:] += 10000
        other = make_features(y)
        pd.testing.assert_frame_equal(x.iloc[:21], other.iloc[:21])
        self.assertAlmostEqual(x.iloc[20].mean3, self.data.total.iloc[17:20].mean())
        self.assertAlmostEqual(x.iloc[20].mean6, self.data.total.iloc[14:20].mean())

    def test_temporal_split_and_shared_entity_dates(self):
        tr, val, te = time_split(self.data.total.index)
        self.assertLess(tr.max(), val.min()); self.assertLess(val.max(), te.min())
        self.assertEqual(len(te), 6)
        rows = self.bundle.evaluation
        for _, frame in rows.groupby(['scope', 'entity', 'method']):
            self.assertEqual(set(frame.month), set(te))

    def test_test_does_not_choose_features_or_window(self):
        data = revenue_fixture()
        data.total.iloc[-6:] *= 15
        data.track.iloc[-6:, :] *= 15
        data.album.iloc[-6:, :] *= 15
        other = train(data)
        self.assertEqual(self.bundle.features, other.features)
        self.assertEqual(self.bundle.window, other.window)
        self.assertEqual(self.bundle.metadata['validation_candidates'], other.metadata['validation_candidates'])

    def test_all_scopes_reconcile_for_every_method_and_month(self):
        for method in ('linear', 'previous', 'mean3'):
            rows = forecast(self.data, self.bundle, method, 6)
            by = rows.groupby(['month', 'scope']).predicted.sum().unstack()
            np.testing.assert_allclose(by.total, by.track, atol=1e-10)
            np.testing.assert_allclose(by.total, by.album, atol=1e-10)
            self.assertTrue((rows.predicted >= 0).all())
        by = self.bundle.evaluation.groupby(['month','method','scope']).predicted.sum().unstack()
        np.testing.assert_allclose(by.total, by.track)
        np.testing.assert_allclose(by.total, by.album)

    def test_recursive_forecast_uses_own_lags(self):
        rows = forecast(self.data, self.bundle, 'linear', 3)
        predicted = rows.loc[rows.scope == 'total'].set_index('month').predicted
        history = self.data.total.copy()
        for month, value in predicted.items():
            expected = max(0, self.bundle.estimator.predict(next_features(history, month, self.bundle.features))[0])
            self.assertAlmostEqual(value, expected)
            history.loc[month] = expected

    def test_allocation_only_uses_past_and_keeps_unsold(self):
        origin = self.data.track.index[12]
        past = self.data.track.loc[self.data.track.index < origin]
        weights = shares(past, 6)
        self.assertEqual(weights['3'], 0)
        self.assertAlmostEqual(weights.sum(), 1)
        rows = forecast(self.data, self.bundle, 'linear', 1)
        self.assertEqual(len(rows.loc[rows.scope == 'track']), 5)

    def test_sparse_evaluation_is_explicit(self):
        scores = self.bundle.scores
        track = scores.loc[(scores.scope == 'track') & (scores.method == 'linear')]
        self.assertIn('positive_actual', track.subset.values)
        self.assertIn('macro_seen_MAE', track.subset.values)
        all_n = track.loc[track.subset == 'all', 'n'].iloc[0]
        positive_n = track.loc[track.subset == 'positive_actual', 'n'].iloc[0]
        self.assertGreater(all_n, positive_n)

    def test_baseline_available_when_ml_history_is_short(self):
        data = revenue_fixture(12)
        self.assertFalse(eligible(data))
        with self.assertRaises(AppError): train(data)
        rows = forecast(data, method='mean3', horizon=1)
        self.assertEqual(set(rows.method), {'mean3'})

    def test_save_load_equivalence_and_incompatibility(self):
        folder = ROOT/'tests'/'_output'; folder.mkdir(exist_ok=True)
        path = folder/'roundtrip.json'
        save_bundle(self.bundle, path)
        loaded = load_bundle(path, self.data)
        pd.testing.assert_frame_equal(forecast(self.data, self.bundle, horizon=6), forecast(self.data, loaded, horizon=6))
        payload = json.loads(path.read_text(encoding='utf-8'))
        payload['metadata']['features'] = list(reversed(self.bundle.features))
        path.write_text(json.dumps(payload), encoding='utf-8')
        with self.assertRaises(AppError): load_bundle(path, self.data)
        path.unlink()

    def test_model_rejects_corrupted_actuals_metrics_or_missing_rows(self):
        folder = ROOT/'tests'/'_output'; folder.mkdir(exist_ok=True)
        path = folder/'invalid_report.json'
        for kind in ('actual', 'score', 'missing', 'infinite', 'duplicate'):
            with self.subTest(kind=kind):
                save_bundle(self.bundle, path)
                payload = json.loads(path.read_text(encoding='utf-8'))
                if kind == 'actual': payload['evaluation'][0]['actual'] += 1
                if kind == 'score': payload['metadata']['test_scores'][0]['MAE'] += 1
                if kind == 'missing': payload['evaluation'].pop()
                if kind == 'infinite': payload['evaluation'][0]['predicted'] = float('inf')
                if kind == 'duplicate': payload['evaluation'][0] = payload['evaluation'][1].copy()
                path.write_text(json.dumps(payload), encoding='utf-8')
                with self.assertRaises(AppError): load_bundle(path, self.data)
        path.unlink()
