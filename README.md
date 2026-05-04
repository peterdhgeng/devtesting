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

**1. Make the sheet readable with an API key**

In Google Sheets: *Share → General access → Anyone with the link → Viewer*.
(Sheet stays unlisted, but anyone who happens to know the URL can read it.)

**2. Get a free Google API key**

1. Go to <https://console.cloud.google.com>.
2. Create a project (any name).
3. *APIs & Services → Library →* search **Google Sheets API** → Enable.
4. *APIs & Services → Credentials → + Create credentials → API key.*
5. Copy the key. (Optional but recommended: click *Restrict key* → API
   restrictions → Google Sheets API only.)

**3. Drop the key into a config file**

```sh
mkdir -p ~/.config/finance-widget
cp config.example.json ~/.config/finance-widget/config.json
# then edit ~/.config/finance-widget/config.json and paste your API key
```

**4. Make sure Tkinter is installed**

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
