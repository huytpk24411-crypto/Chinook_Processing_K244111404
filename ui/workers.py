"""Workers return values through Qt signals; widgets are touched only in UI slots."""
from PySide6.QtCore import QObject, QRunnable, Signal
from connectors.mysql import AppError


class Signals(QObject):
    result = Signal(object)


class Job(QRunnable):
    def __init__(self, token, function):
        super().__init__()
        self.token, self.function = token, function
        self.signals = Signals()

    def run(self):
        try:
            value = self.function()
            self.signals.result.emit((self.token, value, None))
        except AppError as exc:
            self.signals.result.emit((self.token, None, (exc.key, exc.detail)))
        except Exception as exc:
            # Do not expose exception text that could contain connection secrets.
            self.signals.result.emit((self.token, None, ('unexpected_error', type(exc).__name__)))
