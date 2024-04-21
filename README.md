# DEPortfolio

![image](https://github.com/BonUzo29/DEPortfolio/assets/131703145/f43178cb-207b-4821-ac59-f0288130a284)
Realtime ingested CPU readings screenshot.


### Packages needed
numpy
logging
matplotlib
sqlalchemy
confluent_kafka
pandas
streamlit
streamlit_chat

### Setup packages
    pip install -r requirements.txt

### Setup Docker containers

Install docker containerizer engine on our IDE (VsCode)

- MySQL
- Zookeeper
- Kafka
- PhPMyAdmin
- Grafana

# Create Mysql container
    docker run --name MySQL_Engine -e MYSQL_ROOT_PASSWORD=root -p 3306:3306 -d mysql:latest


# Create MYsql database

To enter db: use `mysql --user=root --password=root`

## Create DB in MySQL
    mysql -u root  -p

--------

    CREATE DATABASE gpu_metrics;
    USE gpu_metrics;

    CREATE TABLE gpu_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        datetime DATETIME NOT NULL,
        power_draw FLOAT NOT NULL,
        temperature INT NOT NULL,
        cpu_utilization FLOAT NOT NULL
    );

# Create Kafka Container
    docker run -d --name kafka-container -p 9092:9092 --network host -e TZ=UTC -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 -e KAFKA_ADVERTISED_PORT=9092 -e ZOOKEEPER_HOST=172.17.0.3 -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 ubuntu/kafka:latest

### Create kafka topic
    kafka-topics.sh --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic gpumetrics
Created topic TELEMETRY-STREAMS

# Zookeeper
    docker run -d --name zookeeper -e TZ=UTC -p 2181:2181 ubuntu/zookeeper:latest
