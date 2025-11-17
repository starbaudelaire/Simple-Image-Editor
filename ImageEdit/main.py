import sys
from PyQt5 import QtWidgets
from ui.window import MainWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    # --- DARK THEME STYLESHEET ---
    app.setStyleSheet("""
        QWidget {
            background-color: #2e2e2e;
            color: #f0f0f0;
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
        }
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border-radius: 4px;
            padding: 8px 16px;
            border: none;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3e8e41;
        }
        QPushButton:disabled {
            background-color: #555;
            color: #888;
        }
        QLabel {
            color: #e0e0e0;
        }
        QSlider::groove:horizontal {
            border: 1px solid #555;
            height: 6px;
            background: #444;
            margin: 2px 0;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #4CAF50;
            border: 1px solid #444;
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }
        QSlider::add-page:horizontal {
            background: #444;
        }
        QSlider::sub-page:horizontal {
            background: #4CAF50;
        }
        QMessageBox {
            background-color: #2e2e2e;
        }
    """)

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())