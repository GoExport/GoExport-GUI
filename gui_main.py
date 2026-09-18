"""Entry point for GoExport GUI."""
import sys
from pathlib import Path
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox
from goexport_gui.window import MainWindow
def main() -> int:
    app = QApplication(sys.argv)

    icon_path = Path(__file__).parent / "goexport_gui" / "resources" / "default.ico"
    app.setWindowIcon(QIcon(str(icon_path)))

    app.setStyle("Fusion")
    app.setStyleSheet("""
        QWidget { color: #f7f1ec; font-size: 10pt; }
        QMainWindow, QScrollArea, QScrollArea > QWidget > QWidget,
        QDialog, QMessageBox { background: #171310; }
        QLabel { background: transparent; }
        QLabel#brandLogo { color: #ff9a52; font-size: 23pt; font-weight: 650; }
        QLabel#subtitle { color: #b9aaa0; padding-bottom: 4px; }
        QLabel#status { color: #fff8f2; font-weight: 600; }
        QFrame#card { background: #241d19; border: 1px solid #4c3b31; border-radius: 8px; }
        QMessageBox QLabel { color: #f7f1ec; background: transparent; }
        QMessageBox QPushButton {
            min-width: 76px;
            padding: 7px 13px;
            border: 1px solid #f47821;
            border-radius: 5px;
            background: #f47821;
            color: #21150d;
            font-weight: 650;
        }
        QMessageBox QPushButton:hover { background: #ff9a52; border-color: #ff9a52; }
        QMessageBox QPushButton:pressed { background: #d85d0b; border-color: #d85d0b; }
        QLineEdit, QComboBox, QPlainTextEdit {
            background: #15110f;
            color: #f7f1ec;
            border: 1px solid #574438;
            border-radius: 5px;
            padding: 7px;
            selection-background-color: #f47821;
            selection-color: #21150d;
        }
        QLineEdit:hover, QComboBox:hover, QPlainTextEdit:hover { border-color: #80604d; }
        QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus { border-color: #f47821; }
        QLineEdit:disabled, QComboBox:disabled, QPlainTextEdit:disabled {
            background: #201a17; color: #7e7169; border-color: #3a302a;
        }
        QComboBox QAbstractItemView {
            background: #241d19;
            color: #f7f1ec;
            border: 0;
            outline: 0;
            padding: 4px;
            selection-background-color: #f47821;
            selection-color: #21150d;
        }
        QListView, QTreeView, QTableView {
            background: #241d19; color: #f7f1ec; border: 1px solid #574438;
            selection-background-color: #f47821; selection-color: #21150d;
            alternate-background-color: #2c231e;
        }
        QHeaderView::section { background: #2c231e; color: #f7f1ec; border: 1px solid #574438; padding: 5px; }
        QWidget#comboPopup {
            background: #241d19;
            border: 1px solid #574438;
        }
        QComboBox QAbstractItemView::item {
            min-height: 28px;
            padding: 4px 8px;
        }
        QPushButton {
            padding: 7px 13px; border: 1px solid #6b5141; border-radius: 5px;
            background: #2c231e; color: #f7f1ec;
        }
        QPushButton:hover { background: #3a2c25; border-color: #f47821; }
        QPushButton:pressed { background: #171310; }
        QPushButton:disabled { background: #201a17; color: #766a63; border-color: #3a302a; }
        QPushButton#primaryButton { background: #f47821; color: #21150d; border: 0; font-weight: 650; }
        QPushButton#primaryButton:hover { background: #ff9a52; }
        QPushButton#primaryButton:pressed { background: #d85d0b; }
        QPushButton#primaryButton:disabled { background: #6d4931; color: #b29c8d; }
        QToolButton { border: 0; padding: 5px 2px; font-weight: 600; text-align: left; color: #ff9a52; }
        QToolButton:hover { color: #ffc197; }
        QProgressBar { background: #3a302a; border: 0; border-radius: 4px; height: 8px; }
        QProgressBar::chunk { background: #f47821; border-radius: 4px; }
        QScrollBar:vertical { background: #171310; width: 12px; margin: 0; }
        QScrollBar::handle:vertical { background: #574438; min-height: 28px; border-radius: 6px; }
        QScrollBar::handle:vertical:hover { background: #f47821; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QScrollBar:horizontal { background: #171310; height: 12px; margin: 0; }
        QScrollBar::handle:horizontal { background: #574438; min-width: 28px; border-radius: 6px; }
        QScrollBar::handle:horizontal:hover { background: #f47821; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        QToolTip { color: #21150d; background: #ffbc8d; border: 1px solid #f47821; }
    """)
    try: window = MainWindow()
    except Exception as error: QMessageBox.critical(None, "GoExport GUI", f"Unable to start the GUI:\n{error}"); return 1
    window.show(); return app.exec()
if __name__ == "__main__": raise SystemExit(main())
