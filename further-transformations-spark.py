from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, regexp_extract
from pyspark.sql.types import StringType, FloatType, IntegerType, StructType, TimestampType
from pyspark.sql.window import Window
from pyspark.sql import functions as F
from pyspark.sql.functions import pandas_udf, PandasUDFType
from pyspark.sql.types import *

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

# Define a schema for the stateful mapGroupsWithState operation
schema = StructType([
    StructField("parsed_timestamp", TimestampType()),
    StructField("power_draw", FloatType()),
    StructField("temperature", IntegerType()),
    StructField("cpu_utilization", FloatType()),
    StructField("moving_avg_power_draw", FloatType()),
    StructField("temp_change", IntegerType()),
    StructField("cpu_util_change", FloatType()),
    StructField("power_efficiency", FloatType())
])

# Define a user-defined function (UDF) to calculate metrics
@pandas_udf(schema, PandasUDFType.GROUPED_MAP)
def calculate_metrics(pdf):
    # Sort the data by parsed_timestamp
    pdf = pdf.sort_values('parsed_timestamp')
    
    # Calculate moving average for power_draw over a 3-row window
    pdf['moving_avg_power_draw'] = pdf['power_draw'].rolling(window=3, min_periods=1).mean()
    
    # Calculate temperature change compared to previous row
    pdf['temp_change'] = pdf['temperature'].diff().fillna(0).astype(int)
    
    # Calculate CPU utilization change compared to previous row
    pdf['cpu_util_change'] = pdf['cpu_utilization'].diff().fillna(0)
    
    # Calculate power efficiency (power_draw / cpu_utilization)
    pdf['power_efficiency'] = pdf['power_draw'] / pdf['cpu_utilization']
    
    return pdf

# Apply the UDF using mapGroupsWithState
metrics_df = processed_df.groupBy(F.window("parsed_timestamp", "10 seconds")).apply(calculate_metrics)

# Write the processed data to console for demonstration
query = metrics_df \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()
