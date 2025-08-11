# step2_buttons.py
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QGridLayout, QLineEdit, QLabel, QPushButton)

class Calc(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calc • Step 2")
        self.resize(420, 420)

        root = QWidget(); self.setCentralWidget(root)
        main = QVBoxLayout(root)

        self.sub = QLabel(""); self.sub.setAlignment(Qt.AlignmentFlag.AlignRight)
        main.addWidget(self.sub)

        self.display = QLineEdit(); self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setPlaceholderText("0")
        main.addWidget(self.display)

        grid = QGridLayout(); main.addLayout(grid)

        # چند دکمه نمونه
        buttons = [
            ("7", lambda: self.type_text("7")), ("8", lambda: self.type_text("8")),
            ("9", lambda: self.type_text("9")), ("/", lambda: self.type_text("/")),
            ("4", lambda: self.type_text("4")), ("5", lambda: self.type_text("5")),
            ("6", lambda: self.type_text("6")), ("*", lambda: self.type_text("*")),
            ("1", lambda: self.type_text("1")), ("2", lambda: self.type_text("2")),
            ("3", lambda: self.type_text("3")), ("-", lambda: self.type_text("-")),
            ("0", lambda: self.type_text("0")), (".", lambda: self.type_text(".")),
            ("(", lambda: self.type_text("(")), (")", lambda: self.type_text(")")),
        ]
        # قرار دادن در گرید 4x4
        r = c = 0
        for text, cb in buttons:
            b = QPushButton(text); b.clicked.connect(cb)
            grid.addWidget(b, r, c)
            c += 1
            if c == 4: c = 0; r += 1

    def type_text(self, s: str):
        self.display.insert(s)

def main():
    app = QApplication(sys.argv)
    w = Calc(); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
