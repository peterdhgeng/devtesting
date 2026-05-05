#!/usr/bin/env bash
# Launch the finance widget. Tries to find a Python that actually has tkinter
# (pyenv-installed Pythons often don't), falling back to /usr/bin/python3
# which on macOS ships with Tk built in.
set -e
cd "$(dirname "$0")"

candidates=(
    /usr/bin/python3
    /Library/Frameworks/Python.framework/Versions/Current/bin/python3
    python3
    python
)

for py in "${candidates[@]}"; do
    if command -v "$py" >/dev/null 2>&1 && "$py" -c "import tkinter" >/dev/null 2>&1; then
        exec "$py" widget.py
    fi
done

cat <<'EOF' >&2
Could not find a Python install with tkinter available.

Quickest fix on macOS:
  /usr/bin/python3 widget.py

If /usr/bin/python3 isn't present, install Xcode Command Line Tools:
  xcode-select --install

Or rebuild your pyenv Python with Tk support:
  brew install tcl-tk
  env PYTHON_CONFIGURE_OPTS="--with-tcltk-includes='-I$(brew --prefix tcl-tk)/include' \
      --with-tcltk-libs='-L$(brew --prefix tcl-tk)/lib -ltcl8.6 -ltk8.6'" \
    pyenv install --force 3.11.14
EOF
exit 1
