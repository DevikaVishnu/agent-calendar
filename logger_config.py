import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# Load .env BEFORE anything else
load_dotenv()

# DEBUG: Check if LOG_LEVEL is loaded
print(f"[logger_config.py] LOG_LEVEL from .env: {os.getenv('LOG_LEVEL')}")

def get_logger(name, log_file=None, level=None):
    """
    Set up and return a logger with both file and console output
    
    Args:
        name: Logger name (usually __name__ from calling module)
        log_file: Optional log file path. If None, uses default location
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    if level is None:
        log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
        level = getattr(logging, log_level_str, logging.INFO)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(levelname)s: %(message)s'
    )
    
    # Console handler (what you see in terminal)
    #console_handler = logging.StreamHandler()
    #console_handler.setLevel(logging.INFO)  # Only INFO and above to console
    #console_handler.setFormatter(simple_formatter)
    #logger.addHandler(console_handler)
    
    # File handler (detailed logs saved to file)
    if log_file is None:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        log_file = f'logs/voice_calendar_{datetime.now().strftime("%Y%m%d")}.log'
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)  # Save everything to file
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    return logger