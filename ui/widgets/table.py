import numbers
import pandas as pd
from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtWidgets import QTableView, QHeaderView


class FrameModel(QAbstractTableModel):
    def __init__(self, frame, translator, parent=None):
        super().__init__(parent)
        self.frame, self.tr = frame, translator

    def rowCount(self, parent=None):
        return len(self.frame)

    def columnCount(self, parent=None):
        return len(self.frame.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if (not index.isValid() or index.row() >= len(self.frame) or
                index.column() >= len(self.frame.columns)):
            return None
        value = self.frame.iloc[index.row(), index.column()]
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return int(Qt.AlignmentFlag.AlignVCenter | (Qt.AlignmentFlag.AlignRight if isinstance(value, numbers.Number) else Qt.AlignmentFlag.AlignLeft))
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if pd.isna(value):
            return '—'
        if isinstance(value, pd.Timestamp):
            return self.tr.month(value)
        if isinstance(value, bool):
            return self.tr('yes' if value else 'no')
        if isinstance(value, numbers.Integral):
            return self.tr.number(value, 0)
        if isinstance(value, numbers.Real):
            return self.tr.number(value)
        column = self.frame.columns[index.column()]
        translated = column in ('scope', 'method', 'subset') or (column == 'entity' and str(value) == 'total')
        return self.tr(str(value)) if translated else str(value)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.tr(self.frame.columns[section]) if 0 <= section < len(self.frame.columns) else None
            return str(section+1)
        return None


class DataTable(QTableView):
    def __init__(self, translator):
        super().__init__()
        self.tr, self.frame = translator, pd.DataFrame()
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.verticalHeader().hide()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setStretchLastSection(True)

    def show_frame(self, frame):
        self.frame = frame.copy()
        previous = self.model()
        self.setModel(FrameModel(self.frame, self.tr, self))
        if previous is not None:
            previous.deleteLater()
        self.resizeColumnsToContents()
        for i in range(self.model().columnCount()):
            self.setColumnWidth(i, min(370, max(110, self.columnWidth(i))))
