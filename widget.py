"""Floating macOS desktop widget that shows financial totals from a Google Sheet.

Run with: python3 widget.py
Config: ~/.config/finance-widget/config.json (see config.example.json)
"""
import datetime
import json
import os
import sys
import threading
import tkinter as tk
import urllib.error
import urllib.parse
import urllib.request

CONFIG_PATH = os.path.expanduser("~/.config/finance-widget/config.json")

# (display name, A1 range). Order here is the display order.
METRICS = [
    ("Net Worth",   "Current!C42"),
    ("Liquid",      "Current!C46"),
    ("Cash",        "Current!C2"),
    ("Stocks",      "Current!C12"),
    ("Retirement",  "Current!C21"),
    ("Liabilities", "Current!C38"),
]

REFRESH_INTERVAL_MS = 15 * 60 * 1000  # 15 minutes

BG        = "#1a1a1a"
FG_DIM    = "#888888"
FG_MED    = "#bbbbbb"
FG_BRIGHT = "#ffffff"
RED       = "#f87171"


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def fetch_values(spreadsheet_id, api_key, ranges):
    qs = "&".join("ranges=" + urllib.parse.quote(r) for r in ranges)
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
        f"/values:batchGet?{qs}&valueRenderOption=UNFORMATTED_VALUE"
        f"&key={urllib.parse.quote(api_key)}"
    )
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.load(resp)
    out = {}
    for r, vr in zip(ranges, data.get("valueRanges", [])):
        vals = vr.get("values") or [[None]]
        out[r] = vals[0][0] if vals[0] else None
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
            ranges = [r for _, r in METRICS]
            raw = fetch_values(
                self.config["spreadsheet_id"],
                self.config["api_key"],
                ranges,
            )
            current = {name: raw.get(rng) for name, rng in METRICS}
            self.root.after(0, self._update_ui, current, None)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:120]
            self.root.after(0, self._update_ui, None, f"HTTP {e.code}: {body}")
        except Exception as e:
            self.root.after(0, self._update_ui, None, repr(e))

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
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        example = {
            "spreadsheet_id": "1cCVjiY2gSYFmnW0xymERCRXtpHd3J8E1G-1SfMT5iLc",
            "api_key": "PASTE_YOUR_GOOGLE_API_KEY_HERE",
        }
        sys.stderr.write(
            f"No config found at {CONFIG_PATH}\n\n"
            "Create it with contents like:\n"
            f"{json.dumps(example, indent=2)}\n\n"
            "See README.md for how to get a Google API key.\n"
        )
        sys.exit(1)
    Widget(load_config()).run()


if __name__ == "__main__":
    main()
