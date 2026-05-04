#!/usr/bin/env bash
# Launch the finance widget. Place an alias in your shell or a Login Item
# pointing to this script if you want it to start with macOS.
set -e
cd "$(dirname "$0")"
exec python3 widget.py
