import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from unittest.mock import patch
import pandas as pd
from PySide6.QtWidgets import QApplication, QLineEdit
from PySide6.QtCore import Qt, QDate, QCoreApplication, QEvent
from config.settings import ARTIFACTS
from ui.windows.main_window import MainWindow
from ui.state import ResultState
from ui.widgets.table import FrameModel
from ui.translations import Translator, COPY
from ui.fonts import initialize_font
from ui.windows.connection import ConnectionDialog
from config.settings import DatabaseConfig
from ml.forecast import train, forecast
from tests.fixtures import revenue_fixture


class UITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        initialize_font(cls.app)

    def setUp(self):
        self.preferences = patch('ui.windows.main_window.read_preferences', return_value={'language': 'vi'})
        self.save_preferences = patch('ui.windows.main_window.save_language')
        self.preferences.start(); self.save_preferences.start()
        self.w = MainWindow()

    def tearDown(self):
        self.w.close(); self.w.deleteLater(); self.app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.preferences.stop(); self.save_preferences.stop()

    def test_stale_background_result_is_rejected(self):
        state = ResultState(); revision = state.revision
        state.invalidate()
        self.assertFalse(state.accept(revision, pd.DataFrame({'old': [1]})))
        self.assertIsNone(state.forecast_rows)

    def test_password_dialog_masks_input_and_config_repr(self):
        dialog = ConnectionDialog(Translator('vi'), DatabaseConfig(), self.w)
        self.assertEqual(dialog.password.echoMode(), QLineEdit.EchoMode.Password)
        dialog.password.setText('unit_test_secret')
        self.assertNotIn('unit_test_secret', repr(dialog.config()))

    def test_entity_and_filter_change_clear_visible_forecast(self):
        self.w.data = revenue_fixture(); self.w.populate_entities()
        self.w.bundle = train(self.w.data)
        self.w.scope.setCurrentIndex(1)
        self.w.state.forecast_rows = forecast(self.w.data, self.w.bundle)
        self.w.render()
        self.assertGreater(len(self.w.prediction.table.frame), 0)
        self.w.entity.setCurrentIndex(1)
        self.assertIsNone(self.w.state.forecast_rows)
        self.assertTrue(self.w.prediction.table.frame.empty)
        self.w.snapshot = object()
        self.w.filters_changed()
        self.assertIsNone(self.w.bundle); self.assertIsNone(self.w.data)

    def test_bilingual_table_and_app_copy(self):
        tr = Translator('vi'); model = FrameModel(pd.DataFrame({'revenue': [1234.5]}), tr)
        self.assertEqual(model.headerData(0, Qt.Orientation.Horizontal), 'Doanh thu')
        vi = model.data(model.index(0, 0)); tr.language = 'en'
        self.assertEqual(model.headerData(0, Qt.Orientation.Horizontal), 'Revenue')
        self.assertNotEqual(vi, model.data(model.index(0,0)))
        self.assertTrue(all(len(pair) == 2 and all(pair) for pair in COPY.values()))
        catalog_model = FrameModel(pd.DataFrame({'name': ['linear']}), Translator('vi'))
        self.assertEqual(catalog_model.data(catalog_model.index(0,0)), 'linear')

    def test_language_switch_preserves_result_and_selected_id(self):
        self.w.data = revenue_fixture(); self.w.populate_entities(); self.w.bundle = train(self.w.data)
        self.w.scope.setCurrentIndex(1); self.w.entity.setCurrentIndex(1)
        self.w.state.forecast_rows = forecast(self.w.data, self.w.bundle)
        selected_id = self.w.entity.currentData()
        self.w.language.setCurrentIndex(1)
        self.assertEqual(self.w.entity.currentData(), selected_id)
        self.assertIsNotNone(self.w.state.forecast_rows)
        self.assertFalse(self.w.prediction.table.frame.empty)

    def test_empty_search_has_no_old_entity_or_result(self):
        self.w.data = revenue_fixture(); self.w.populate_entities(); self.w.scope.setCurrentIndex(1)
        self.w.search.setText('NO SUCH TRACK AT ALL')
        self.assertIsNone(self.w.entity.currentData())
        self.assertFalse(self.w.prediction.run.isEnabled())
        self.assertTrue(self.w.prediction.table.frame.empty)

    def test_real_widget_render_with_separate_test_fixture(self):
        # This validates widgets with a labeled test fixture, not a MySQL integration.
        self.w.data = revenue_fixture(); self.w.populate_entities(); self.w.bundle = train(self.w.data)
        for widget, date in [(self.w.start,self.w.data.total.index[0]),(self.w.end,self.w.data.total.index[-1])]:
            widget.blockSignals(True); widget.setDate(QDate(date.year,date.month,1)); widget.blockSignals(False)
        self.w.horizon.setCurrentIndex(1)
        self.w.state.forecast_rows = forecast(self.w.data, self.w.bundle, horizon=3)
        self.w.set_status('ready')
        self.w.nav.setCurrentRow(4); self.w.render(); self.w.show(); self.app.processEvents()
        folder = ARTIFACTS/'verification'; folder.mkdir(exist_ok=True)
        self.w.grab().save(str(folder/'forecast_test_fixture.png'))
        self.w.language.setCurrentIndex(1); self.app.processEvents()
        self.w.grab().save(str(folder/'english_test_fixture.png'))
        self.assertIn('Revenue', self.w.windowTitle())
