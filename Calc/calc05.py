# step5_history.py
import sys, math, re
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QGridLayout, QLineEdit, QLabel, QPushButton, QMessageBox,
                             QDockWidget, QListWidget)

ALLOWED_FUNCS = {"sqrt": math.sqrt, "abs": abs, "round": round}
ALLOWED_PATTERN = re.compile(r"^[0-9\s\+\-\*/\.\%\^\(\)a-zA-Z]+$")

def normalize(expr: str) -> str:
    return (expr.replace("√", "sqrt").replace("^", "**"))

def safe_eval(expr: str) -> float:
    expr = normalize((expr or "").strip())
    if not expr: return 0.0
    if "__" in expr or not ALLOWED_PATTERN.match(expr):
        raise ValueError("Invalid/unsafe")
    expr = re.sub(r"(\d+(\.\d+)?)\%", r"(\1/100)", expr)
    return eval(expr, {"__builtins__": {}}, ALLOWED_FUNCS.copy())

class Calc(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calc • Step 5 (History)")
        self.resize(520, 560)
        self.history = []

        root = QWidget(); self.setCentralWidget(root)
        main = QVBoxLayout(root)

        self.sub = QLabel(""); self.sub.setAlignment(Qt.AlignmentFlag.AlignRight)
        main.addWidget(self.sub)

        self.display = QLineEdit(); self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setPlaceholderText("0")
        self.display.returnPressed.connect(self.evaluate)
        main.addWidget(self.display)

        grid = QGridLayout(); main.addLayout(grid)
        keys = [
            "7","8","9","/","4","5","6","*",
            "1","2","3","-","0",".","(",")",
            "^","√","%","+"
        ]
        r=c=0
        for k in keys:
            b = QPushButton(k); b.clicked.connect(lambda _,x=k:self.type_text(x))
            grid.addWidget(b, r, c); c+=1
            if c==4: c=0; r+=1

        eq = QPushButton("="); eq.clicked.connect(self.evaluate)
        clr = QPushButton("C"); clr.clicked.connect(self.clear_all)
        hist = QPushButton("Hist"); hist.clicked.connect(self.toggle_history)
        grid.addWidget(clr,  r, 0, 1, 2)
        grid.addWidget(eq,   r, 2, 1, 1)
        grid.addWidget(hist, r, 3, 1, 1)

        # داک تاریخچه
        self.dock = QDockWidget("History", self)
        self.hist_list = QListWidget()
        self.hist_list.itemDoubleClicked.connect(self.use_selected)
        self.dock.setWidget(self.hist_list)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)
        self.dock.hide()

    def type_text(self, s: str): self.display.insert(s)
    def clear_all(self): self.display.clear(); self.sub.setText("")
    def toggle_history(self): self.dock.setVisible(not self.dock.isVisible())

    def evaluate(self):
        expr = self.display.text().strip()
        if not expr: return
        self.sub.setText(expr)
        try:
            val = safe_eval(expr)
            self.display.setText(self._fmt(val))
            self.push_history(expr, val)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"عبارت نامعتبر:\n{e}")

    def push_history(self, expr, val):
        self.history.append((expr, val))
        self.hist_list.clear()
        for e, v in reversed(self.history[-300:]):
            self.hist_list.addItem(f"{e} = {self._num(v)}")

    def use_selected(self):
        item = self.hist_list.currentItem()
        if not item: return
        _, val = item.text().split("=", 1)
        self.display.setText(val.strip())

    def _fmt(self, v: float) -> str:
        return str(int(v)) if abs(v-int(v))<1e-12 else f"{v:.12g}"

    def _num(self, v: float) -> str:
        return f"{v:.12g}"

def main():
    app = QApplication(sys.argv)
    w = Calc(); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
