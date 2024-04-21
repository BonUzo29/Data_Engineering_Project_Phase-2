from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, regexp_extract
from pyspark.sql.types import StringType, FloatType, IntegerType, StructType, TimestampType

spark = SparkSession.builder \
    .appName("KafkaStreamProcessing") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# Define the schema to match the data format from Kafka
schema = StructType() \
    .add("timestamp", StringType()) \
    .add("power_draw", FloatType()) \
    .add("temperature", IntegerType()) \
    .add("cpu_utilization", FloatType())

# Subscribe to Kafka topic
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "gpu_metrics") \
    .load()

# Convert value column from Kafka to string
parsed_df = df \
    .selectExpr("CAST(value AS STRING)")

# Extract data from the string using regular expressions
parsed_df = parsed_df.withColumn("timestamp", regexp_extract(col("value"), r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", 1))
parsed_df = parsed_df.withColumn("power_draw", regexp_extract(col("value"), r"Power Draw: ([\d.]+)", 1).cast(FloatType()))
parsed_df = parsed_df.withColumn("temperature", regexp_extract(col("value"), r"Temperature: (\d+)", 1).cast(IntegerType()))
parsed_df = parsed_df.withColumn("cpu_utilization", regexp_extract(col("value"), r"CPU Utilization: ([\d.]+)", 1).cast(FloatType()))

# Convert the timestamp column to TimestampType
parsed_df = parsed_df.withColumn("parsed_timestamp", col("timestamp").cast(TimestampType()))

# Select only the desired columns
processed_df = parsed_df.select("parsed_timestamp", "power_draw", "temperature", "cpu_utilization")

# Write the processed data to console for demonstration
query = processed_df \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()
