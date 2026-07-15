#!/bin/zsh
set -e

cd "$(dirname "$0")"

# Recording layout constants. Change these two values for another canvas.
export DASHBOARD_WIDTH="${DASHBOARD_WIDTH:-1440}"
export DASHBOARD_HEIGHT="${DASHBOARD_HEIGHT:-900}"
export DASHBOARD_REFRESH_MS="${DASHBOARD_REFRESH_MS:-2500}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed. Install it from https://www.python.org/downloads/macos/ and run this file again."
  echo
  read "?Press Return to close..."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Creating a local Python environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo
echo "Starting the Galaxy Ring live dashboard"
echo "Recording window: ${DASHBOARD_WIDTH}×${DASHBOARD_HEIGHT}"
echo "Dashboard URL: http://127.0.0.1:8050"
echo "Keep this Terminal window open. Press Control+C to stop."
echo
python start_demo.py --width "$DASHBOARD_WIDTH" --height "$DASHBOARD_HEIGHT"
