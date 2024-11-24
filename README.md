# etl-sensor-docs

**Architecture and Design of the Pipeline**

**Overview**
The ETL pipeline processes sensor data in real-time by monitoring a directory for new files. Once a file is detected, it validates, transforms, and aggregates the data before saving it to a PostgreSQL database. The pipeline includes resilience features like retries for transient errors, quarantining invalid files, and logging.

**Pipeline Components**

Folder Monitoring:
The pipeline continuously monitors a folder for new CSV files every 5–10 seconds.
Uses the os module for directory scanning.

File Validation and Transformation:
Validates data integrity, such as date formats, numerical ranges, and missing values.
Transforms data by normalizing key columns and converting temperatures to Kelvin.
Aggregation:

Calculates metrics (min, max, mean, std) for critical columns like temperature, humidity, and pressure.
Focuses on essential sensor data while still storing all columns.

Database Interaction:
Saves raw data and aggregated metrics to a PostgreSQL database.
Uses prepared SQL queries to ensure security and consistency.

Error Handling and Resilience:
Implements a retry mechanism for failed operations (e.g., database connection failures).
Quarantines invalid files for manual review.

Logging:
Logs important events, such as successful processing, retries, and errors.

Pipeline Flow

1. Folder Monitoring:
   Detects a new CSV file and triggers processing.

2. Validation:
   Reads and validates the data.
   Quarantines invalid files.

3. Transformation:
   Applies normalization, Kelvin conversion, and metadata addition.

4. Aggregation:
   Computes statistical metrics for critical columns.

5. Database Insertion:
   Inserts raw data and metrics into the PostgreSQL database.
   Retries on failures to ensure data consistency.

6. File Archival:
   Moves processed files to a "processed" folder for record-keeping.

Instructions for Setting Up and Running the Pipeline Locally

1. Install Dependencies
   Make sure you have the required Python libraries and PostgreSQL installed.

Install Python 3.8 or higher.
Install dependencies using pip

2. You can find all the dependencies in requirements.txt file

3. Set Up PostgreSQL Database
   Create a PostgreSQL database and the required tables.

Connect to PostgreSQL and run the `script.sql` file

4. Set Up Environment Variables
   Create a .env file in the root directory of your project with the following content

**Database Configuration**

DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432

**File Monitoring Configuration**

DATA_FOLDER=./data # Folder to monitor for new files
PROCESSED_FOLDER=./processed # Folder to move processed files
MONITOR_INTERVAL=5 # Interval (in seconds) to check for new files

5. Run the Pipeline
   Run the pipeline by executing the etl-pipeline script:

`python etl-pipeline.py`

# Scale Process For Files

Scaling a data ingestion and processing pipeline to handle millions of files per day requires careful consideration of both the data volume and the processing load. For such a high-throughput pipeline, we need to implement distributed systems, event-driven architectures, and efficient storage solutions. Below is a brief outline of how I would design the pipeline to scale horizontally, along with optimizations for high-volume data ingestion and processing.

1. Horizontal Scalability Considerations
   To scale the pipeline horizontally, we can distribute the tasks across multiple workers or processing nodes, ensuring high availability and better performance as the data volume increases.

Key Design Components:
1.1. Distributed File Storage:

Cloud Storage Solutions (e.g., AWS S3, Google Cloud Storage):
Why? Cloud storage solutions allow you to scale storage capacity as needed and offer high durability and availability. Storing files in S3 or GCS makes it easier to access data globally and asynchronously.
How? Files can be directly uploaded to the cloud storage, and metadata about each file (such as filename, size, timestamp) can be stored in a database for processing orchestration.

1.2. Event-Driven Architecture:

AWS Lambda or Google Cloud Functions:
Why? Using event-driven serverless architectures like AWS Lambda or Google Cloud Functions allows the pipeline to automatically scale based on incoming events. When a file is uploaded to the cloud storage (S3/GCS), a notification can trigger a Lambda function to start processing the file.
How? Set up an event trigger (e.g., S3 put event) to invoke a Lambda function. The function would then pull the file from the storage, process it (e.g., validate, aggregate, and save to the database), and then archive the processed file or move it to a separate "processed" bucket/folder.

1.3. Distributed Data Processing Framework:
Apache Spark
Why? For large-scale data processing, Spark allows distributed processing of large datasets across multiple nodes, enabling parallel computation for tasks like validation, aggregation, and transformation.
How? Spark can be used for both batch processing (processing large chunks of data at scheduled intervals) or streaming processing (processing data as it arrives). Spark jobs could read data from cloud storage (S3 or GCS), perform transformations, and write the results back to a database or another storage solution.

2. Optimizations for High-Volume Data Ingestion and Processing

2.1. Data Partitioning and Sharding:
For efficient processing, partition or shard data based on certain keys (e.g., timestamp, sensor ID, or location).
Why? This reduces the amount of data each worker has to process, and allows Spark or other processing engines to work on smaller chunks of data in parallel.

2.2. Asynchronous Processing:
Instead of processing files synchronously one after the other, process them asynchronously in parallel. This can be achieved by using a task queue (e.g., AWS SQS, Kafka, or RabbitMQ) where each task (file processing) is queued and handled by a pool of workers.
Why? It reduces the bottleneck caused by sequential processing and improves throughput.

3. Pipeline with Apache Spark and AWS Lambda
   Here's a more detailed example of how we could scale the pipeline with AWS Lambda and Apache Spark:

Data Ingestion:

Files are uploaded to an S3 bucket. Each new file upload triggers an S3 event.
Lambda Function is invoked by the S3 event notification.
File Processing:

Lambda pulls the file from S3, validates and transforms the data, and performs simple calculations like aggregating metrics.
For large datasets, Lambda can pass the file to an Apache Spark job running on an Amazon EMR cluster for distributed processing.
Storage:

Raw data is stored back in S3 (perhaps in a separate folder).
Processed data (aggregated metrics, etc.) is saved to a PostgreSQL database (via RDS or Aurora), ensuring the database is optimized for querying.
Consider using Amazon Redshift or Google BigQuery for analytics and long-term storage of large, structured datasets.
Scaling and Monitoring:

Use AWS CloudWatch to monitor Lambda function executions and failures.
Apache Spark on EMR can scale dynamically to process large batches of data.
Kafka or Step Functions can be used to manage the task execution flow.

AWS Lambda and Apache Spark (on Amazon EMR). This pipeline will scale horizontally and process large amounts of sensor data uploaded to AWS S3. We'll break the implementation into the following steps:

Data Ingestion (S3 + Lambda)
Data Processing (Lambda + Apache Spark on EMR)
Storage (S3 + RDS/PostgreSQL)
Event-Driven Architecture (S3 + Lambda)

1. Data Ingestion and Event-Driven Architecture
   First, let's define how to trigger AWS Lambda when a new CSV file is uploaded to an S3 bucket.

1.1. Create S3 Bucket
Create an S3 bucket to store raw data. For example: sensor-data.
You can create a separate folder (prefix) for raw and processed files within the bucket, e.g., raw/ and processed/.
1.2. Create Lambda Function for S3 Event Trigger
Here’s the Python code for the Lambda function. The function is triggered when a new file is uploaded to the S3 bucket.

2. Data Processing with Apache Spark on EMR
   We now need to submit a Spark job to process the uploaded CSV files. The Spark job will process the raw data, perform any transformations or validations, and save the results back to S3 or a database.

2.1. Create a Spark Job Script (PySpark)
This script will run on the EMR cluster. It will process the CSV file, calculate metrics, and write the results to a PostgreSQL database or another S3 bucket.

3. Storage (S3 + PostgreSQL)
   After processing the data, the aggregated results are stored back in an S3 bucket or a PostgreSQL database.

S3: The processed files are stored in a processed/ folder in the same S3 bucket.
PostgreSQL: If you prefer to store the results in a database, you can use the JDBC connection within the Spark job script to write the data into a PostgreSQL database.

4. Orchestration (AWS Step Functions or Managed Workflow)
   Instead of managing the Lambda and Spark jobs manually, you could use AWS Step Functions to orchestrate the entire process.

Step Functions can help you orchestrate the sequence of Lambda executions, manage error handling, and retry logic. 5. Scaling with AWS
Auto-Scaling: AWS EMR can scale the number of workers based on the load. The Lambda function will trigger the Spark job as soon as new data is uploaded to the S3 bucket.
Lambda Scaling: AWS Lambda scales automatically to handle high-frequency events and processes each file in parallel.
