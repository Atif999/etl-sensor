import os
import time
import logging
from utilites import validate_and_transform, calculate_metrics, save_to_database
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables
load_dotenv()
DATA_FOLDER = os.getenv('DATA_FOLDER', 'data')  # Default to 'data' folder
PROCESSED_FOLDER = os.getenv('PROCESSED_FOLDER', 'processed')  # Folder for processed files
MONITOR_INTERVAL = int(os.getenv('MONITOR_INTERVAL', 5))  # Polling interval in seconds

# Create required folders if they don't exist
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')



# Retry decorator for the entire file processing
@retry(
    stop=stop_after_attempt(5),  # Retry up to 5 times
    wait=wait_exponential(multiplier=1, min=2, max=10),  # Exponential backoff
    retry_error_callback=lambda retry_state: logging.error(
        f"File processing failed after retries: {retry_state.outcome.exception()}"
    )
)
def process_file(file_path):
    """Process a single CSV file."""
    try:
        logging.info(f"Processing file: {file_path}")
        raw_data = validate_and_transform(file_path)
        if raw_data is not None:
            logging.info("Data validated and transformed successfully.")
            metrics = calculate_metrics(raw_data)
            logging.info("Metrics calculated.")
            save_to_database(raw_data, metrics)
            logging.info("Data saved to the database.")
            
            # Move the processed file to the processed folder
            processed_file_path = os.path.join(PROCESSED_FOLDER, os.path.basename(file_path))
            os.rename(file_path, processed_file_path)
            logging.info(f"Moved processed file to: {processed_file_path}")
        else:
            logging.warning(f"File {file_path} could not be processed and was quarantined.")
    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}")

def monitor_folder():
    """Monitor the data folder and process new files."""
    logging.info("Starting folder monitoring...")
    processed_files = set()  # Keep track of already processed files

    while True:
        try:
            for filename in os.listdir(DATA_FOLDER):
                file_path = os.path.join(DATA_FOLDER, filename)
                
                # Check if the file is a CSV and hasn't been processed yet
                if filename.endswith('.csv') and file_path not in processed_files:
                    logging.info(f"Detected new file: {filename}")
                    process_file(file_path)
                    processed_files.add(file_path)

            # Wait for the specified interval before checking again
            time.sleep(MONITOR_INTERVAL)
        except Exception as e:
            logging.error(f"Error in folder monitoring: {e}")

if __name__ == "__main__":
    monitor_folder()