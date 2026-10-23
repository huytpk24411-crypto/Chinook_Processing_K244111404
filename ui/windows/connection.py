from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout, QLabel,
                               QLineEdit, QSpinBox, QVBoxLayout)
from config.settings import DatabaseConfig


class ConnectionDialog(QDialog):
    def __init__(self, translator, config, parent=None):
        super().__init__(parent)
        tr = translator
        self.setWindowTitle(tr('connection'))
        self.setMinimumWidth(440)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.host = QLineEdit(config.host)
        self.port = QSpinBox(); self.port.setRange(1, 65535); self.port.setValue(config.port)
        self.user = QLineEdit(config.user)
        self.database = QLineEdit(config.database)
        self.password = QLineEdit(config.password)
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        for key, widget in [('host', self.host), ('port', self.port), ('user', self.user),
                            ('database', self.database), ('password', self.password)]:
            form.addRow(tr(key), widget)
        layout.addLayout(form)
        note = QLabel(tr('password_note')); note.setWordWrap(True); layout.addWidget(note)
        buttons = QDialogButtonBox()
        connect = buttons.addButton(tr('connect'), QDialogButtonBox.ButtonRole.AcceptRole)
        connect.clicked.connect(self.accept)
        layout.addWidget(buttons)

    def config(self):
        return DatabaseConfig(self.host.text().strip(), self.port.value(), self.user.text().strip(),
                              self.database.text().strip(), self.password.text())
