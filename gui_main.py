"""Entry point for GoExport GUI."""
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from goexport_gui.window import MainWindow
def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QWidget { color: #20242a; font-size: 10pt; }
        QMainWindow, QScrollArea, QScrollArea > QWidget > QWidget { background: #f4f6f8; }
        QDialog, QMessageBox { background: #f4f6f8; }
        QMessageBox QLabel { color: #20242a; background: transparent; }
        QMessageBox QPushButton {
            min-width: 76px;
            padding: 7px 13px;
            border: 1px solid #cbd1d8;
            border-radius: 5px;
            background: white;
            color: #20242a;
        }
        QMessageBox QPushButton:hover { background: #eef2f6; }
        QLabel#title { font-size: 23pt; font-weight: 650; color: #15181d; }
        QLabel#subtitle { color: #626a76; padding-bottom: 4px; }
        QLabel#status { font-weight: 600; }
        QFrame#card { background: white; border: 1px solid #dfe3e8; border-radius: 8px; }
        QLineEdit, QComboBox, QPlainTextEdit { background: white; border: 1px solid #cbd1d8; border-radius: 5px; padding: 7px; }
        QLineEdit:focus, QComboBox:focus { border-color: #3178c6; }
        QComboBox QAbstractItemView {
            background: white;
            color: #20242a;
            border: 0;
            outline: 0;
            padding: 4px;
            selection-background-color: #dceafb;
            selection-color: #163a61;
        }
        QWidget#comboPopup {
            background: white;
            border: 1px solid #cbd1d8;
        }
        QComboBox QAbstractItemView::item {
            min-height: 28px;
            padding: 4px 8px;
        }
        QPushButton { padding: 7px 13px; border: 1px solid #cbd1d8; border-radius: 5px; background: white; }
        QPushButton:hover { background: #eef2f6; }
        QPushButton#primaryButton { background: #246fbd; color: white; border: 0; font-weight: 650; }
        QPushButton#primaryButton:hover { background: #1c61a8; }
        QPushButton#primaryButton:disabled { background: #93b4d6; }
        QToolButton { border: 0; padding: 5px 2px; font-weight: 600; text-align: left; }
        QProgressBar { background: #e2e6ea; border: 0; border-radius: 4px; height: 8px; }
        QProgressBar::chunk { background: #2d7dcc; border-radius: 4px; }
    """)
    try: window = MainWindow()
    except Exception as error: QMessageBox.critical(None, "GoExport GUI", f"Unable to start the GUI:\n{error}"); return 1
    window.show(); return app.exec()
if __name__ == "__main__": raise SystemExit(main())
