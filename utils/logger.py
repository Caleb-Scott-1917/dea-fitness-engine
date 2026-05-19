import logging
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, "data", "system_error.log")

# Ensure the data directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Configure the logger format
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s | %(levelname)s | %(module)s.%(funcName)s Line %(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def log_system_error(exception, context_message="An unexpected system exception occurred."):
    """Logs background errors to a hidden local file instead of disrupting the user interface."""
    error_msg = f"{context_message} Details: {str(exception)}"
    logging.error(error_msg)