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

### One-time setup

**1. Share the sheet via link**

In Google Sheets: *Share → General access → Anyone with the link → Viewer*.
The sheet stays unlisted, but anyone who happens to know the URL can read
it. No API key, no Google Cloud project — the widget reads the public CSV
export endpoint that Sheets exposes for link-shared documents.

**2. Drop the spreadsheet ID into a config file**

```sh
mkdir -p ~/.config/finance-widget
cp config.example.json ~/.config/finance-widget/config.json
```

The default already points at the right sheet ID. If you ever swap to a
different sheet, copy the long ID from its URL
(`docs.google.com/spreadsheets/d/<THIS_PART>/edit`) into the config.

**3. Make sure Tkinter is installed**

Tkinter ships with the python.org installer and Anaconda. If you're on
Homebrew Python and `python3 -m tkinter` errors, install it:

```sh
brew install python-tk
```

### Run it

```sh
./run.sh
# or
python3 widget.py
```

The widget appears in the top-right corner. Drag it anywhere with your mouse.
Press `⌘Q` or `Esc` to close, `⌘R` to force-refresh. It auto-refreshes every
15 minutes.

### Launch on login

Easiest way: *System Settings → General → Login Items → +* → pick `run.sh`
(or wrap it in an Automator "Application" if macOS won't accept the .sh).
