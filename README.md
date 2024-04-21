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
- pyspark[sql-kafka]
- PhPMyAdmin
- Grafana

# Create Mysql container
    docker run --name MySQL_Engine -e MYSQL_ROOT_PASSWORD=root -p 3306:3306 -d mysql:latest


# Create MYsql database

To enter db: use `mysql --user=root --password=root`

## Create DB in MySQL
    mysql -u root  -p

Then create database and table

    CREATE DATABASE gpu_metrics;
    USE gpu_metrics;

   
    CREATE TABLE IF NOT EXISTS processed_gpu_data (
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



# PySpark

Initialize our docker container using this:

    docker run -it --rm   -v /home/blackjack/GITHUB\ PROJECTS/bona:/mnt   ruslanmv/pyspark-elyra:3.0.2
    
To mount a volume for persistence, we us the '-v' flag as shown above. This mounts our local directory `/home/bona` to the container's `/mnt` directory:

    -v /home/blackjack/GITHUB\ PROJECTS/bona:/mnt: 

We submit the PySpark script that receives the Kafka values using this:
    
    spark-submit   --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.1   processed_spark.py


The 'processed_spark.py', when it works correctly returns this:

    24/04/21 23:24:02 INFO BlockManagerMasterEndpoint: Registering block manager 192.168.163.235:46231 with 434.4 MiB RAM, BlockManagerId(driver, 192.168.163.235, 46231, None)
    24/04/21 23:24:02 INFO BlockManagerMaster: Registered BlockManager BlockManagerId(driver, 192.168.163.235, 46231, None)
    24/04/21 23:24:02 INFO BlockManager: Initialized BlockManager: BlockManagerId(driver, 192.168.163.235, 46231, None)
    24/04/21 23:24:02 INFO SharedState: Setting hive.metastore.warehouse.dir ('null') to the value of spark.sql.warehouse.dir ('file:/home/bona/spark-warehouse').
    24/04/21 23:24:02 INFO SharedState: Warehouse path is 'file:/home/bona/spark-warehouse'.
    -------------------------------------------
    Batch: 0
    -------------------------------------------
    +----------------+----------+-----------+---------------+
    |parsed_timestamp|power_draw|temperature|cpu_utilization|
    +----------------+----------+-----------+---------------+
    +----------------+----------+-----------+---------------+
    
    -------------------------------------------
    Batch: 1
    -------------------------------------------
    +-------------------+----------+-----------+---------------+
    |   parsed_timestamp|power_draw|temperature|cpu_utilization|
    +-------------------+----------+-----------+---------------+
    |2024-04-21 23:24:06|      4.02|         47|           46.8|
    +-------------------+----------+-----------+---------------+
    
    -------------------------------------------
    Batch: 2
    -------------------------------------------
    +-------------------+----------+-----------+---------------+
    |   parsed_timestamp|power_draw|temperature|cpu_utilization|
    +-------------------+----------+-----------+---------------+
    |2024-04-21 23:24:08|      4.16|         47|           16.3|
    +-------------------+----------+-----------+---------------+
    
    -------------------------------------------
    Batch: 3
    -------------------------------------------


To demonstrate further data processing and transformations that PySpark is capable of, we created a new script called `further-transformations-spark.py`.
This script now adds some columns. The `calculate_metrics` UDF now calculates these new metrics:

`temp_change`: Temperature change compared to the previous row.
`cpu_util_change`: CPU utilization change compared to the previous row.
`power_efficiency`: Power efficiency, which is the ratio of power_draw to cpu_utilization.

When we run it we produce columns with more transormations as seen below:


    -------------------------------------------
    Batch: 1
    -------------------------------------------
    +-------------------+----------+-----------+---------------+---------------------+-----------+---------------+----------------+
    |   parsed_timestamp|power_draw|temperature|cpu_utilization|moving_avg_power_draw|temp_change|cpu_util_change|power_efficiency|
    +-------------------+----------+-----------+---------------+---------------------+-----------+---------------+----------------+
    |2024-04-21 23:51:53|      6.11|         46|           44.1|                 6.11|          0|            0.0|      0.13854876|
    +-------------------+----------+-----------+---------------+---------------------+-----------+---------------+----------------+
    
    -------------------------------------------
    Batch: 2
    -------------------------------------------
    +-------------------+----------+-----------+---------------+---------------------+-----------+---------------+----------------+
    |   parsed_timestamp|power_draw|temperature|cpu_utilization|moving_avg_power_draw|temp_change|cpu_util_change|power_efficiency|
    +-------------------+----------+-----------+---------------+---------------------+-----------+---------------+----------------+
    |2024-04-21 23:51:55|      4.61|         47|           56.5|                 4.61|          0|            0.0|     0.081592925|
    +-------------------+----------+-----------+---------------+---------------------+-----------+---------------+----------------+
    
    scala:333)
    	at org.apache.spark.sql.execution.streaming.StreamExecution$$anon$1.run(StreamExecution.scala:244)
    -------------------------------------------
    Batch: 3
    -------------------------------------------
    +-------------------+----------+-----------+---------------+---------------------+-----------+---------------+----------------+
    |   parsed_timestamp|power_draw|temperature|cpu_utilization|moving_avg_power_draw|temp_change|cpu_util_change|power_efficiency|
    +-------------------+----------+-----------+---------------+---------------------+-----------+---------------+----------------+
    |2024-04-21 23:51:57|      4.78|         47|           33.5|                 4.78|          0|            0.0|      0.14268658|
    +-------------------+----------+-----------+---------------+---------------------+-----------+---------------+----------------+


As PySpark container runs, we can see more under-the-hood operations by visiting this local URL: 

    http://192.168.163.235:4040/StreamingQuery/statistics/?id=50d6909a-89ad-42e8-be3b-34de702b8b28

![image](https://github.com/BonUzo29/Data_Engineering_Project_Phase-2/assets/131703145/ab16748f-3b28-4581-a05d-3e13e4689ff6)


