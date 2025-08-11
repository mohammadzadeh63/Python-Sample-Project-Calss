#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ماشین‌حساب گرافیکی ساده و قابل فهم با PyQt6
# ویژگی‌ها: چهار عمل اصلی، پرانتز، درصد، توان (^)، جذر (√)، تاریخچه، مموری (MC/MR/M+/M−)
# تمرکز روی سادگی کد و خوانایی – بدون eventFilter و استایل‌های پیچیده

import sys, math, re
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QLineEdit, QLabel, QPushButton, QListWidget, QHBoxLayout, QMessageBox, QDockWidget
)

# ----------------------- ارزیابی امن عبارت -----------------------
# فقط توابع و ثابت‌های مجاز را معرفی می‌کنیم
ALLOWED_FUNCS = {
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "log": math.log10, "ln": math.log, "abs": abs, "round": round,
    "floor": math.floor, "ceil": math.ceil,
    "pi": math.pi, "e": math.e
}
# الگوی کاراکترهای مجاز
ALLOWED_PATTERN = re.compile(r"^[0-9\s\+\-\*/\.\%\^\(\)\,a-zA-Z]+$")

def normalize(expr: str) -> str:
    """تبدیل ورودی کاربر به چیزی که eval بفهمد"""
    return (expr.replace("√", "sqrt")
                .replace("^", "**"))

def safe_eval(expr: str) -> float:
    """ارزیابی امن و ساده با محدود کردن فضای اجرا"""
    expr = normalize((expr or "").strip())
    if not expr:
        return 0.0
    if "__" in expr or not ALLOWED_PATTERN.match(expr):
        raise ValueError("عبارت نامعتبر/غیرامن")
    return eval(expr, {"__builtins__": {}}, ALLOWED_FUNCS.copy())

# ----------------------- پنجره اصلی -----------------------
class Calc(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SimpleCalc • PyQt6")
        self.resize(420, 600)

        # مموری و تاریخچه
        self.memory = 0.0
        self.history: list[tuple[str, float]] = []

        self._build_ui()
        self._apply_style()

    # --- ساخت رابط ---
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(16, 16, 16, 16)
        main.setSpacing(10)

        # نمایشگر کوچک (عبارت قبلی)
        self.sub = QLabel("")
        self.sub.setAlignment(Qt.AlignmentFlag.AlignRight)
        main.addWidget(self.sub)

        # نمایشگر اصلی
        self.display = QLineEdit()
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setPlaceholderText("0")
        self.display.returnPressed.connect(self.evaluate)  # Enter = مساوی
        main.addWidget(self.display)

        # گرید دکمه‌ها
        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)
        main.addLayout(grid)

        # تعریف دکمه‌ها (متن، کال‌بک)
        rows = [
            [("MC", self.mem_clear), ("MR", self.mem_recall),
             ("M+", self.mem_add),  ("M-", self.mem_sub),
             ("C",  self.clear_all), ("⌫", self.backspace)],

            [("(",  lambda: self.type_text("(")),  (")",  lambda: self.type_text(")")),
             ("%",  lambda: self.type_text("%")),  ("/",  lambda: self.type_text("/")),
             ("√",  lambda: self.type_text("√(")), ("Hist", self.toggle_history)],

            [("7", lambda: self.type_text("7")), ("8", lambda: self.type_text("8")),
             ("9", lambda: self.type_text("9")), ("*", lambda: self.type_text("*")),
             ("1/x", self.reciprocal),            ("^", lambda: self.type_text("^"))],

            [("4", lambda: self.type_text("4")), ("5", lambda: self.type_text("5")),
             ("6", lambda: self.type_text("6")), ("-", lambda: self.type_text("-")),
             ("sin", lambda: self.type_text("sin(")), ("cos", lambda: self.type_text("cos("))],

            [("1", lambda: self.type_text("1")), ("2", lambda: self.type_text("2")),
             ("3", lambda: self.type_text("3")), ("+", lambda: self.type_text("+")),
             ("tan", lambda: self.type_text("tan(")), ("ln", lambda: self.type_text("ln("))],

            [("±", self.toggle_sign), ("0", lambda: self.type_text("0")),
             (".", lambda: self.type_text(".")), ("=", self.evaluate),
             ("log", lambda: self.type_text("log(")), ("π", lambda: self.type_text("pi"))],
        ]

        # ساخت و جایگذاری دکمه‌ها
        for r, row in enumerate(rows):
            for c, (text, cb) in enumerate(row):
                b = QPushButton(text)
                b.clicked.connect(cb)
                grid.addWidget(b, r, c)

        # نوار راهنما و مموری
        foot = QHBoxLayout()
        self.mem_label = QLabel("")     # نمایش مقدار مموری (اگر غیرصفر باشد)
        tip = QLabel("M • ^ توان • √ جذر • Esc=پاک • Enter = مساوی")
        foot.addWidget(self.mem_label)
        foot.addStretch(1)
        foot.addWidget(tip)
        main.addLayout(foot)

        # داک تاریخچه (قابل باز/بسته‌شدن)
        self.dock = QDockWidget("History", self)
        self.dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        self.hist_list = QListWidget()
        self.hist_list.itemDoubleClicked.connect(self._use_selected_history)
        self.dock.setWidget(self.hist_list)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)
        self.dock.hide()

        # کلیدهای ضروری
        self.shortcut_keys()

    # --- میانبرها ---
    def shortcut_keys(self):
        # Esc = پاک‌کردن (با overrideKeyPress ساده‌تره)
        self.display.keyPressEvent = self._wrap_keypress(self.display.keyPressEvent)

    def _wrap_keypress(self, orig_handler):
        def handler(ev):
            if ev.key() == Qt.Key.Key_Escape:
                self.clear_all()
                return
            elif ev.key() == Qt.Key.Key_Backspace:
                # اجازه بده بک‌اسپیس پیش‌فرض هم کار کنه
                return orig_handler(ev)
            else:
                return orig_handler(ev)
        return handler

    # ----------------------- منطق دکمه‌ها -----------------------
    def type_text(self, s: str):
        self.display.insert(s)

    def clear_all(self):
        self.display.clear()
        self.sub.setText("")

    def backspace(self):
        t = self.display.text()
        if t:
            self.display.setText(t[:-1])

    def toggle_sign(self):
        """علامت آخرین عدد را عوض می‌کند"""
        cur = self.display.text().rstrip()
        if not cur:
            return
        m = re.search(r"(-?\d+(\.\d+)?)\s*$", cur)
        if m:
            start, end = m.span(1)
            num = m.group(1)
            rep = num[1:] if num.startswith("-") else "-" + num
            self.display.setText(cur[:start] + rep + cur[end:])
        else:
            self.display.setText(f"-({cur})")

    def reciprocal(self):
        """محاسبه 1/x روی کل عبارت فعلی"""
        cur = (self.display.text() or "0").strip()
        self.sub.setText(f"1/({cur})")
        try:
            val = safe_eval(f"1/({cur})")
            self.display.setText(self._fmt(val))
            self._push_history(f"1/({cur})", val)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"عملیات نامعتبر:\n{e}")

    # ----------------------- مموری -----------------------
    def mem_clear(self):
        self.memory = 0.0
        self._update_mem_label()

    def mem_recall(self):
        self.type_text(self._num(self.memory))

    def mem_add(self):
        try:
            v = safe_eval(self.display.text() or "0")
            self.memory += v
            self._update_mem_label()
        except Exception:
            pass

    def mem_sub(self):
        try:
            v = safe_eval(self.display.text() or "0")
            self.memory -= v
            self._update_mem_label()
        except Exception:
            pass

    def _update_mem_label(self):
        self.mem_label.setText(f"M: {self._num(self.memory)}" if abs(self.memory) > 1e-15 else "")

    # ----------------------- تاریخچه -----------------------
    def toggle_history(self):
        self.dock.setVisible(not self.dock.isVisible())

    def _push_history(self, expr: str, result: float):
        self.history.append((expr, result))
        self._refresh_history()

    def _refresh_history(self):
        self.hist_list.clear()
        for expr, res in reversed(self.history[-300:]):
            self.hist_list.addItem(f"{expr} = {self._num(res)}")

    def _use_selected_history(self):
        item = self.hist_list.currentItem()
        if not item:
            return
        text = item.text()
        if "=" in text:
            _, val = text.split("=", 1)
            self.display.setText(val.strip())

    # ----------------------- ارزیابی -----------------------
    def evaluate(self):
        expr = self.display.text().strip()
        if not expr:
            return
        self.sub.setText(expr)
        try:
            val = safe_eval(expr)
            self.display.setText(self._fmt(val))
            self._push_history(expr, val)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"عبارت نامعتبر:\n{e}")

    # ----------------------- کمکی‌ها -----------------------
    def _fmt(self, v: float) -> str:
        """نمایش مناسب عدد (حذف اعشار اضافی)"""
        if abs(v - int(v)) < 1e-12:
            return str(int(round(v)))
        return f"{v:.12g}"

    def _num(self, v: float) -> str:
        return f"{v:.12g}"

    # ----------------------- استایل خیلی ساده (اختیاری) -----------------------
    def _apply_style(self):
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

# ----------------------- main -----------------------
def main():
    app = QApplication(sys.argv)
    w = Calc()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
