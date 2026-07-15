# Delivery manifest — v2

## Working interactive software

- `app.py` — live three-page Dash dashboard with filters, pause/resume, smooth transitions, and responsive Plotly charts
- `assets/styles.css` — color-coded UI, hover animation, fixed recording density, and responsive safeguards
- `ui_config.py` — centralized width, height, card, chart, sidebar, and refresh constants
- `simulator.py` — synthetic wearable event producer with late updates and deletes
- `db.py` — Bronze/Silver/Gold pipeline, watermark, upserts, delete propagation, and quality checks
- `start_demo.py` — starts the server and opens a fixed-size recording window when Chrome is available
- `run_demo_mac.command` — one-click Mac launcher configured for 1440×900
- `run_demo.bat`, `run_demo.sh` — Windows and Linux launchers
- `Dockerfile`, `docker-compose.yml` — container launch option

## Interactive dashboard pages

- Health Overview — live ticker, KPI cards, trend selector, heart-rate smoothing, sleep colors, and operational status
- Metric Explorer — metric/window filters, raw-versus-smoothed display, zoom, hover, statistics, and sortable records
- Pipeline Operations — medallion flow, throughput, duration, CDC activity, data quality, and incremental processing logic

## Recording and screen-fit assets

- `screenshots/overview.png` — 1440×900 browser-rendered overview
- `screenshots/metric_explorer.png` — 1440×900 browser-rendered explorer
- `screenshots/pipeline_operations.png` — 1440×900 browser-rendered operations page
- `recording/final/galaxy_ring_dashboard_v2_captioned.mp4` — captioned 53-second v2 preview using the real dashboard captures
- `recording/capture_dashboard_previews.py` — repeatable preview/QC capture helper
- `UI_VALIDATION.txt` — viewport and callback validation results

## Microsoft Fabric

- `fabric/notebooks/00_setup_lakehouse.py`
- `fabric/notebooks/01_bronze_to_silver_incremental.py`
- `fabric/notebooks/02_silver_to_gold_daily.py`
- `fabric/notebooks/03_data_quality.py`
- `fabric/notebooks/04_maintenance.py`
- `fabric/pipeline/orchestration.md`

## Power BI

- Refreshed CSV tables under `powerbi/data/`
- `powerbi/GalaxyRing_DarkTheme.json`
- `powerbi/measures.dax`
- `powerbi/build_report.md`

## Source-code images

- Seven PNG files under `code_images/`

## LinkedIn

- `linkedin/post.md`
- `linkedin/carousel_order.md`
- `linkedin/cover_16x9.png`
- `linkedin/carousel_cover_4x5.png`

## Validation

- `tests/test_pipeline.py`
- `TEST_RESULTS.txt`
- `UI_VALIDATION.txt`
- All Python files compile successfully
- All three incremental-pipeline tests pass
