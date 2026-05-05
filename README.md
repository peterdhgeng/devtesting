# devtesting

repo for testing out things

## Finance widget (`widget.py`)

A floating, always-on-top macOS desktop widget that pulls values from a Google
Sheet and shows total net worth, liquid net worth, cash, stocks, retirement,
and liabilities.

### Cells it reads

From the `Current` tab of the spreadsheet:

| Metric        | Cell |
| ------------- | ---- |
| Net Worth     | C42  |
| Liquid        | C46  |
| Cash          | C2   |
| Stocks        | C12  |
| Retirement    | C21  |
| Liabilities   | C38  |

### Setup

**1. Share the sheet via link.** In Google Sheets:
*Share → General access → Anyone with the link → Viewer.* The sheet stays
unlisted, but anyone who knows the URL can read it. No API key, no Google
Cloud project.

**2. Run it.**

```sh
git clone <this repo> && cd devtesting
./run.sh
```

That's it. The sheet ID is already baked in (`DEFAULT_SPREADSHEET_ID` at the
top of `widget.py`); edit that constant or set `FINANCE_SHEET_ID=...` if you
ever want to point at a different sheet.

If `./run.sh` errors with *"No module named tkinter"* you're on Homebrew
Python — fix with `brew install python-tk`. The python.org installer and
Anaconda both ship Tkinter built-in.

The widget appears in the top-right corner. Drag it anywhere with your mouse.
Press `⌘Q` or `Esc` to close, `⌘R` to force-refresh. It auto-refreshes every
15 minutes.

### Launch on login

Easiest way: *System Settings → General → Login Items → +* → pick `run.sh`
(or wrap it in an Automator "Application" if macOS won't accept the .sh).
