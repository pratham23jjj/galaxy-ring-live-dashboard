from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

from ui_config import DEFAULT_VIEWPORT_HEIGHT, DEFAULT_VIEWPORT_WIDTH

ROOT = Path(__file__).resolve().parent


def wait_for_server(url: str, timeout_seconds: int = 25) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.35)
    raise RuntimeError(f"Dashboard did not start within {timeout_seconds} seconds: {url}")


def open_recording_window(url: str, width: int, height: int) -> None:
    system = platform.system()
    chrome_candidates: list[Path] = []
    if system == "Darwin":
        chrome_candidates = [
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
    elif system == "Linux":
        chrome_candidates = [Path("/usr/bin/google-chrome"), Path("/usr/bin/chromium"), Path("/usr/bin/chromium-browser")]

    chrome = next((path for path in chrome_candidates if path.exists()), None)
    if chrome:
        subprocess.Popen(
            [
                str(chrome),
                "--new-window",
                f"--window-size={width},{height}",
                "--force-device-scale-factor=1",
                url,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return

    if system == "Darwin":
        subprocess.Popen(["open", url])
    else:
        webbrowser.open(url)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the Galaxy Ring live dashboard.")
    parser.add_argument("--no-browser", action="store_true", help="Start the server without opening a browser.")
    parser.add_argument("--width", type=int, default=DEFAULT_VIEWPORT_WIDTH, help="Recording browser width.")
    parser.add_argument("--height", type=int, default=DEFAULT_VIEWPORT_HEIGHT, help="Recording browser height.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    port = os.getenv("PORT", "8050")
    url = f"http://127.0.0.1:{port}"
    process = subprocess.Popen([sys.executable, str(ROOT / "app.py")], cwd=ROOT)
    try:
        wait_for_server(url)
        if not args.no_browser:
            open_recording_window(url, max(1024, args.width), max(650, args.height))
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
    except Exception:
        process.terminate()
        raise


if __name__ == "__main__":
    main()
