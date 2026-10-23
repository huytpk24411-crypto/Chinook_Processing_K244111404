"""Explicit system font registration also supports Windows offscreen QA."""
import os
from pathlib import Path
from PySide6.QtGui import QFont, QFontDatabase


def initialize_font(application):
    font = Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts'/'segoeui.ttf'
    if font.is_file():
        QFontDatabase.addApplicationFont(str(font))
    application.setFont(QFont('Segoe UI', 10))
