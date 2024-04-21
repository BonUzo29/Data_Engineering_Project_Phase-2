import time
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer
import psutil
import subprocess
import mysql.connector

# Kafka Configuration
KAFKA_TOPIC = 'gpu_metrics'
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

def send_to_kafka(producer, data):
    try:
        producer.send(KAFKA_TOPIC, data.encode('utf-8'))
        producer.flush()
        print(f"Sent to Kafka topic {KAFKA_TOPIC}: {data}")
    except Exception as e:
        print(f"Failed to send to Kafka topic {KAFKA_TOPIC}: {e}")

def process_data(data):
    # Here you can implement any processing you want to apply to the data
    return data.upper()

def store_to_mysql(mysql_conn, data):
    try:
        cursor = mysql_conn.cursor()
        insert_query = "INSERT INTO processed_gpu_data (datetime, power_draw, temperature, cpu_utilization) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_query, data)
        mysql_conn.commit()
        cursor.close()
        print(f"Stored processed data in MySQL: {data}")
    except Exception as e:
        print(f"Error processing and storing data: {e}")

def process_and_store_processed_data(mysql_conn):
    consumer = KafkaConsumer(KAFKA_TOPIC, bootstrap_servers=KAFKA_SERVER)
    for message in consumer:
        raw_data = message.value.decode('utf-8')
        try:
            # Extracting individual values from raw data string
            split_data = raw_data.split(',')
            timestamp = split_data[0].strip()
            power_draw = float(split_data[1].split(':')[1].strip().split()[0])  # Extracting and converting power draw
            temperature = int(split_data[2].split(':')[1].strip().split()[0])  # Extracting and converting temperature
            cpu_utilization = float(split_data[3].split(':')[1].strip().split()[0])  # Extracting and converting CPU utilization

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

    # Create processed_gpu_data table if not exists
    create_processed_table(mysql_conn)

    try:
        while True:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            power_draw, temperature = get_gpu_metrics()
            cpu_utilization = get_cpu_utilization()

            # Format raw data
            raw_data = f"{timestamp}, Power Draw: {power_draw} W, Temperature: {temperature} °C, CPU Utilization: {cpu_utilization} %"
            print("Raw Data:", raw_data)

            # Send raw data to Kafka
            send_to_kafka(producer, raw_data)

            # Sleep for 1 second
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
        producer.close()
        mysql_conn.close()

if __name__ == "__main__":
    main()
