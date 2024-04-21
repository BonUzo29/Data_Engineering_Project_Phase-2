# DEPortfolio

![image](https://github.com/BonUzo29/Data_Engineering_Project_Phase-2/assets/131703145/6956d48b-d41d-4b5c-a305-a626ffb6a7b3)

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

# PhpMyAdmin web-UI

- First we log into the PhpMyAdmin docker container using 'root' as password and username.
  
![image](https://github.com/BonUzo29/Data_Engineering_Project_Phase-2/assets/131703145/908f469d-4d3f-4cd2-a783-f7a1f52a4796)

- We can access and view the streaming data from Kafka here, in phpMyAdmin
  
![image](https://github.com/BonUzo29/Data_Engineering_Project_Phase-2/assets/131703145/d2f6173c-8f0d-498f-b343-867cb0c9a643)

- We can quickly visualize a part (row 400 to 450) of the readings of the values saved in our MySQL database using the phpMyAdmin 'Create Chart' feature.

![image](https://github.com/BonUzo29/Data_Engineering_Project_Phase-2/assets/131703145/37c2d409-3256-453b-b39d-549525da3246)

- We can alternatively graph the values in Grafana container running on docker.
    
  We first need to create the connection to the database using our MySQL docker container IP address.
  
  ![image](https://github.com/BonUzo29/Data_Engineering_Project_Phase-2/assets/131703145/07455eb7-1e33-4602-870b-3210aa5e08bb)

- Once connection is established, we can then use a line chart or whatever is suitable inside Grafana to chart it.

  ![image](https://github.com/BonUzo29/Data_Engineering_Project_Phase-2/assets/131703145/1bd5deba-6685-40b8-826e-5fd7987ccd01)

- More charting options

  ![image](https://github.com/BonUzo29/Data_Engineering_Project_Phase-2/assets/131703145/0fabaefe-f111-4e1c-9434-92ad76027201)





# Zookeeper
    docker run -d --name zookeeper -e TZ=UTC -p 2181:2181 ubuntu/zookeeper:latest

# Create Kafka Container
    docker run -d --name kafka-container -p 9092:9092 --network host -e TZ=UTC -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 -e KAFKA_ADVERTISED_PORT=9092 -e ZOOKEEPER_HOST=172.17.0.3 -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 ubuntu/kafka:latest

### Create kafka topic
First topic 'gpumetrics' will lodge all our value from from the computer
    
    kafka-topics.sh --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic gpumetrics

Second topic 'processed_gpu_metrics' for the Kafka processed data specifically.

    kafka-topics.sh --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic processed_gpu_metrics





