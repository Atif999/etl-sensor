import os
import pandas as pd
from datetime import datetime
import psycopg2
from psycopg2 import sql
import logging
from dotenv import load_dotenv

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Function to get database connection
def get_db_connection():
    load_dotenv()  # Load environment variables from a .env file
    db_config = {
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT')
    }
    return psycopg2.connect(**db_config)

# Function to validate and transform data
def validate_and_transform(file_path):
    try:
        # Load data
        df = pd.read_csv(file_path)  
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        if df['date'].isnull().any():
            raise ValueError("Invalid dates detected.")


        if not ((df['T'] >= -50) & (df['T'] <= 50)).all():
            raise ValueError("Temperature values out of range.")
        if not ((df['rh'] >= 0) & (df['rh'] <= 100)).all():
            raise ValueError("Humidity values out of range.")
        if not ((df['p'] > 900) & (df['p'] < 1100)).all():
            raise ValueError("Pressure values out of range.")

        # Normalize values and overwrite the original columns
        df['T'] = (df['T'] - df['T'].mean()) / df['T'].std()  # Normalized T
        df['p'] = (df['p'] - df['p'].mean()) / df['p'].std()  # Normalized p

        # Add metadata
        df['file_name'] = os.path.basename(file_path)
        df['processed_at'] = datetime.now()

        return df
    except Exception as e:
        logging.error(f"Validation failed for {file_path}: {e}")
        quarantine_file(file_path, str(e))
        return None
  
# Function to quarantine invalid files
def quarantine_file(file_path, reason):
    quarantine_folder = "./quarantine"
    os.makedirs(quarantine_folder, exist_ok=True)
    quarantine_path = os.path.join(quarantine_folder, os.path.basename(file_path))
    os.rename(file_path, quarantine_path)
    with open(quarantine_path + "_error.log", "w") as log_file:
        log_file.write(reason)

# Function to calculate aggregated metrics
def calculate_metrics(df):
    metrics = df[['T', 'rh', 'p']].agg(['min', 'max', 'mean', 'std']).transpose()
    metrics.reset_index(inplace=True)
    metrics.rename(columns={'index': 'sensor_type'}, inplace=True)
    return metrics

# Function to save data to the database
def save_to_database(raw_data, metrics):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        for _, row in raw_data.iterrows():
            placeholders = ', '.join(['%s'] * len(row))
            columns = ', '.join(row.index)
            query = f"INSERT INTO raw_sensor_data ({columns}) VALUES ({placeholders})"
            cursor.execute(query, tuple(row))

        # Insert aggregated metrics with metadata
        for _, row in metrics.iterrows():
            cursor.execute(
                sql.SQL(
                    """
                    INSERT INTO aggregated_metrics (
                        sensor_type, min, max, mean, std, file_name, timestamp, processed_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                ),
                (
                    row['sensor_type'], row['min'], row['max'], 
                    row['mean'], row['std'], 
                    raw_data['file_name'].iloc[0],  # Use file_name from raw data
                    raw_data['date'].min(),        # Minimum date from raw data as "data timestamp"
                    datetime.now()                 # Current time as "processed_at"
                )
            )

        conn.commit()
    except Exception as e:
        logging.error(f"Database operation failed: {e}")
    finally:
        conn.close()