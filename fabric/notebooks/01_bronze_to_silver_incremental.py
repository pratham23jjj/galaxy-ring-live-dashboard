# Fabric notebook: 01_bronze_to_silver_incremental
# Purpose: apply only new/changed Bronze events to Silver using an idempotent
# Delta MERGE. Attach to lh_galaxy_ring.

from datetime import datetime, timezone
from uuid import uuid4

from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql.window import Window

PIPELINE_NAME = "bronze_to_silver"
SAFETY_OVERLAP_MINUTES = 30
run_id = str(uuid4())
started_utc = datetime.now(timezone.utc)

watermark_row = (
    spark.table("ops.pipeline_watermark")
    .filter(F.col("pipeline_name") == PIPELINE_NAME)
    .select("watermark_utc")
    .first()
)
if watermark_row is None:
    raise RuntimeError(f"Missing watermark row for {PIPELINE_NAME}")

watermark_utc = watermark_row["watermark_utc"]

source = (
    spark.table("bronze.bronze_ring_events")
    .filter(
        F.col("ingestion_time_utc")
        > F.expr(
            f"TIMESTAMPADD(MINUTE, -{SAFETY_OVERLAP_MINUTES}, "
            f"TIMESTAMP('{watermark_utc}'))"
        )
    )
    .filter(F.col("operation").isin("UPSERT", "DELETE"))
)

input_rows = source.count()

# A single source row per business key is required for deterministic MERGE.
# The newest source modification wins, followed by ingestion time and event ID.
window = Window.partitionBy("record_id", "metric_type").orderBy(
    F.col("source_last_modified_utc").desc(),
    F.col("ingestion_time_utc").desc(),
    F.col("event_id").desc(),
)
latest = source.withColumn("_rn", F.row_number().over(window)).filter("_rn = 1").drop("_rn")
deduplicated_rows = latest.count()

target = DeltaTable.forName(spark, "silver.silver_ring_metrics")

merge_condition = """
target.record_id = source.record_id
AND target.metric_type = source.metric_type
"""

(
    target.alias("target")
    .merge(latest.alias("source"), merge_condition)
    .whenMatchedDelete(
        condition="""
        source.operation = 'DELETE'
        AND source.source_last_modified_utc >= target.source_last_modified_utc
        """
    )
    .whenMatchedUpdate(
        condition="""
        source.operation = 'UPSERT'
        AND source.source_last_modified_utc >= target.source_last_modified_utc
        """,
        set={
            "user_id": "source.user_id",
            "device_id": "source.device_id",
            "device_type": "source.device_type",
            "event_time_utc": "source.event_time_utc",
            "end_time_utc": "source.end_time_utc",
            "numeric_value": "source.numeric_value",
            "unit": "source.unit",
            "sleep_stage": "source.sleep_stage",
            "source_last_modified_utc": "source.source_last_modified_utc",
            "ingestion_time_utc": "source.ingestion_time_utc",
            "schema_version": "source.schema_version",
        },
    )
    .whenNotMatchedInsert(
        condition="source.operation = 'UPSERT'",
        values={
            "record_id": "source.record_id",
            "user_id": "source.user_id",
            "device_id": "source.device_id",
            "device_type": "source.device_type",
            "metric_type": "source.metric_type",
            "event_time_utc": "source.event_time_utc",
            "end_time_utc": "source.end_time_utc",
            "numeric_value": "source.numeric_value",
            "unit": "source.unit",
            "sleep_stage": "source.sleep_stage",
            "source_last_modified_utc": "source.source_last_modified_utc",
            "ingestion_time_utc": "source.ingestion_time_utc",
            "schema_version": "source.schema_version",
        },
    )
    .execute()
)

max_ingestion = source.agg(F.max("ingestion_time_utc").alias("max_ts")).first()["max_ts"]

if max_ingestion is not None:
    watermark_source = spark.createDataFrame(
        [(PIPELINE_NAME, max_ingestion)],
        ["pipeline_name", "watermark_utc"],
    ).withColumn("updated_utc", F.current_timestamp())

    (
        DeltaTable.forName(spark, "ops.pipeline_watermark")
        .alias("target")
        .merge(watermark_source.alias("source"), "target.pipeline_name = source.pipeline_name")
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )

delete_rows = latest.filter(F.col("operation") == "DELETE").count()
upsert_rows = latest.filter(F.col("operation") == "UPSERT").count()
completed_utc = datetime.now(timezone.utc)

run_log = spark.createDataFrame(
    [
        (
            run_id,
            PIPELINE_NAME,
            started_utc,
            completed_utc,
            "SUCCEEDED",
            input_rows,
            deduplicated_rows,
            upsert_rows,
            delete_rows,
            f"Processed with a {SAFETY_OVERLAP_MINUTES}-minute safety overlap.",
        )
    ],
    """
    run_id string, pipeline_name string, started_utc timestamp,
    completed_utc timestamp, status string, input_rows long,
    deduplicated_rows long, inserted_or_updated_rows long,
    deleted_rows long, message string
    """,
)
run_log.write.format("delta").mode("append").saveAsTable("ops.pipeline_run")

print(
    {
        "run_id": run_id,
        "input_rows": input_rows,
        "deduplicated_rows": deduplicated_rows,
        "upserts": upsert_rows,
        "deletes": delete_rows,
        "new_watermark": str(max_ingestion),
    }
)
