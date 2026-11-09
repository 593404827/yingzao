#!/bin/sh
cd -- "$(dirname -- "$0")" || exit 1
python3 scripts/open_browser.py &
exec python3 run.py
