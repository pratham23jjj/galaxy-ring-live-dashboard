# Fabric notebook: 02_silver_to_gold_daily
# Purpose: produce one analytics row per user and day.

from delta.tables import DeltaTable
from pyspark.sql import functions as F

silver = spark.table("silver.silver_ring_metrics").withColumn(
    "health_date", F.to_date("event_time_utc")
)

daily = (
    silver.groupBy("health_date", "user_id")
    .agg(
        F.max(F.when(F.col("metric_type") == "steps", F.col("numeric_value"))).cast("long").alias("steps"),
        F.avg(F.when(F.col("metric_type") == "heart_rate", F.col("numeric_value"))).alias("avg_heart_rate"),
        F.min(F.when(F.col("metric_type") == "heart_rate", F.col("numeric_value"))).alias("min_heart_rate"),
        F.max(F.when(F.col("metric_type") == "heart_rate", F.col("numeric_value"))).alias("max_heart_rate"),
        F.avg(F.when(F.col("metric_type") == "blood_oxygen", F.col("numeric_value"))).alias("avg_blood_oxygen"),
        F.avg(F.when(F.col("metric_type") == "skin_temperature", F.col("numeric_value"))).alias("avg_skin_temperature"),
        F.max(F.when(F.col("metric_type") == "sleep_session", F.col("numeric_value"))).alias("sleep_minutes"),
        F.sum(
            F.when(
                (F.col("metric_type") == "sleep_stage") & (F.col("sleep_stage") == "DEEP"),
                F.col("numeric_value"),
            )
        ).alias("deep_sleep_minutes"),
        F.sum(
            F.when(
                (F.col("metric_type") == "sleep_stage") & (F.col("sleep_stage") == "REM"),
                F.col("numeric_value"),
            )
        ).alias("rem_sleep_minutes"),
        F.sum(
            F.when(
                (F.col("metric_type") == "sleep_stage") & (F.col("sleep_stage") == "AWAKE"),
                F.col("numeric_value"),
            )
        ).alias("awake_sleep_minutes"),
        F.max(F.when(F.col("metric_type") == "energy_score", F.col("numeric_value"))).alias("energy_score"),
        F.max("event_time_utc").alias("last_metric_event_utc"),
    )
    .withColumn("refreshed_utc", F.current_timestamp())
)

target = DeltaTable.forName(spark, "gold.gold_daily_health")
(
    target.alias("target")
    .merge(
        daily.alias("source"),
        "target.health_date = source.health_date AND target.user_id = source.user_id",
    )
    .whenMatchedUpdateAll()
    .whenNotMatchedInsertAll()
    .execute()
)

print(f"Gold daily rows prepared: {daily.count()}")
