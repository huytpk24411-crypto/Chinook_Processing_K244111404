from pathlib import Path
import json
import pandas as pd
from PySide6.QtCore import QDate, QThreadPool, Slot
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QListWidget, QStackedWidget, QLineEdit, QDateEdit, QCheckBox,
    QPushButton, QFileDialog, QProgressBar, QScrollArea, QDialog)
from config.settings import ROOT, ARTIFACTS, DatabaseConfig, read_preferences, save_language
from connectors.mysql import AppError
from repositories.chinook import ChinookRepository
from services.data import Filters, audit, build_data
from services.audit_report import write_audit
from services.model_report import write_model_report
from ml.forecast import train, forecast, eligible
from ml.persistence import load_bundle, save_bundle
from ui.translations import Translator
from ui.workers import Job
from ui.state import ResultState
from ui.windows.connection import ConnectionDialog
from ui.windows.pages import (label, button, ConnectionPage, OverviewPage, ExplorePage,
                              TrainingPage, ForecastPage, QualityPage, ExplanationPage)

NAV = ['connection', 'overview', 'explore', 'training', 'forecast', 'quality', 'explanation']


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tr = Translator(read_preferences().get('language', 'vi'))
        self.config = DatabaseConfig.from_env()
        self.snapshot = self.report = self.data = self.bundle = None
        self.state = ResultState()
        self.bindings, self.jobs = [], {}
        self.busy = False
        self.status_key, self.status_detail = 'not_connected', ''
        self.pool = QThreadPool(self); self.pool.setMaxThreadCount(2)
        self.resize(1240, 850); self.setMinimumSize(980, 680)
        self.setStyleSheet((ROOT/'ui/styles/light.qss').read_text(encoding='utf-8'))
        root = QWidget(); self.setCentralWidget(root)
        outer = QHBoxLayout(root); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        side = QWidget(); side.setFixedWidth(225); sidebox = QVBoxLayout(side)
        sidebox.setContentsMargins(12, 12, 12, 12)
        brand = QLabel('CHINOOK'); brand.setObjectName('brand'); sidebox.addWidget(brand)
        sidebox.addWidget(label(self, 'subtitle'))
        self.nav = QListWidget(); self.nav.setObjectName('sidebar')
        self.nav.addItems(NAV); sidebox.addWidget(self.nav, 1)
        self.language = QComboBox(); self.language.addItem('Tiếng Việt', 'vi'); self.language.addItem('English', 'en')
        self.language.setCurrentIndex(0 if self.tr.language == 'vi' else 1)
        self.language.currentIndexChanged.connect(self.change_language)
        sidebox.addWidget(self.language); outer.addWidget(side)
        content = QWidget(); box = QVBoxLayout(content); box.setContentsMargins(20, 16, 20, 16)
        box.setSpacing(9)
        self.status = QLabel(); self.status.setObjectName('status'); self.status.setWordWrap(True); box.addWidget(self.status)
        self.progress = QProgressBar(); self.progress.setRange(0, 0); self.progress.hide(); box.addWidget(self.progress)
        self.filter_panel = QWidget(); fb = QVBoxLayout(self.filter_panel); fb.setContentsMargins(0, 0, 0, 0)
        dates = QHBoxLayout()
        self.start = QDateEdit(QDate.currentDate()); self.end = QDateEdit(QDate.currentDate())
        for key, widget in [('start', self.start), ('end', self.end)]:
            widget.setDisplayFormat('MM/yyyy'); widget.setCalendarPopup(True)
            dates.addWidget(label(self, key)); dates.addWidget(widget)
            widget.dateChanged.connect(self.filters_changed)
        self.apply = button(self, 'apply', self.apply_filters); dates.addWidget(self.apply); dates.addStretch()
        fb.addLayout(dates)
        self.boundaries = QCheckBox(); self.coverage = QCheckBox()
        for key, widget in [('boundaries', self.boundaries), ('coverage', self.coverage)]:
            self.bindings.append((widget.setText, key)); widget.toggled.connect(self.filters_changed)
        checkrow = QHBoxLayout(); checkrow.addWidget(self.boundaries); checkrow.addWidget(self.coverage); checkrow.addStretch()
        fb.addLayout(checkrow)
        self.boundary_note = label(self, 'boundary_note'); fb.addWidget(self.boundary_note)
        selection = QHBoxLayout()
        self.scope = QComboBox()
        for k in ('total', 'track', 'album'): self.scope.addItem(k, k)
        self.search = QLineEdit(); self.entity = QComboBox(); self.entity.setMinimumWidth(180)
        self.entity.setMaximumWidth(350)
        selection.addWidget(label(self, 'scope')); selection.addWidget(self.scope)
        selection.addWidget(self.search, 1); selection.addWidget(self.entity, 2)
        self.scope.currentIndexChanged.connect(self.scope_changed)
        self.search.textChanged.connect(self.populate_entities)
        self.entity.currentIndexChanged.connect(self.selection_changed)
        fb.addLayout(selection)
        methodrow = QHBoxLayout(); self.method = QComboBox(); self.horizon = QComboBox()
        for k in ('linear', 'previous', 'mean3'): self.method.addItem(k, k)
        for n in (1, 3, 6): self.horizon.addItem(str(n), n)
        methodrow.addWidget(label(self, 'method')); methodrow.addWidget(self.method, 1)
        methodrow.addWidget(label(self, 'horizon')); methodrow.addWidget(self.horizon); methodrow.addStretch()
        self.method.currentIndexChanged.connect(self.selection_changed)
        self.horizon.currentIndexChanged.connect(self.selection_changed)
        fb.addLayout(methodrow); box.addWidget(self.filter_panel)
        self.pages = QStackedWidget()
        self.connection_page = ConnectionPage(self)
        self.overview = OverviewPage(self); self.explore = ExplorePage(self)
        self.training = TrainingPage(self); self.prediction = ForecastPage(self)
        self.quality = QualityPage(self); self.explanation = ExplanationPage(self)
        for page in (self.connection_page, self.overview, self.explore, self.training,
                     self.prediction, self.quality, self.explanation):
            scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QScrollArea.Shape.NoFrame)
            scroll.setWidget(page); self.pages.addWidget(scroll)
        box.addWidget(self.pages, 1); outer.addWidget(content, 1)
        self.nav.currentRowChanged.connect(self.navigate); self.nav.setCurrentRow(0)
        self.retranslate(); self.update_actions()

    def set_status(self, key, detail=''):
        self.status_key, self.status_detail = key, detail
        self.status.setText(self.tr(key) + (f' ({detail})' if detail else ''))

    def navigate(self, row):
        self.pages.setCurrentIndex(row)
        self.filter_panel.setVisible(row in (1, 2, 3, 4))

    def change_language(self):
        self.tr.language = self.language.currentData()
        try: save_language(self.tr.language)
        except OSError: pass
        self.retranslate(); self.populate_entities(invalidate=False); self.render()
        # Force a full redraw after layouts/headers change language.
        self.centralWidget().update()

    def retranslate(self):
        self.setWindowTitle(self.tr('app'))
        for setter, key in self.bindings: setter(self.tr(key))
        for i, key in enumerate(NAV): self.nav.item(i).setText(self.tr(key))
        for combo in (self.scope, self.method):
            combo.blockSignals(True)
            for i in range(combo.count()): combo.setItemText(i, self.tr(combo.itemData(i)))
            combo.blockSignals(False)
        self.search.setPlaceholderText(self.tr('search'))
        self.boundaries.setToolTip(self.tr('boundary_note'))
        self.coverage.setToolTip(self.tr('coverage_error'))
        self.training.tabs.setTabText(0, self.tr('training'))
        self.training.tabs.setTabText(1, self.tr('actual')+' / '+self.tr('predicted'))
        self.training.tabs.setTabText(2, self.tr('history'))
        self.prediction.tabs.setTabText(0, self.tr('predicted'))
        self.prediction.tabs.setTabText(1, self.tr('reconciliation'))
        self.quality.tabs.setTabText(0, self.tr('quality'))
        self.quality.tabs.setTabText(1, self.tr('schema_tab'))
        self.quality.tabs.setTabText(2, self.tr('relations_tab'))
        self.explanation.text.setPlainText(self.tr('explanation_text'))
        self.set_status(self.status_key, self.status_detail)

    def update_actions(self):
        self.filter_panel.setEnabled(self.snapshot is not None and not self.busy)
        self.connection_page.connect.setEnabled(not self.busy)
        self.training.train.setEnabled(self.data is not None and not self.busy)
        self.training.load.setEnabled(self.data is not None and not self.busy)
        self.training.save.setEnabled(self.bundle is not None and not self.busy)
        self.prediction.run.setEnabled(self.data is not None and not self.busy and
                                      (self.scope.currentData() == 'total' or self.entity.currentData() is not None))
        self.progress.setVisible(self.busy)

    def submit(self, function, callback):
        if self.busy: return
        token = self.state.revision
        job = Job(token, function)
        self.jobs[id(job)] = (job, callback)
        # One job at a time. The slot receiver belongs to the GUI thread.
        job.signals.result.connect(self.job_result)
        self.busy = True; self.set_status('loading'); self.update_actions()
        self.pool.start(job)

    @Slot(object)
    def job_result(self, payload):
        token, value, error = payload
        _, callback = self.jobs.pop(next(iter(self.jobs)))
        self.busy = False
        if token == self.state.revision:
            if error: self.set_status(*error)
            else:
                try: callback(value)
                except AppError as exc: self.set_status(exc.key, exc.detail)
                except Exception as exc: self.set_status('unexpected_error', type(exc).__name__)
        self.update_actions()

    def open_connection(self):
        if self.busy: return
        dialog = ConnectionDialog(self.tr, self.config, self)
        if dialog.exec() != QDialog.DialogCode.Accepted: return
        self.config = dialog.config()
        self.connect_configured()

    def connect_configured(self):
        """Load MySQL with configured credentials, without opening a dialog."""
        if self.busy: return
        self.snapshot = self.report = self.data = self.bundle = None
        self.state.invalidate(); self.render()
        config = self.config
        def load():
            snapshot = ChinookRepository(config).load()
            report = audit(snapshot); write_audit(report)
            return snapshot, report
        self.submit(load, self.connected)

    def connected(self, result):
        self.snapshot, self.report = result
        inv = self.snapshot.invoices
        if inv.empty or not inv.InvoiceDate.notna().any():
            self.set_status('no_data'); self.render(); return
        for widget, date in [(self.start, inv.InvoiceDate.min()), (self.end, inv.InvoiceDate.max())]:
            widget.blockSignals(True); widget.setDate(QDate(date.year, date.month, 1)); widget.blockSignals(False)
        self.set_status('connected'); self.render()
        self.apply_filters()

    def filters_changed(self):
        if self.snapshot is None: return
        self.state.invalidate(); self.data = self.bundle = None
        self.set_status('stale'); self.render(); self.update_actions()

    def apply_filters(self):
        if self.snapshot is None: return
        self.state.invalidate(); self.data = self.bundle = None
        self.render()
        filters = Filters(self.start.date().toString('yyyy-MM-01'), self.end.date().toString('yyyy-MM-01'),
                          self.boundaries.isChecked(), self.coverage.isChecked())
        snapshot = self.snapshot
        self.submit(lambda: build_data(snapshot, filters), self.data_ready)

    def data_ready(self, data):
        self.data = data; self.populate_entities(); self.set_status('ready'); self.render()
        if self.nav.currentRow() == 0: self.nav.setCurrentRow(1)

    def scope_changed(self):
        self.search.blockSignals(True); self.search.clear(); self.search.blockSignals(False)
        self.populate_entities()

    def populate_entities(self, *args, invalidate=True):
        old = self.entity.currentData(); self.entity.blockSignals(True); self.entity.clear()
        scope = self.scope.currentData()
        self.search.setEnabled(scope != 'total'); self.entity.setEnabled(scope != 'total')
        if self.data is not None and scope != 'total':
            catalog = self.data.tracks if scope == 'track' else self.data.albums
            idcol, namecol = ('TrackId', 'Name') if scope == 'track' else ('AlbumId', 'Title')
            text = self.search.text().strip().casefold()
            for row in catalog.to_dict('records'):
                name = str(row[namecol]) if pd.notna(row[namecol]) else self.tr('unassigned' if row[idcol] == 'unassigned' else 'unknown_name')
                item = f'{name}  [ID: {row[idcol]}]'
                if not text or text in item.casefold(): self.entity.addItem(item, row[idcol])
            if self.entity.findData(old) >= 0: self.entity.setCurrentIndex(self.entity.findData(old))
        self.entity.blockSignals(False)
        if invalidate: self.selection_changed()

    def selection_changed(self):
        self.state.invalidate()
        if self.data is not None: self.set_status('selection_stale')
        self.render(); self.update_actions()

    def run_training(self):
        if self.data is None: return
        if not eligible(self.data):
            self.set_status('insufficient_history'); return
        data = self.data
        def work():
            bundle = train(data); write_model_report(bundle)
            return bundle
        self.submit(work, self.trained)

    def trained(self, bundle):
        self.bundle = bundle; self.state.forecast_rows = None
        self.set_status('trained'); self.render()

    def run_forecast(self):
        if self.data is None: return
        data, bundle = self.data, self.bundle
        method, horizon = self.method.currentData(), self.horizon.currentData()
        if method == 'linear' and bundle is None:
            self.set_status('insufficient_history' if not eligible(data) else 'not_trained'); return
        self.state.forecast_rows = None; self.render()
        revision = self.state.revision
        def done(rows):
            self.state.accept(revision, rows); self.set_status('ready'); self.render()
        self.submit(lambda: forecast(data, bundle, method, horizon), done)

    def save_model(self):
        if self.bundle is None: self.set_status('not_trained'); return
        path, _ = QFileDialog.getSaveFileName(self, self.tr('save_model'), str(ARTIFACTS/'revenue_model.json'), 'JSON (*.json)')
        if path:
            bundle = self.bundle
            self.submit(lambda: save_bundle(bundle, path), lambda _: self.set_status('model_saved'))

    def load_model(self):
        if self.data is None: return
        path, _ = QFileDialog.getOpenFileName(self, self.tr('load_model'), str(ARTIFACTS), 'JSON (*.json)')
        if path:
            data = self.data
            def done(bundle):
                self.bundle = bundle; self.state.forecast_rows = None
                self.set_status('model_loaded'); self.render()
            self.submit(lambda: load_bundle(path, data), done)

    def export_csv(self, frame):
        if frame.empty: self.set_status('no_data'); return
        path, _ = QFileDialog.getSaveFileName(self, self.tr('export_csv'), str(ARTIFACTS/'export.csv'), 'CSV (*.csv)')
        if path:
            data = frame.copy()
            self.submit(lambda: data.to_csv(path, index=False, encoding='utf-8-sig'), lambda _: self.set_status('exported'))

    def export_png(self, chart):
        if self.data is None: self.set_status('no_data'); return
        path, _ = QFileDialog.getSaveFileName(self, self.tr('export_png'), str(ARTIFACTS/'chart.png'), 'PNG (*.png)')
        if path:
            try: chart.figure.savefig(path, dpi=160); self.set_status('exported')
            except OSError: self.set_status('unexpected_error')

    def selected_history(self):
        if self.data is None: return None
        scope, entity = self.scope.currentData(), self.entity.currentData()
        if scope != 'total' and entity is None: return None
        return self.data.history(scope, entity)

    def selected_rows(self, rows):
        scope = self.scope.currentData()
        entity = 'total' if scope == 'total' else self.entity.currentData()
        return rows.loc[(rows.scope == scope) & (rows.entity == entity)].copy()

    def render(self):
        self.render_quality()
        empty = pd.DataFrame()
        for table in [self.overview.table, self.explore.table, self.explore.history,
                      self.training.scores, self.training.details, self.prediction.table, self.prediction.reconcile]:
            table.show_frame(empty)
        self.overview.summary.clear(); self.training.summary.setText(self.tr('not_trained'))
        self.prediction.note.setText(self.tr('allocation_note'))
        for chart in [self.overview.chart, self.training.chart, self.prediction.chart]: chart.plot()
        if self.data is None: return
        d = self.data
        self.overview.summary.setText(self.tr('overview_summary', months=len(d.total), start=self.tr.month(d.total.index[0]),
            end=self.tr.month(d.total.index[-1]), revenue=self.tr.number(d.total.sum()), tracks=len(d.tracks), albums=len(d.albums)))
        self.overview.table.show_frame(d.reconciliation()); self.overview.chart.plot(d.total)
        scope, history = self.scope.currentData(), self.selected_history()
        if scope == 'total': ranking = pd.DataFrame({'month': d.total.index, 'revenue': d.total.values})
        else:
            values = getattr(d, scope).sum().sort_values(ascending=False)
            catalog = (d.tracks.set_index('TrackId').Name if scope == 'track' else d.albums.set_index('AlbumId').Title)
            names = catalog.reindex(values.index).fillna(self.tr('unassigned' if scope == 'album' else 'unknown_name'))
            ranking = pd.DataFrame({'id': values.index, 'name': names.values, 'revenue': values.values})
            text = self.search.text().strip().casefold()
            if text: ranking = ranking.loc[(ranking['id'].astype(str)+' '+ranking['name'].astype(str)).str.casefold().str.contains(text, regex=False)]
        self.explore.table.show_frame(ranking)
        if history is not None:
            self.explore.history.show_frame(pd.DataFrame({'month': history.index, 'revenue': history.values}))
            if not (history > 0).any(): self.prediction.note.setText(self.tr('never_sold')+'\n'+self.tr('allocation_note'))
        if self.bundle is not None: self.render_evaluation(history)
        rows = self.state.forecast_rows
        if rows is not None:
            selected = self.selected_rows(rows)
            self.prediction.table.show_frame(selected)
            reconcile = rows.groupby(['month', 'scope']).predicted.sum().unstack('scope')
            reconcile['difference'] = reconcile.total-reconcile.track
            self.prediction.reconcile.show_frame(reconcile.reset_index())
            if history is not None:
                pred = selected.set_index('month').predicted
                self.prediction.chart.plot(history, pred, pred.index[0] if len(pred) else None)
                if len(pred):
                    origin = self.tr('forecast_origin', origin=self.tr.month(history.index[-1]),
                                     start=self.tr.month(pred.index[0]), end=self.tr.month(pred.index[-1]))
                    self.prediction.note.setText(self.tr(self.method.currentData())+' · '+origin+'\n'+self.prediction.note.text())

    def render_evaluation(self, history):
        m = self.bundle.metadata; split = m['split']
        self.training.summary.setText(self.tr('training_summary', train=split['train']['n'], ts=split['train']['start'],
            te=split['train']['end'], val=split['validation']['n'], test=split['test']['n'],
            ss=split['test']['start'], se=split['test']['end'], features=', '.join(self.bundle.features),
            window=self.bundle.window or self.tr('all_history'), deployment=split['deployment_fit']['n']))
        self.training.scores.show_frame(self.bundle.scores.loc[self.bundle.scores.scope == self.scope.currentData()])
        selected = self.selected_rows(self.bundle.evaluation)
        self.training.details.show_frame(selected)
        chart_rows = selected.loc[selected.method == self.method.currentData()]
        if history is not None and len(chart_rows):
            self.training.chart.plot(history, chart_rows.set_index('month').predicted, chart_rows.month.min())

    def render_quality(self):
        if self.report is None:
            for table in (self.quality.table, self.quality.schema, self.quality.relations): table.show_frame(pd.DataFrame())
            return
        rows = []
        for key, value in self.report.items():
            if key in ('source', 'currency', 'boundary_completeness', 'schema', 'relations'): continue
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    rows.append({'check': self.tr(key)+' / '+str(subkey), 'value': json.dumps(subvalue, ensure_ascii=False)})
            else:
                shown = (self.tr('yes' if value else 'no') if isinstance(value, bool) else
                         self.tr.number(value, 6 if 'fraction' in key else 2) if isinstance(value, (float,int)) else str(value))
                rows.append({'check': self.tr(key), 'value': shown})
        self.quality.table.show_frame(pd.DataFrame(rows))
        self.quality.schema.show_frame(self.snapshot.schema)
        self.quality.relations.show_frame(self.snapshot.relations)

    def closeEvent(self, event):
        # Do not destroy signal receivers while a short-lived DB worker is finishing.
        if self.busy:
            event.ignore(); return
        event.accept()
