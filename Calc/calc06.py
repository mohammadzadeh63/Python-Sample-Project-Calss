# step6_memory_style.py
import sys, math, re
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QGridLayout, QLineEdit, QLabel, QPushButton, QMessageBox,
                             QDockWidget, QListWidget, QHBoxLayout)

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
        self.setWindowTitle("Calc • Step 6 (Memory + Style)")
        self.resize(540, 600)
        self.history = []
        self.memory = 0.0

        root = QWidget(); self.setCentralWidget(root)
        main = QVBoxLayout(root); main.setContentsMargins(16,16,16,16)

        self.sub = QLabel(""); self.sub.setAlignment(Qt.AlignmentFlag.AlignRight)
        main.addWidget(self.sub)

        self.display = QLineEdit(); self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setPlaceholderText("0"); self.display.returnPressed.connect(self.evaluate)
        main.addWidget(self.display)

        grid = QGridLayout(); main.addLayout(grid)
        top = [
            ("MC", self.mem_clear), ("MR", self.mem_recall), ("M+", self.mem_add),
            ("M-", self.mem_sub),   ("C", self.clear_all),   ("⌫", self.backspace)
        ]
        nums_ops = [
            "7","8","9","/","4","5","6","*","1","2","3","-","0",".","(",")","^","√","%","+"
        ]

        # ردیف اول (مموری و پاک)
        for i, (t, cb) in enumerate(top):
            b = QPushButton(t); b.clicked.connect(cb); grid.addWidget(b, 0, i)

        # بقیه‌ی کلیدها
        r, c = 1, 0
        for k in nums_ops:
            b = QPushButton(k); b.clicked.connect(lambda _,x=k:self.type_text(x))
            grid.addWidget(b, r, c); c += 1
            if c == 4: c = 0; r += 1

        eq = QPushButton("="); eq.clicked.connect(self.evaluate)
        hist = QPushButton("Hist"); hist.clicked.connect(self.toggle_history)
        grid.addWidget(hist, r, 0, 1, 2)
        grid.addWidget(eq,   r, 2, 1, 2)

        # Footer: نشانگر مموری
        foot = QHBoxLayout()
        self.mem_label = QLabel("")
        tip = QLabel("M • ^ توان • √ جذر • Enter = مساوی • Esc = پاک")
        foot.addWidget(self.mem_label); foot.addStretch(1); foot.addWidget(tip)
        main.addLayout(foot)

        # تاریخچه
        self.dock = QDockWidget("History", self)
        self.hist_list = QListWidget(); self.hist_list.itemDoubleClicked.connect(self.use_selected)
        self.dock.setWidget(self.hist_list); self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)
        self.dock.hide()

        # استایل خیلی سبک
        self.setStyleSheet("""
            QMainWindow { background: #0f1117; }
            QWidget { color: #e6ecff; font-size: 15px; }
            QLineEdit {
                background: #141a24; border: 1px solid #202635; border-radius: 10px;
                padding: 10px; font-size: 24px;
            }
            QLabel { color: #96a1b5; }
            QPushButton {
                background: #1b2332; border: 1px solid #202635; color: #e6ecff;
                border-radius: 10px; padding: 10px; font-size: 15px;
            }
            QPushButton:hover { background: #243044; }
            QPushButton:pressed { background: #2b3a52; }
            QListWidget {
                background: #111827; border: 1px solid #202635; border-radius: 8px;
            }
        """)

        # Esc = پاک‌کردن (ساده)
        self.display.keyPressEvent = self._wrap_keypress(self.display.keyPressEvent)

    # ورودی و پایه
    def type_text(self, s: str): self.display.insert(s)
    def clear_all(self): self.display.clear(); self.sub.setText("")
    def backspace(self):
        t = self.display.text()
        if t: self.display.setText(t[:-1])

    # مموری
    def mem_clear(self): self.memory = 0.0; self._update_mem()
    def mem_recall(self): self.type_text(self._num(self.memory))
    def mem_add(self):
        try: self.memory += safe_eval(self.display.text() or "0"); self._update_mem()
        except: pass
    def mem_sub(self):
        try: self.memory -= safe_eval(self.display.text() or "0"); self._update_mem()
        except: pass
    def _update_mem(self):
        self.mem_label.setText(f"M: {self._num(self.memory)}" if abs(self.memory)>1e-15 else "")

    # تاریخچه
    def toggle_history(self): self.dock.setVisible(not self.dock.isVisible())
    def push_history(self, expr, val):
        self.history.append((expr, val))
        self.hist_list.clear()
        for e, v in reversed(self.history[-300:]):
            self.hist_list.addItem(f"{e} = {self._num(v)}")
    def use_selected(self):
        it = self.hist_list.currentItem()
        if not it: return
        _, v = it.text().split("=", 1)
        self.display.setText(v.strip())

    # محاسبه
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

    # کمکی‌ها
    def _fmt(self, v: float) -> str:
        return str(int(v)) if abs(v-int(v))<1e-12 else f"{v:.12g}"
    def _num(self, v: float) -> str:
        return f"{v:.12g}"

    def _wrap_keypress(self, orig):
        def handler(ev):
            if ev.key() == Qt.Key.Key_Escape:
                self.clear_all(); return
            return orig(ev)
        return handler

def main():
    app = QApplication(sys.argv)
    w = Calc(); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
