# step1_window.py
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLineEdit, QLabel

class Calc(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calc • Step 1")
        self.resize(380, 200)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        self.sub = QLabel("")                          # نمایشگر فرعی
        self.sub.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.sub)

        self.display = QLineEdit()                     # نمایشگر اصلی
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setPlaceholderText("0")
        layout.addWidget(self.display)

def main():
    app = QApplication(sys.argv)
    w = Calc()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
