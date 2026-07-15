# Fabric pipeline orchestration

Pipeline name: `pl_galaxy_ring_incremental`

## Incremental pipeline

Schedule: every 15 minutes

1. **Notebook — Bronze to Silver**
   - Notebook: `01_bronze_to_silver_incremental`
   - Retry: 2
   - Retry interval: 2 minutes
   - Timeout: 20 minutes
2. **Notebook — Data quality**
   - Depends on Bronze to Silver succeeding
   - Notebook: `03_data_quality`
3. **Failure path**
   - Add a notification activity or call a Teams/Email endpoint
   - Include pipeline name, run ID, failed activity, and error text

## Daily Gold pipeline

Schedule: once each morning after expected overnight ring synchronization

1. **Notebook — Silver to Gold**
   - Notebook: `02_silver_to_gold_daily`
2. **Notebook — Data quality**
   - Notebook: `03_data_quality`
3. **Lakehouse maintenance**
   - Use the maintenance activity where available, or run `04_maintenance`
4. **Optional semantic-model action**
   - Direct Lake generally avoids a traditional import refresh, but validate framing/freshness for your model and report.

## Parameters worth adding

- `p_pipeline_name`
- `p_safety_overlap_minutes`
- `p_process_from_utc`
- `p_process_to_utc`
- `p_full_reload`
- `p_environment` (`dev`, `test`, `prod`)

## Monitoring

Track:

- Number of Bronze input rows
- Number of deduplicated keys
- Number of upserts and deletes
- New watermark value
- Processing latency
- Failed data-quality checks
- Pipeline duration and status

## Demo tip

Before recording, publish several initial events, then publish:
- one duplicate,
- one corrected heart-rate record with the same `record_id`,
- one `DELETE` event.

After the pipeline runs, show that Silver contains exactly one current record per business key.
