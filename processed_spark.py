from pyspark.sql import SparkSession
from pyspark.sql.functions import split

spark = SparkSession.builder \
    .appName("GPU_Metrics_Processing") \
    .getOrCreate()

# Read from Kafka topic
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "processed_gpu_metrics") \
    .load()

# Convert value column to string and split on commas
df = df.withColumn("value_str", df["value"].cast("string"))
split_cols = split(df["value_str"], ",")
df = df.withColumn("timestamp", split_cols.getItem(0))
df = df.withColumn("power_draw", split_cols.getItem(1))
df = df.withColumn("temperature", split_cols.getItem(2))
df = df.withColumn("cpu_utilization", split_cols.getItem(3))

# You can further process or write this DataFrame as needed
query = df \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()
