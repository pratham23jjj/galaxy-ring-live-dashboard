# Microsoft Fabric implementation

The runnable Dash demo uses SQLite so it can execute locally without a Fabric tenant. The notebooks in this folder are the matching production-style Microsoft Fabric implementation:

1. `00_setup_lakehouse.py` creates Bronze, Silver, Gold, watermark, run-audit, and data-quality Delta tables.
2. `01_bronze_to_silver_incremental.py` reads a watermark overlap window, deduplicates the business key, and applies Delta Lake `MERGE` upserts and deletes.
3. `02_silver_to_gold_daily.py` builds the daily health model used by Power BI.
4. `03_data_quality.py` records engineering checks.
5. `04_maintenance.py` runs Delta optimization and maintenance.

Attach the notebooks to a Fabric Lakehouse named `lh_galaxy_ring`. Route Eventstream output into `bronze.bronze_ring_events`, then orchestrate the notebooks with the pipeline design in `pipeline/orchestration.md`.
