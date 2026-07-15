# Screen-resolution controls

The dashboard defaults to a recording-safe 1440×900 layout.

## Change constants permanently

Edit `ui_config.py`:

```python
DEFAULT_VIEWPORT_WIDTH = 1440
DEFAULT_VIEWPORT_HEIGHT = 900
SIDEBAR_WIDTH = 228
HEADER_HEIGHT = 76
KPI_HEIGHT = 104
CHART_HEIGHT = 224
OPS_STRIP_HEIGHT = 78
REFRESH_MS = 2500
```

## Override from Terminal

```bash
DASHBOARD_WIDTH=1680 DASHBOARD_HEIGHT=1050 ./run_demo_mac.command
```

## Dashboard display modes

- `Fit 1440×900` keeps the compact recording layout.
- `Auto` expands on larger screens and uses compact mode below 1280×780.

The CSS also reduces graph and card heights automatically below 820px and 700px viewport heights. Horizontal overflow is disabled, grids use `minmax(0, 1fr)`, and every Plotly chart is responsive.
