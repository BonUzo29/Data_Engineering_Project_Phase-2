from time import sleep
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
import psutil
import subprocess
import mysql.connector

# Kafka Configuration
KAFKA_TOPIC = 'gpu_metrics'
KAFKA_SERVER = 'localhost:9092'

# MySQL Configuration
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'root'
MYSQL_DATABASE = 'gpu_metrics'

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
        print(f"Sent to Kafka: {data}")
    except KafkaError as e:
        print(f"Failed to send to Kafka: {e}")

def process_data(data):
    # Here you can implement any processing you want to apply to the data
    return data.upper()

def store_to_mysql(mysql_conn, data):
    cursor = mysql_conn.cursor()
    insert_query = "INSERT INTO gpu_data (datetime, power_draw, temperature, cpu_utilization) VALUES (%s, %s, %s, %s)"
    cursor.execute(insert_query, data)
    mysql_conn.commit()
    cursor.close()

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

            # Format data
            data = f"{timestamp}, Power Draw: {power_draw} W, Temperature: {temperature} °C, CPU Utilization: {cpu_utilization} %"

            # Send raw data to Kafka
            send_to_kafka(producer, data)

            # Process the data
            processed_data = process_data(data)

            # Store processed data in MySQL
            store_to_mysql(mysql_conn, (timestamp, power_draw, temperature, cpu_utilization))

            sleep(1)  # Sleep for 1 second
    except KeyboardInterrupt:
        print("Exiting...")
        producer.close()
        mysql_conn.close()

if __name__ == "__main__":
    main()
