"""
HKD <-> USD Currency Converter  (Tkinter 桌面小程序)

实时汇率来源: open.er-api.com (免费、无需 API Key)
如果网络不可用, 自动回退到固定汇率 1 USD = 7.80 HKD, 并在界面上提示。

运行方式:
    python converter.py
"""

import json
import tkinter as tk
from tkinter import messagebox, ttk
from urllib.error import URLError
from urllib.request import urlopen

API_URL = "https://open.er-api.com/v6/latest/USD"  # 实时汇率接口
FALLBACK_RATE = 7.8                                # 1 USD = ? HKD 的兜底汇率
CURRENCIES = ("USD", "HKD")


def fetch_rate():
    """获取 1 USD 等于多少 HKD。

    返回 (rate, updated_utc):
        rate         : float, 当前汇率
        updated_utc  : 汇率更新时间字符串; 获取失败时返回空字符串, 表示使用兜底汇率
    """
    try:
        with urlopen(API_URL, timeout=8) as resp:
            payload = json.load(resp)
        if payload.get("result") != "success":
            raise ValueError(payload)
        rate = float(payload["rates"]["HKD"])
        updated = payload.get("time_last_update_utc", "")
        return rate, updated
    except (URLError, OSError, ValueError, KeyError):
        return FALLBACK_RATE, ""


class ConverterApp:
    """主窗口类"""

    def __init__(self, root):
        self.root = root
        self.hkd_per_usd = None   # 1 USD = ? HKD
        self.rate_updated = ""    # 汇率更新时间 (为空表示离线兜底)
        self.live = False         # 当前是否为实时汇率

        root.title("HKD \u21c4 USD Currency Converter")
        root.resizable(False, False)

        container = ttk.Frame(root, padding=28)
        container.pack(fill="both", expand=True)

        # 标题
        title = tk.Label(container, text="HKD \u21c4 USD Converter",
                         font=("Segoe UI", 20, "bold"), fg="#0b57d0")
        title.pack(pady=(0, 8))

        # 金额输入
        amount_box = ttk.Frame(container)
        amount_box.pack(fill="x", pady=(14, 2))
        ttk.Label(amount_box, text="Amount").pack(anchor="w")
        self.amount_var = tk.StringVar(value="100")
        self.amount_entry = ttk.Entry(amount_box, textvariable=self.amount_var,
                                      font=("Segoe UI", 14), justify="right")
        self.amount_entry.pack(fill="x", pady=(4, 0))
        # 输入内容一变化就立即换算
        self.amount_var.trace_add("write", lambda *_: self.convert())

        # 从 / 到 币种选择
        picker = ttk.Frame(container)
        picker.pack(fill="x", pady=(8, 0))
        picker.columnconfigure(0, weight=1)
        picker.columnconfigure(2, weight=1)

        from_box = ttk.Frame(picker)
        from_box.grid(row=0, column=0, sticky="we")
        ttk.Label(from_box, text="From").pack(anchor="w")
        self.from_var = tk.StringVar(value="USD")
        from_combo = ttk.Combobox(from_box, textvariable=self.from_var,
                                  values=CURRENCIES, state="readonly", width=8)
        from_combo.pack(fill="x", pady=(4, 0))
        from_combo.bind("<<ComboboxSelected>>", lambda e: self.convert())

        ttk.Button(picker, text="\u21c4", width=3,
                   command=self.swap).grid(row=0, column=1, padx=10, pady=(16, 0))

        to_box = ttk.Frame(picker)
        to_box.grid(row=0, column=2, sticky="we")
        ttk.Label(to_box, text="To").pack(anchor="w")
        self.to_var = tk.StringVar(value="HKD")
        to_combo = ttk.Combobox(to_box, textvariable=self.to_var,
                                values=CURRENCIES, state="readonly", width=8)
        to_combo.pack(fill="x", pady=(4, 0))
        to_combo.bind("<<ComboboxSelected>>", lambda e: self.convert())

        # 结果显示 (输入/选择时实时更新, 无需按钮)
        self.result_label = tk.Label(container, text="\u2014", font=("Segoe UI", 16, "bold"),
                                     fg="#0b57d0", pady=(18, 8))
        self.result_label.pack(fill="x")

        # 汇率信息 + 刷新
        self.rate_label = tk.Label(container, text="Loading live rate\u2026",
                                   font=("Segoe UI", 9), fg="#5f6b7a", justify="center")
        self.rate_label.pack(fill="x")
        refresh_btn = tk.Button(container, text="\u21bb Refresh rate", command=self.refresh_rate,
                                bg="#eef3fb", fg="#0b57d0", font=("Segoe UI", 9),
                                activebackground="#dbe7f7", relief="flat", cursor="hand2")
        refresh_btn.pack(pady=(6, 0))

        # 启动时自动获取一次实时汇率
        self.amount_entry.focus_set()
        self.refresh_rate()

    # ---------- 核心逻辑 ----------

    def refresh_rate(self, show_errors=True):
        """联网获取汇率并更新界面。"""
        self.root.config(cursor="watch")
        self.root.update()
        try:
            rate, updated = fetch_rate()
            self.hkd_per_usd = rate
            self.rate_updated = updated
            self.live = bool(updated)
        finally:
            self.root.config(cursor="")

        if self.live:
            text = ("1 USD = {:.4f} HKD\n"
                    "1 HKD = {:.4f} USD\n"
                    "Updated: {}".format(self.hkd_per_usd,
                                         1 / self.hkd_per_usd,
                                         self.rate_updated))
        else:
            text = ("Offline \u2014 using fixed rate 1 USD = {:.2f} HKD\n"
                    "1 HKD \u2248 {:.4f} USD".format(self.hkd_per_usd,
                                                     1 / self.hkd_per_usd))
            if show_errors:
                messagebox.showwarning(
                    "No connection",
                    "Could not fetch the live rate from the API.\n"
                    "A fixed rate of 1 USD = {:.2f} HKD is used instead.".format(self.hkd_per_usd))
        self.rate_label.config(text=text)
        self.convert()

    def swap(self):
        """互换 From / To, 并立即换算。"""
        f, t = self.from_var.get(), self.to_var.get()
        self.from_var.set(t)
        self.to_var.set(f)
        self.convert()

    def convert(self):
        """按当前输入的金额与币种即时换算 (输入变化即触发, 无需按钮)。"""
        raw = self.amount_var.get().strip()
        try:
            amount = float(raw)
        except ValueError:
            # 输入为空/非法 (如只有小数点) 时保持结果空白
            self.result_label.config(text="")
            return

        if self.hkd_per_usd is None:
            # 汇率尚未获取到, 保持提示状态
            self.result_label.config(text="Loading rate\u2026")
            return

        from_ccy, to_ccy = self.from_var.get(), self.to_var.get()
        rate = self.hkd_per_usd or FALLBACK_RATE
        if from_ccy == to_ccy:
            result = amount
        elif from_ccy == "USD" and to_ccy == "HKD":
            result = amount * rate
        else:  # HKD -> USD
            result = amount / rate

        self.result_label.config(
            text="{:.2f} {} = {:.2f} {}".format(amount, from_ccy, result, to_ccy))


if __name__ == "__main__":
    window = tk.Tk()
    ConverterApp(window)
    window.mainloop()
