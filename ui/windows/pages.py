"""Screen composition; data queries and ML algorithms are kept outside the UI."""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTabWidget, QTextBrowser, QSizePolicy)
from ui.widgets.chart import RevenueChart
from ui.widgets.table import DataTable


def label(window, key):
    item = QLabel(); item.setWordWrap(True)
    item.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
    if key in ('start', 'end', 'scope', 'method', 'horizon'):
        item.setWordWrap(False)
        item.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    window.bindings.append((item.setText, key))
    return item


def button(window, key, callback, primary=False):
    item = QPushButton()
    window.bindings.append((item.setText, key))
    item.clicked.connect(callback)
    if primary:
        item.setObjectName('primary')
    return item


class Page(QWidget):
    def __init__(self, window, key):
        super().__init__()
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(10)
        title = label(window, key); title.setObjectName('pageTitle'); self.body.addWidget(title)


class ConnectionPage(Page):
    def __init__(self, w):
        super().__init__(w, 'connection')
        self.body.addWidget(label(w, 'readonly_note'))
        self.connect = button(w, 'connect', w.open_connection, True)
        self.body.addWidget(self.connect)
        self.body.addWidget(label(w, 'password_note'))
        self.body.addStretch()


class OverviewPage(Page):
    def __init__(self, w):
        super().__init__(w, 'overview')
        self.summary = QLabel(); self.summary.setWordWrap(True); self.summary.setMinimumHeight(48); self.body.addWidget(self.summary)
        self.body.addWidget(label(w, 'unit_note'))
        self.chart = RevenueChart(w.tr); self.body.addWidget(self.chart, 2)
        self.body.addWidget(label(w, 'reconciliation'))
        self.table = DataTable(w.tr); self.body.addWidget(self.table, 2)
        row = QHBoxLayout()
        row.addWidget(button(w, 'export_csv', lambda: w.export_csv(self.table.frame)))
        row.addWidget(button(w, 'export_png', lambda: w.export_png(self.chart)))
        row.addStretch(); self.body.addLayout(row)


class ExplorePage(Page):
    def __init__(self, w):
        super().__init__(w, 'explore')
        self.body.addWidget(label(w, 'ranking'))
        self.table = DataTable(w.tr); self.body.addWidget(self.table, 3)
        self.body.addWidget(label(w, 'history'))
        self.history = DataTable(w.tr); self.body.addWidget(self.history, 2)
        row = QHBoxLayout()
        row.addWidget(button(w, 'export_ranking', lambda: w.export_csv(self.table.frame)))
        row.addWidget(button(w, 'export_history', lambda: w.export_csv(self.history.frame)))
        row.addStretch(); self.body.addLayout(row)


class TrainingPage(Page):
    def __init__(self, w):
        super().__init__(w, 'training')
        row = QHBoxLayout()
        self.train = button(w, 'train', w.run_training, True)
        self.save = button(w, 'save_model', w.save_model)
        self.load = button(w, 'load_model', w.load_model)
        for b in (self.train, self.save, self.load): row.addWidget(b)
        row.addStretch(); self.body.addLayout(row)
        self.summary = QLabel(); self.summary.setWordWrap(True); self.summary.setMinimumHeight(58); self.body.addWidget(self.summary)
        self.body.addWidget(label(w, 'metric_note'))
        self.tabs = QTabWidget()
        self.scores = DataTable(w.tr); self.details = DataTable(w.tr)
        self.chart = RevenueChart(w.tr)
        for widget in (self.scores, self.details, self.chart): self.tabs.addTab(widget, '')
        self.body.addWidget(self.tabs, 1)
        self.body.addWidget(label(w, 'test_note'))
        row = QHBoxLayout()
        row.addWidget(button(w, 'export_csv', lambda: w.export_csv(
            self.details.frame if self.tabs.currentIndex() == 1 else self.scores.frame)))
        row.addWidget(button(w, 'export_png', lambda: w.export_png(self.chart)))
        row.addStretch(); self.body.addLayout(row)


class ForecastPage(Page):
    def __init__(self, w):
        super().__init__(w, 'forecast')
        self.run = button(w, 'run_forecast', w.run_forecast, True)
        self.body.addWidget(self.run)
        self.note = QLabel(); self.note.setWordWrap(True)
        self.note.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.body.addWidget(self.note)
        self.body.addWidget(label(w, 'forecast_note'))
        self.chart = RevenueChart(w.tr); self.body.addWidget(self.chart, 3)
        self.chart.setMinimumHeight(180); self.chart.setMaximumHeight(225)
        self.tabs = QTabWidget()
        self.table = DataTable(w.tr); self.reconcile = DataTable(w.tr)
        self.tabs.setMinimumHeight(170)
        self.tabs.addTab(self.table, ''); self.tabs.addTab(self.reconcile, '')
        self.body.addWidget(self.tabs, 2)
        row = QHBoxLayout()
        row.addWidget(button(w, 'export_csv', lambda: w.export_csv(
            self.table.frame if self.tabs.currentIndex() == 0 else self.reconcile.frame)))
        row.addWidget(button(w, 'export_png', lambda: w.export_png(self.chart)))
        row.addStretch(); self.body.addLayout(row)


class QualityPage(Page):
    def __init__(self, w):
        super().__init__(w, 'quality')
        self.body.addWidget(label(w, 'quality_intro'))
        self.tabs = QTabWidget()
        self.table = DataTable(w.tr); self.schema = DataTable(w.tr); self.relations = DataTable(w.tr)
        for widget, name in [(self.table, ''), (self.schema, 'Schema'), (self.relations, 'Foreign keys')]:
            self.tabs.addTab(widget, name)
        self.body.addWidget(self.tabs, 1)
        self.body.addWidget(button(w, 'export_csv', lambda: w.export_csv(self.table.frame)))


class ExplanationPage(Page):
    def __init__(self, w):
        super().__init__(w, 'explanation')
        self.text = QTextBrowser(); self.body.addWidget(self.text)
