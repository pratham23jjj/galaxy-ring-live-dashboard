I built an interactive, near-real-time Samsung Galaxy Ring analytics project using Python, Microsoft Fabric, PySpark, Delta Lake, and Power BI-ready modeling.

This is not a static dashboard mockup. The runnable application produces new synthetic wearable events, processes incremental changes, and refreshes the dashboard continuously.

The pipeline follows:

Samsung Health integration path → Eventstream → Bronze → incremental Spark/Delta MERGE → Silver → Gold → Power BI Direct Lake

What I implemented:

✅ Live event generation for heart rate, sleep, SpO₂, skin temperature, steps, and energy score
✅ Bronze, Silver, and Gold data layers
✅ Watermark processing with a 30-minute overlap
✅ Deduplication by record ID and metric type
✅ Upsert and source-delete propagation
✅ Idempotent reruns
✅ Data-quality and freshness monitoring
✅ Interactive metric and time-window filters
✅ Raw versus smoothed metric views
✅ Zoom, hover, and sortable event-level records
✅ Color-coded pipeline operations and health trends
✅ A fixed 1440×900 recording mode for consistent presentation

The app includes three interactive pages:

1. Health Overview
2. Metric Explorer
3. Pipeline Operations

For the public demo, I used synthetic data so the project is reproducible and does not expose personal health information. The repository also contains Microsoft Fabric notebooks, Delta Lake MERGE logic, Power BI DAX measures, a report theme, testing, and Mac launch scripts.

Tech stack: Python, Dash, Plotly, SQLite, Microsoft Fabric, Eventstream, PySpark, Delta Lake, OneLake, Power BI, Direct Lake, and DAX.

GitHub: [ADD YOUR GITHUB LINK]

#DataEngineering #MicrosoftFabric #PySpark #DeltaLake #PowerBI #Python #RealTimeAnalytics #Lakehouse #WearableTechnology #DataAnalytics
