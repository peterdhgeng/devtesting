#!/usr/bin/env bash
# Launch the finance widget. Finds a Python with a working tkinter — by
# actually creating a Tk root (a bare `import tkinter` doesn't trigger the
# system Tcl/Tk frameworks to load, so it can't catch macOS-SDK mismatches
# like the one that ships in Apple's /usr/bin/python3 on older macOS).
set -e
cd "$(dirname "$0")"

CACHE_FILE=".python-bin"

PROBE='
import sys
try:
    import tkinter
    r = tkinter.Tk()
    r.withdraw()
    r.destroy()
except Exception:
    sys.exit(1)
'

probe() { "$1" -c "$PROBE" >/dev/null 2>&1; }

# Reuse the last working interpreter if still good.
if [ -f "$CACHE_FILE" ]; then
    cached=$(cat "$CACHE_FILE")
    if [ -n "$cached" ] && [ -x "$cached" ] && probe "$cached"; then
        exec "$cached" widget.py
    fi
    rm -f "$CACHE_FILE"
fi

candidates=(
    /opt/homebrew/bin/python3.13
    /opt/homebrew/bin/python3.12
    /opt/homebrew/bin/python3.11
    /opt/homebrew/bin/python3
    /usr/local/bin/python3.13
    /usr/local/bin/python3.12
    /usr/local/bin/python3.11
    /usr/local/bin/python3
    /Library/Frameworks/Python.framework/Versions/Current/bin/python3
    /usr/bin/python3
    python3
    python
)

for py in "${candidates[@]}"; do
    if command -v "$py" >/dev/null 2>&1 && probe "$py"; then
        if [[ "$py" == /* ]]; then
            echo "$py" > "$CACHE_FILE"
        else
            command -v "$py" > "$CACHE_FILE"
        fi
        exec "$py" widget.py
    fi
done

cat <<'EOF' >&2
Could not find a Python install with a working tkinter on this Mac.

Quickest fix (you probably have Homebrew):

    brew install python-tk

then re-run ./run.sh.

If you don't have Homebrew, install Python from python.org:

    https://www.python.org/downloads/macos/

— the .pkg installer ships with a working tkinter built in.
EOF
exit 1
