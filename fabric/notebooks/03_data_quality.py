# Fabric notebook: 03_data_quality
# Records non-medical engineering checks in ops.data_quality.

from pyspark.sql import functions as F

checks = []

silver = spark.table("silver.silver_ring_metrics")

duplicate_rows = (
    silver.groupBy("record_id", "metric_type")
    .count()
    .filter(F.col("count") > 1)
    .count()
)
checks.append(("silver.silver_ring_metrics", "unique_business_key", duplicate_rows))

invalid_operations = (
    spark.table("bronze.bronze_ring_events")
    .filter(~F.col("operation").isin("UPSERT", "DELETE"))
    .count()
)
checks.append(("bronze.bronze_ring_events", "valid_operation", invalid_operations))

missing_keys = silver.filter(
    F.col("record_id").isNull()
    | F.col("metric_type").isNull()
    | F.col("user_id").isNull()
).count()
checks.append(("silver.silver_ring_metrics", "required_keys_not_null", missing_keys))

future_events = silver.filter(
    F.col("event_time_utc") > F.current_timestamp() + F.expr("INTERVAL 5 MINUTES")
).count()
checks.append(("silver.silver_ring_metrics", "event_time_not_in_future", future_events))

# Broad plausibility bounds catch malformed telemetry; they are not medical advice.
plausibility_failures = silver.filter(
    ((F.col("metric_type") == "heart_rate") & ~F.col("numeric_value").between(20, 250))
    | ((F.col("metric_type") == "blood_oxygen") & ~F.col("numeric_value").between(50, 100))
    | ((F.col("metric_type") == "skin_temperature") & ~F.col("numeric_value").between(20, 45))
    | ((F.col("metric_type") == "steps") & ~F.col("numeric_value").between(0, 100000))
).count()
checks.append(("silver.silver_ring_metrics", "broad_value_plausibility", plausibility_failures))

rows = [
    (
        table_name,
        check_name,
        "PASS" if failed_rows == 0 else "FAIL",
        failed_rows,
        "Portfolio data-engineering validation; not a clinical rule.",
    )
    for table_name, check_name, failed_rows in checks
]

result = (
    spark.createDataFrame(
        rows,
        "table_name string, check_name string, status string, failed_rows long, details string",
    )
    .withColumn("check_time_utc", F.current_timestamp())
    .select("check_time_utc", "table_name", "check_name", "status", "failed_rows", "details")
)

result.write.format("delta").mode("append").saveAsTable("ops.data_quality")
display(result)
