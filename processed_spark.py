from pyspark.sql import SparkSession
import pyspark.sql.functions as F

if __name__ == "__main__":
    spark = SparkSession.builder \
        .appName("KafkaSparkStructuredStreaming") \
        .config("spark.sql.shuffle.partitions", "1") \
        .getOrCreate()

    # Set log level to ERROR
    spark.sparkContext.setLogLevel("ERROR")

    # Read data from Kafka
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", "gpu_metrics") \
        .load()

    # Transform value_str to columns
    split_col = F.split(df['value'].cast("string"), ',')
    df = df.withColumn('value_str', split_col)
    df = df.withColumn('power_draw', df['value_str'].getItem(0).cast("float") * 100)
    df = df.withColumn('temperature', df['value_str'].getItem(1).cast("float") * 100)
    df = df.withColumn('cpu_utilization', df['value_str'].getItem(2).cast("float"))

    # Select relevant columns
    df = df.select('key', 'value', 'topic', 'partition', 'offset', 'timestamp', 'timestampType', 
                   'value_str', 'power_draw', 'temperature', 'cpu_utilization')

    # Write the transformed data to console for debugging
    query = df.writeStream \
        .outputMode("append") \
        .format("console") \
        .start()

    query.awaitTermination()

    spark.stop()
