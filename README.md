# Galaxy Ring Live Analytics — Interactive Dashboard v2

This package contains a real, runnable, near-real-time dashboard backed by a working Bronze/Silver/Gold incremental pipeline. The dashboard itself is code-driven with Dash and Plotly; the preview screenshots are browser-rendered from the same figures and live SQLite data.

## What changed in v2

- Recording-safe **Fit 1440×900** layout enabled by default
- Automatic compact layout for smaller browser windows
- Live viewport-size indicator in the header
- Width, height, card, chart, and refresh constants in `ui_config.py`
- Mac launcher opens Google Chrome at the configured recording dimensions when Chrome is installed
- Six metric-specific, color-coded KPI cards
- Smooth Plotly transitions and spline curves
- Live event ticker and per-minute event rate
- Seven-day and 14-day trend controls
- Pause/resume live dashboard updates
- Interactive Metric Explorer with metric, time-window, and smoothing controls
- Zoom, hover, sorting, and event-level data inspection
- Color-coded Pipeline Operations page with the complete medallion flow
- Height-aware CSS safeguards for 820px and 700px browser heights
- No horizontal overflow at the validated 1440×900 recording viewport

## Run on macOS

Double-click:

```text
run_demo_mac.command
```

The launcher:

1. Creates a local `.venv` on the first run
2. Installs the required Python packages
3. Starts the live event producer and incremental pipeline
4. Opens the dashboard at `http://127.0.0.1:8050`
5. Opens Google Chrome in a 1440×900 window when Chrome is available

Keep the Terminal window open. Press **Control+C** to stop the dashboard.

If macOS blocks the launcher, right-click the file, choose **Open**, and confirm.

## Terminal option

```bash
cd /path/to/galaxy-ring-live-dashboard
chmod +x run_demo_mac.command
./run_demo_mac.command
```

## Change the recording resolution

The default constants are in `ui_config.py`:

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

Override the window size without editing code:

```bash
DASHBOARD_WIDTH=1680 DASHBOARD_HEIGHT=1050 ./run_demo_mac.command
```

The dashboard offers two display modes:

- **Fit 1440×900:** fixed, compact recording density
- **Auto:** expands on larger screens and switches to a compact layout on smaller screens

## Interactive features

### Health Overview

- Live event ticker and event-rate counter
- Seven-day and 14-day switching
- Steps target and seven-day moving average
- Color-coded sleep duration bars
- Live heart-rate points with a smoothed line
- Sleep-stage donut chart
- Freshness, successful runs, quality checks, and watermark monitoring

### Metric Explorer

- Metric selector
- One-hour, six-hour, 24-hour, and all-history windows
- Raw or five-point-smoothed display
- Zoom and hover inspection
- Sortable event table
- Latest, minimum, maximum, and record-count cards

### Pipeline Operations

- Bronze and Silver row counts
- Latest upserts and deletes
- Eventstream → Bronze → Spark MERGE → Silver → Gold flow
- Input-versus-deduplicated throughput
- Color-coded job duration
- Upserts-versus-deletes activity
- Latest data-quality results

## What is actually running

- A synthetic Galaxy Ring event producer emits new records every two seconds.
- Bronze stores immutable `UPSERT` and `DELETE` events in SQLite.
- The incremental processor runs every five seconds.
- It uses a saved watermark plus a 30-minute overlap.
- It deduplicates by `record_id + metric_type`.
- Newer changes update Silver and source deletes are propagated.
- Gold daily aggregates and data-quality checks are recalculated.
- The dashboard refreshes every 2.5 seconds by default.

## Microsoft Fabric and Power BI

The `fabric` folder contains the PySpark and Delta Lake implementation for Microsoft Fabric. The `powerbi` folder contains refreshed data exports, a dark theme, DAX measures, and exact report-building instructions.

A `.pbix` is not included because creating and validating a binary Power BI Desktop report requires Power BI Desktop on Windows. The runnable dashboard demonstrates the complete interaction and visual design on macOS, while the Fabric and Power BI assets provide the deployment path.

## Validation

Run the pipeline tests:

```bash
python -m unittest discover -s tests -v
```

See:

- `TEST_RESULTS.txt`
- `UI_VALIDATION.txt`
- `screenshots/overview.png`
- `screenshots/metric_explorer.png`
- `screenshots/pipeline_operations.png`

## Clean database reset

```bash
python -c "from db import initialize_db, seed_history; initialize_db(reset=True); seed_history()"
```

## Disclaimer

Synthetic wellness analytics demo. Not medical advice and not affiliated with Samsung or Microsoft.

## Public hosting

The project includes `render.yaml`, a production Gunicorn command, a health endpoint, and configurable storage. See [`HOSTING_RENDER.md`](HOSTING_RENDER.md) for the public deployment steps.
