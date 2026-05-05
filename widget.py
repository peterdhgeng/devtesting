"""Floating macOS desktop widget that shows financial totals from a Google Sheet.

Run with: python3 widget.py
Config: ~/.config/finance-widget/config.json (see config.example.json)
"""
import csv
import datetime
import io
import json
import os
import sys
import threading
import tkinter as tk
import urllib.error
import urllib.parse
import urllib.request

# Default sheet to read. Override with $FINANCE_SHEET_ID or by editing this.
DEFAULT_SPREADSHEET_ID = "1cCVjiY2gSYFmnW0xymERCRXtpHd3J8E1G-1SfMT5iLc"
CONFIG_PATH = os.path.expanduser("~/.config/finance-widget/config.json")

GID = 1419170754  # numeric id of the Current tab. Override with $FINANCE_GID.
COL_INDEX = 2  # column C, 0-indexed

# (display name, 1-indexed row number on the Current tab)
METRICS = [
    ("Net Worth",   42),
    ("Liquid",      46),
    ("Cash",         2),
    ("Stocks",      12),
    ("Retirement",  21),
    ("Liabilities", 38),
]

REFRESH_INTERVAL_MS = 15 * 60 * 1000  # 15 minutes

BG        = "#1a1a1a"
FG_DIM    = "#888888"
FG_MED    = "#bbbbbb"
FG_BRIGHT = "#ffffff"
RED       = "#f87171"


def load_config():
    """Resolve sheet ID and gid from env, config file, or hardcoded defaults."""
    cfg = {"spreadsheet_id": DEFAULT_SPREADSHEET_ID, "gid": GID}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            cfg.update(json.load(f))
    if os.environ.get("FINANCE_SHEET_ID"):
        cfg["spreadsheet_id"] = os.environ["FINANCE_SHEET_ID"]
    if os.environ.get("FINANCE_GID"):
        cfg["gid"] = int(os.environ["FINANCE_GID"])
    return cfg


def fetch_sheet_csv(spreadsheet_id, gid):
    """Fetch a tab from a link-viewable Google Sheet as CSV. No auth needed.

    Uses /export?format=csv (the same endpoint as File → Download → CSV),
    which preserves empty rows exactly. The gviz/tq endpoint silently drops
    them, throwing off row indexing — don't use it.
    """
    url = (
        f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        f"/export?format=csv&gid={gid}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "finance-widget/1"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    if body.lstrip().lower().startswith(("<!doctype", "<html")):
        raise RuntimeError(
            "sheet not public — set sharing to 'Anyone with the link → Viewer'"
        )
    return list(csv.reader(io.StringIO(body)))


def parse_money(s):
    """Best-effort: turn '$1,234.56', '(500)', '-$500', '1234' into a float."""
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    s = s.replace(",", "").replace("$", "").replace(" ", "").replace("\xa0", "")
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        return float(s)
    except ValueError:
        return None


def fetch_values(spreadsheet_id, gid):
    rows = fetch_sheet_csv(spreadsheet_id, gid)
    out = {}
    for name, row_num in METRICS:
        idx = row_num - 1
        if idx < len(rows) and COL_INDEX < len(rows[idx]):
            out[name] = parse_money(rows[idx][COL_INDEX])
        else:
            out[name] = None
    return out


def fmt_money(v):
    if v is None:
        return "—"
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    sign = "-" if f < 0 else ""
    return f"{sign}${abs(f):,.0f}"


class Widget:
    def __init__(self, config):
        self.config = config
        self.root = tk.Tk()
        self.root.title("Finance Widget")
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", True)
        try:
            self.root.attributes("-alpha", 0.93)
        except tk.TclError:
            pass
        try:
            self.root.overrideredirect(True)
        except tk.TclError:
            pass

        self._drag_offset = (0, 0)
        self.root.bind("<ButtonPress-1>", self._start_drag)
        self.root.bind("<B1-Motion>", self._drag_move)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("<Command-q>", lambda e: self.root.destroy())
        self.root.bind("<Command-r>", lambda e: self._refresh())

        self._build_ui()

        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        w = self.root.winfo_width()
        self.root.geometry(f"+{sw - w - 24}+48")

        self._refresh()
        self._schedule_next_refresh()

    def _start_drag(self, e):
        self._drag_offset = (
            e.x_root - self.root.winfo_x(),
            e.y_root - self.root.winfo_y(),
        )

    def _drag_move(self, e):
        x = e.x_root - self._drag_offset[0]
        y = e.y_root - self._drag_offset[1]
        self.root.geometry(f"+{x}+{y}")

    def _build_ui(self):
        outer = tk.Frame(self.root, bg=BG, padx=18, pady=14)
        outer.pack()

        header = tk.Frame(outer, bg=BG)
        header.pack(fill="x", pady=(0, 6))
        tk.Label(header, text="Finances", bg=BG, fg=FG_MED,
                 font=("Helvetica", 11)).pack(side="left")
        tk.Button(header, text="✕", bg=BG, fg=FG_DIM, bd=0,
                  activebackground=BG, activeforeground=FG_BRIGHT,
                  highlightthickness=0, padx=4,
                  command=self.root.destroy).pack(side="right")
        tk.Button(header, text="⟳", bg=BG, fg=FG_DIM, bd=0,
                  activebackground=BG, activeforeground=FG_BRIGHT,
                  highlightthickness=0, padx=4,
                  command=self._refresh).pack(side="right")

        self.nw_value = tk.Label(outer, text="—", bg=BG, fg=FG_BRIGHT,
                                 font=("Helvetica", 26, "bold"))
        self.nw_value.pack(anchor="w")
        tk.Label(outer, text="Net Worth", bg=BG, fg=FG_DIM,
                 font=("Helvetica", 9)).pack(anchor="w", pady=(0, 12))

        self.row_widgets = {}
        for name, _ in METRICS:
            if name == "Net Worth":
                continue
            row = tk.Frame(outer, bg=BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=name, bg=BG, fg=FG_MED,
                     font=("Helvetica", 11), width=12, anchor="w"
                     ).pack(side="left")
            value_lbl = tk.Label(row, text="—", bg=BG, fg=FG_BRIGHT,
                                 font=("Helvetica", 12, "bold"),
                                 anchor="e")
            value_lbl.pack(side="right")
            self.row_widgets[name] = value_lbl

        self.status = tk.Label(outer, text="", bg=BG, fg=FG_DIM,
                               font=("Helvetica", 8))
        self.status.pack(anchor="w", pady=(10, 0))

    def _refresh(self):
        self.status.config(text="loading…", fg=FG_DIM)
        threading.Thread(target=self._do_refresh, daemon=True).start()

    def _do_refresh(self):
        try:
            current = fetch_values(
                self.config["spreadsheet_id"],
                self.config.get("gid", GID),
            )
            self.root.after(0, self._update_ui, current, None)
        except urllib.error.HTTPError as e:
            self.root.after(0, self._update_ui, None, f"HTTP {e.code}")
        except Exception as e:
            self.root.after(0, self._update_ui, None, str(e))

    def _update_ui(self, current, error):
        if error:
            self.status.config(text=error[:80], fg=RED)
            return
        self.nw_value.config(text=fmt_money(current.get("Net Worth")))
        for name, _ in METRICS:
            if name == "Net Worth":
                continue
            self.row_widgets[name].config(text=fmt_money(current.get(name)))
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.status.config(text=f"updated {ts}", fg=FG_DIM)

    def _schedule_next_refresh(self):
        self.root.after(REFRESH_INTERVAL_MS, self._tick)

    def _tick(self):
        self._refresh()
        self._schedule_next_refresh()

    def run(self):
        self.root.mainloop()


def main():
    Widget(load_config()).run()


if __name__ == "__main__":
    main()
