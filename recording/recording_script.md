# 3-minute recording script

## 0:00–0:15 — Dashboard hook
Open the live Overview page.

“I built a near-real-time Galaxy Ring analytics pipeline with a working live dashboard. The public demo uses synthetic events so it is reproducible and does not expose personal health data.”

## 0:15–0:40 — Live metrics
Point to the live-feed indicator and wait for the heart-rate chart and freshness card to update.

“The simulator publishes heart rate, steps, blood oxygen, skin temperature, and energy events. The dashboard refreshes every three seconds while the incremental pipeline runs every five seconds.”

## 0:40–1:10 — Event-level explorer
Open Metric Explorer. Change Heart Rate to Blood Oxygen and switch the time window.

“Each event has a stable record ID, event time, source modification time, and operation. Those fields let the pipeline handle late corrections and source deletes.”

## 1:10–1:55 — Pipeline operations
Open Pipeline Operations.

“Bronze preserves immutable input events. The incremental job reads from the saved watermark with a 30-minute overlap, deduplicates each business key, and upserts only the newest source modification into Silver. Delete events remove the current Silver record. Gold daily aggregates and quality checks run before the watermark advances.”

Point to throughput, duration, upserts/deletes, and quality charts.

## 1:55–2:30 — Code
Show `db.py` at `process_incremental`, then `simulator.py`.

“The run is idempotent because rerunning the overlap window produces the same Silver state. The simulator deliberately sends late updates and deletes so the behavior is visible rather than only described.”

## 2:30–3:00 — Power BI path
Show the `powerbi` folder, theme, DAX, and source CSVs.

“The same Gold, Silver, run, and quality tables are supplied as Power BI-ready data. In Fabric they become Delta tables and the semantic model can use Direct Lake. The repository includes the theme, DAX measures, exact report layout, screenshots, and recording script.”
