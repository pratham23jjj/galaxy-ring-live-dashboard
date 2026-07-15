# Build the actual Power BI report

The included live Dash application is already runnable and is used for the supplied screenshots/video. To reproduce the same report in Power BI Desktop:

1. Open Power BI Desktop and select **Get data → Text/CSV**.
2. Import every CSV in `powerbi/data/`:
   - `gold_daily_health.csv`
   - `silver_metrics.csv`
   - `pipeline_runs.csv`
   - `data_quality.csv`
3. Set date/time data types for every `_utc` field and set `health_date` to Date.
4. Import `GalaxyRing_DarkTheme.json` through **View → Themes → Browse for themes**.
5. Create the measures from `measures.dax`.
6. Build three pages:

## Page 1: Health Overview
- Six cards: Total Steps, Sleep Hours, Average Heart Rate, Average Blood Oxygen, Average Skin Temperature, Average Energy Score.
- Line chart: `health_date` vs Total Steps and Steps 7D Average.
- Column chart: `health_date` vs Sleep Hours.
- Line chart: `event_time_utc` vs `numeric_value`, filtered to `heart_rate`.
- Donut: sleep stage by sum of `numeric_value`, filtered to `sleep_stage`.

## Page 2: Metric Explorer
- Slicer: `metric_type`.
- Line chart: `event_time_utc` vs `numeric_value`.
- Table: record ID, metric, event time, value, unit, modified time, ingestion time.

## Page 3: Pipeline Operations
- Cards: Successful Runs, Failed Quality Checks, latest watermark, total input rows.
- Line chart: pipeline run time vs input and deduplicated rows.
- Stacked columns: upsert rows and delete rows.
- Bar chart: quality check vs failed rows.

For Fabric, load the same tables as Delta tables in a Lakehouse and create a semantic model in Direct Lake mode. The report layer is unchanged.
