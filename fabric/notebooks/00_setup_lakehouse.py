# Fabric notebook: 00_setup_lakehouse
# Attach this notebook to the lh_galaxy_ring Lakehouse.

from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, IntegerType, TimestampType
)

spark.sql("CREATE SCHEMA IF NOT EXISTS bronze")
spark.sql("CREATE SCHEMA IF NOT EXISTS silver")
spark.sql("CREATE SCHEMA IF NOT EXISTS gold")
spark.sql("CREATE SCHEMA IF NOT EXISTS ops")

event_schema = StructType([
    StructField("event_id", StringType(), False),
    StructField("record_id", StringType(), False),
    StructField("user_id", StringType(), False),
    StructField("device_id", StringType(), False),
    StructField("device_type", StringType(), True),
    StructField("metric_type", StringType(), False),
    StructField("event_time_utc", TimestampType(), False),
    StructField("end_time_utc", TimestampType(), True),
    StructField("numeric_value", DoubleType(), True),
    StructField("unit", StringType(), True),
    StructField("sleep_stage", StringType(), True),
    StructField("operation", StringType(), False),
    StructField("source_last_modified_utc", TimestampType(), False),
    StructField("ingestion_time_utc", TimestampType(), False),
    StructField("schema_version", IntegerType(), False),
])

# Eventstream should normally create/populate this table. The empty-table
# definition makes local/file-based demos reproducible.
spark.createDataFrame([], event_schema).write.format("delta").mode("ignore").saveAsTable(
    "bronze.bronze_ring_events"
)

spark.sql("""
CREATE TABLE IF NOT EXISTS silver.silver_ring_metrics (
    record_id STRING,
    user_id STRING,
    device_id STRING,
    device_type STRING,
    metric_type STRING,
    event_time_utc TIMESTAMP,
    end_time_utc TIMESTAMP,
    numeric_value DOUBLE,
    unit STRING,
    sleep_stage STRING,
    source_last_modified_utc TIMESTAMP,
    ingestion_time_utc TIMESTAMP,
    schema_version INT
) USING DELTA
""")

spark.sql("""
CREATE TABLE IF NOT EXISTS ops.pipeline_watermark (
    pipeline_name STRING,
    watermark_utc TIMESTAMP,
    updated_utc TIMESTAMP
) USING DELTA
""")

spark.sql("""
CREATE TABLE IF NOT EXISTS ops.pipeline_run (
    run_id STRING,
    pipeline_name STRING,
    started_utc TIMESTAMP,
    completed_utc TIMESTAMP,
    status STRING,
    input_rows BIGINT,
    deduplicated_rows BIGINT,
    inserted_or_updated_rows BIGINT,
    deleted_rows BIGINT,
    message STRING
) USING DELTA
""")

spark.sql("""
CREATE TABLE IF NOT EXISTS ops.data_quality (
    check_time_utc TIMESTAMP,
    table_name STRING,
    check_name STRING,
    status STRING,
    failed_rows BIGINT,
    details STRING
) USING DELTA
""")

spark.sql("""
CREATE TABLE IF NOT EXISTS gold.gold_daily_health (
    health_date DATE,
    user_id STRING,
    steps BIGINT,
    avg_heart_rate DOUBLE,
    min_heart_rate DOUBLE,
    max_heart_rate DOUBLE,
    avg_blood_oxygen DOUBLE,
    avg_skin_temperature DOUBLE,
    sleep_minutes DOUBLE,
    deep_sleep_minutes DOUBLE,
    rem_sleep_minutes DOUBLE,
    awake_sleep_minutes DOUBLE,
    energy_score DOUBLE,
    last_metric_event_utc TIMESTAMP,
    refreshed_utc TIMESTAMP
) USING DELTA
""")

# Initialize the incremental watermark.
spark.sql("""
MERGE INTO ops.pipeline_watermark AS target
USING (
    SELECT
        'bronze_to_silver' AS pipeline_name,
        TIMESTAMP('1900-01-01 00:00:00') AS watermark_utc,
        current_timestamp() AS updated_utc
) AS source
ON target.pipeline_name = source.pipeline_name
WHEN NOT MATCHED THEN INSERT *
""")

print("Lakehouse schemas and Delta tables are ready.")
