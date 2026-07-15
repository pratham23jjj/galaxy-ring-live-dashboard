# Fabric notebook: 04_maintenance
# Run after substantial ingestion/update activity, not necessarily every 15 minutes.

spark.sql("OPTIMIZE silver.silver_ring_metrics VORDER")
spark.sql("OPTIMIZE gold.gold_daily_health VORDER")

# Keep the platform's default retention policy unless your governance process
# explicitly approves a different value.
spark.sql("VACUUM silver.silver_ring_metrics")
spark.sql("VACUUM gold.gold_daily_health")

print("Delta maintenance completed.")
