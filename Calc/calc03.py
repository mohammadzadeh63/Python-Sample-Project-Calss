# step3_eval_basic.py
import sys, math, re
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QGridLayout, QLineEdit, QLabel, QPushButton, QMessageBox)

ALLOWED_FUNCS = {"abs": abs, "round": round}
ALLOWED_PATTERN = re.compile(r"^[0-9\s\+\-\*/\.\(\)]+$")  # ساده: چهار عمل و پرانتز

def safe_eval(expr: str) -> float:
    expr = (expr or "").strip()
    if not expr: return 0.0
    if "__" in expr or not ALLOWED_PATTERN.match(expr):
        raise ValueError("Invalid/unsafe")
    return eval(expr, {"__builtins__": {}}, ALLOWED_FUNCS.copy())

class Calc(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calc • Step 3")
        self.resize(420, 480)

        root = QWidget(); self.setCentralWidget(root)
        main = QVBoxLayout(root)

        self.sub = QLabel(""); self.sub.setAlignment(Qt.AlignmentFlag.AlignRight)
        main.addWidget(self.sub)

        self.display = QLineEdit(); self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setPlaceholderText("0")
        self.display.returnPressed.connect(self.evaluate)  # Enter == =
        main.addWidget(self.display)

        grid = QGridLayout(); main.addLayout(grid)
        keys = [
            "7","8","9","/","4","5","6","*",
            "1","2","3","-","0",".","(",")"
        ]
        r=c=0
        for k in keys:
            b = QPushButton(k); b.clicked.connect(lambda _,x=k:self.type_text(x))
            grid.addWidget(b, r, c); c+=1
            if c==4: c=0; r+=1

        eq = QPushButton("="); eq.clicked.connect(self.evaluate)
        clr = QPushButton("C"); clr.clicked.connect(self.clear_all)
        grid.addWidget(clr, r, 0, 1, 2)
        grid.addWidget(eq,  r, 2, 1, 2)

    def type_text(self, s: str): self.display.insert(s)
    def clear_all(self): self.display.clear(); self.sub.setText("")

    def evaluate(self):
        expr = self.display.text().strip()
        if not expr: return
        self.sub.setText(expr)
        try:
            val = safe_eval(expr)
            self.display.setText(self._fmt(val))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"عبارت نامعتبر:\n{e}")

    def _fmt(self, v: float) -> str:
        return str(int(v)) if abs(v-int(v))<1e-12 else f"{v:.12g}"

def main():
    app = QApplication(sys.argv)
    w = Calc(); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
