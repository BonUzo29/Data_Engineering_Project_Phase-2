import time
from time import sleep
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import psutil
import subprocess
import mysql.connector
import threading

# Kafka Configuration
KAFKA_RAW_TOPIC = 'gpu_metrics'
KAFKA_PROCESSED_TOPIC = 'processed_gpu_metrics'
KAFKA_SERVER = 'localhost:9092'

# MySQL Configuration
MYSQL_HOST = '172.17.0.3'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'root'
MYSQL_DATABASE = 'gpu_metrics'

def create_processed_table(mysql_conn):
    try:
        cursor = mysql_conn.cursor()
        create_table_query = """
            CREATE TABLE IF NOT EXISTS processed_gpu_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                datetime DATETIME NOT NULL,
                power_draw FLOAT NOT NULL,
                temperature INT NOT NULL,
                cpu_utilization FLOAT NOT NULL
            )
        """
        cursor.execute(create_table_query)
        mysql_conn.commit()
        cursor.close()
        print("Table 'processed_gpu_data' created successfully.")
    except mysql.connector.Error as e:
        print(f"Error creating table: {e}")

def get_gpu_metrics():
    nvidia_smi_command = 'nvidia-smi --query-gpu=power.draw,temperature.gpu --format=csv,noheader,nounits'
    output = subprocess.check_output(nvidia_smi_command, shell=True).decode('utf-8').strip().split(',')
    power_draw = float(output[0])
    temperature = int(output[1])
    return power_draw, temperature

def get_cpu_utilization():
    return psutil.cpu_percent(interval=1)

def send_to_kafka(producer, topic, data):
    try:
        producer.send(topic, data.encode('utf-8'))
        producer.flush()
        print(f"Sent to Kafka topic {topic}: {data}")
    except KafkaError as e:
        print(f"Failed to send to Kafka topic {topic}: {e}")

def process_data(data):
    # Here you can implement any processing you want to apply to the data
    return data.upper()

def store_to_mysql(mysql_conn, data):
    attempts = 3  # Number of attempts to retry
    for _ in range(attempts):
        try:
            cursor = mysql_conn.cursor()
            insert_query = "INSERT INTO processed_gpu_data (datetime, power_draw, temperature, cpu_utilization) VALUES (%s, %s, %s, %s)"
            cursor.execute(insert_query, data)
            mysql_conn.commit()
            cursor.close()
            print(f"Stored processed data in MySQL: {data}")
            break  # Break out of loop if successful
        except mysql.connector.Error as e:
            print(f"Error processing and storing data: {e}")
            print("Retrying...")
            time.sleep(1)  # Wait for 1 second before retrying
    else:
        print("Failed to store data after multiple attempts.")


def process_and_store_processed_data(mysql_conn):
    consumer = KafkaConsumer(KAFKA_PROCESSED_TOPIC, bootstrap_servers=KAFKA_SERVER)
    for message in consumer:
        processed_data = message.value.decode('utf-8')
        try:
            # Extracting individual values from processed data string
            split_data = processed_data.split(',')
            timestamp = split_data[0].strip()
            
            # Extracting and converting power draw
            power_draw_str = split_data[1].split(':')[1].strip()  # Extracting value after ":"
            power_draw = float(power_draw_str.split()[0])  # Splitting to remove "W" and converting to float
            
            # Extracting and converting temperature
            temperature_str = split_data[2].split(':')[1].strip()  # Extracting value after ":"
            temperature = int(temperature_str.split()[0])  # Splitting to remove "°C" and converting to int
            
            # Extracting and converting CPU utilization
            cpu_utilization_str = split_data[3].split(':')[1].strip()  # Extracting value after ":"
            cpu_utilization = float(cpu_utilization_str.split()[0])  # Splitting to remove "%" and converting to float

            # Store processed data in MySQL
            store_to_mysql(mysql_conn, (timestamp, power_draw, temperature, cpu_utilization))
        except Exception as e:
            print(f"Error processing and storing data: {e}")

def main():
    # Connect to Kafka
    producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER)

    # Connect to MySQL
    mysql_conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )

    try:
        while True:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            power_draw, temperature = get_gpu_metrics()
            cpu_utilization = get_cpu_utilization()

            # Format raw data
            raw_data = f"{timestamp}, Power Draw: {power_draw} W, Temperature: {temperature} °C, CPU Utilization: {cpu_utilization} %"
            print("Raw Data:", raw_data)

            # Send raw data to Kafka
            send_to_kafka(producer, KAFKA_RAW_TOPIC, raw_data)
            print("Sent to Kafka:", raw_data)

            # Process the raw data
            processed_data = process_data(raw_data)
            print("Processed Data:", processed_data)

            # Send processed data to Kafka for further processing
            send_to_kafka(producer, KAFKA_PROCESSED_TOPIC, processed_data)
            print("Sent to Kafka (Processed):", processed_data)

            # Store raw data in MySQL
            store_to_mysql(mysql_conn, (timestamp, power_draw, temperature, cpu_utilization))
            print("Stored in MySQL:", (timestamp, power_draw, temperature, cpu_utilization))

            # Removed sleep for faster iteration
            # sleep(1)  # Sleep for 1 second
    except KeyboardInterrupt:
        print("Exiting...")
        producer.close()
        mysql_conn.close()

if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
