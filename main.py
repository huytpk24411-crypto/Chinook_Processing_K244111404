"""Main entry: browser interface by default; use --desktop for PySide6."""
import sys


def desktop_main():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    from config.settings import ARTIFACTS
    from ui.windows.main_window import MainWindow
    from ui.fonts import initialize_font
    ARTIFACTS.mkdir(exist_ok=True)
    app = QApplication(sys.argv)
    initialize_font(app)
    app.setStyle('Fusion')
    window = MainWindow(); window.show()
    if '--connect' in sys.argv:
        QTimer.singleShot(0, window.open_connection)
    elif window.config.password:
        QTimer.singleShot(0, window.connect_configured)
    return app.exec()


def main():
    if '--desktop' in sys.argv:
        sys.argv.remove('--desktop')
        return desktop_main()
    from web_app import main as browser_main
    return browser_main()


if __name__ == '__main__':
    sys.exit(main())
