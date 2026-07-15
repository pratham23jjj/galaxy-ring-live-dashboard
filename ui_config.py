"""UI and refresh constants for the recording-ready dashboard.

Override the numeric values through environment variables when needed, e.g.
DASHBOARD_WIDTH=1680 DASHBOARD_HEIGHT=1050 ./run_demo_mac.command
"""
from __future__ import annotations

import os


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


# Default recording canvas. The app remains responsive, but Fit mode uses these
# dimensions to select compact chart/card heights that stay inside the viewport.
DEFAULT_VIEWPORT_WIDTH = _env_int("DASHBOARD_WIDTH", 1440)
DEFAULT_VIEWPORT_HEIGHT = _env_int("DASHBOARD_HEIGHT", 900)
SIDEBAR_WIDTH = _env_int("DASHBOARD_SIDEBAR_WIDTH", 228)
HEADER_HEIGHT = _env_int("DASHBOARD_HEADER_HEIGHT", 76)
KPI_HEIGHT = _env_int("DASHBOARD_KPI_HEIGHT", 104)
CHART_HEIGHT = _env_int("DASHBOARD_CHART_HEIGHT", 224)
OPS_STRIP_HEIGHT = _env_int("DASHBOARD_OPS_HEIGHT", 78)
REFRESH_MS = _env_int("DASHBOARD_REFRESH_MS", 2500)
VIEWPORT_POLL_MS = _env_int("DASHBOARD_VIEWPORT_POLL_MS", 1000)

# Small-screen threshold used by the clientside viewport callback.
COMPACT_BREAKPOINT_WIDTH = _env_int("DASHBOARD_COMPACT_WIDTH", 1280)
COMPACT_BREAKPOINT_HEIGHT = _env_int("DASHBOARD_COMPACT_HEIGHT", 780)
