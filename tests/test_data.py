import unittest
import pandas as pd
from connectors.mysql import AppError
from repositories.chinook import identifier, query
from services.data import audit, build_data, Filters
from tests.fixtures import snapshot_fixture, revenue_fixture


class DataTests(unittest.TestCase):
    def test_join_does_not_multiply_invoice_total(self):
        s = snapshot_fixture()
        expected = s.invoices.Total.sum()
        wrong = s.invoices.merge(s.lines, on='InvoiceId').Total.sum()
        self.assertGreater(wrong, expected)
        d = revenue_fixture()
        self.assertAlmostEqual(d.total.sum(), expected)
        self.assertAlmostEqual(d.track.sum().sum(), expected)
        self.assertAlmostEqual(d.album.sum().sum(), expected)

    def test_invoice_detail_reconciliation_and_unassigned(self):
        s = snapshot_fixture(); report = audit(s)
        self.assertTrue(report['safe_for_forecast'])
        self.assertLess(abs(report['difference']), .005)
        self.assertEqual(report['tracks_without_album'], 1)
        d = revenue_fixture()
        self.assertGreater(d.album.unassigned.sum(), 0)
        self.assertEqual(d.track['3'].sum(), 0)
        self.assertIn('2', d.album.columns)

    def test_bad_invoice_blocks_training_data(self):
        s = snapshot_fixture(); s.invoices.loc[0, 'Total'] += 1
        self.assertFalse(audit(s)['safe_for_forecast'])
        with self.assertRaises(AppError):
            build_data(s, Filters('2018-01-01', '2021-06-01', True))

    def test_missing_month_requires_explicit_coverage(self):
        s = snapshot_fixture(); s.invoices = s.invoices.loc[s.invoices.InvoiceId != 8]
        s.lines = s.lines.loc[s.lines.InvoiceId != 8]
        with self.assertRaises(AppError) as ctx:
            build_data(s, Filters('2018-01-01', '2021-06-01', True))
        self.assertEqual(ctx.exception.key, 'coverage_error')
        d = build_data(s, Filters('2018-01-01', '2021-06-01', True, True))
        self.assertEqual(d.total.loc['2018-08-01'], 0)

    def test_boundaries_are_policy_not_day_of_last_sale(self):
        s = snapshot_fixture()
        d = build_data(s, Filters('2018-01-01', '2021-06-01'))
        self.assertEqual(len(d.total), 40)
        self.assertEqual(d.total.index[0], pd.Timestamp('2018-02-01'))
        self.assertEqual(d.total.index[-1], pd.Timestamp('2021-05-01'))

    def test_month_filter_identity_is_independent_of_day(self):
        a = Filters('2018-01-01', '2021-06-01', True)
        b = Filters('2018-01-03', '2021-06-22', True)
        self.assertEqual(a, b)
        self.assertEqual(build_data(snapshot_fixture(), a).signature, build_data(snapshot_fixture(), b).signature)

    def test_missing_album_reference_is_retained(self):
        s = snapshot_fixture(); s.tracks.loc[0, 'AlbumId'] = 999
        d = build_data(s, Filters('2018-01-01', '2021-06-01', True))
        self.assertEqual(d.track_album['1'], 'unassigned')
        self.assertAlmostEqual(d.total.sum(), d.album.sum().sum())

    def test_invalid_month_filters_are_rejected(self):
        for value in ('', ' ', 'NaT', None, 'not-a-date'):
            with self.subTest(value=value), self.assertRaises((ValueError, TypeError)):
                Filters(value, '2021-06')
        with self.assertRaises(ValueError):
            Filters('2021-06', '2018-01')

    def test_duplicate_and_null_keys_are_reported_before_join(self):
        s = snapshot_fixture()
        s.invoices = pd.concat([s.invoices, s.invoices.iloc[[0]]], ignore_index=True)
        report = audit(s)
        self.assertEqual(report['duplicate_primary_keys']['invoice'], 1)
        self.assertFalse(report['safe_for_forecast'])
        s = snapshot_fixture(); s.lines.loc[0, 'TrackId'] = None
        self.assertFalse(audit(s)['safe_for_forecast'])

    def test_identifier_rejects_untrusted_sql(self):
        with self.assertRaises(AppError): identifier('invoice; DROP TABLE x')

    def test_query_closes_cursor_and_binds_values(self):
        class Cursor:
            column_names = ['n']
            closed = False
            def execute(self, sql, params): self.sql, self.params = sql, params
            def fetchall(self): return [{'n': 1}]
            def close(self): self.closed = True
        class Connection:
            c = Cursor()
            def cursor(self, **kwargs): return self.c
        c = Connection(); query(c, 'SELECT x WHERE month >= %s', ('2020-01-01',))
        self.assertTrue(c.c.closed)
        self.assertEqual(c.c.params, ('2020-01-01',))
