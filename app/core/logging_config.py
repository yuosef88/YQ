"""
Logging configuration for the Curtain Quotation System.
Provides comprehensive logging with file rotation and debug output.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from core.paths import app_paths

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

def setup_logging(log_level=logging.INFO, enable_file_logging=True):
    """
    Set up comprehensive logging for the application.
    
    Args:
        log_level: Logging level (default: INFO)
        enable_file_logging: Whether to log to files (default: True)
    """
    # Create logs directory if it doesn't exist
    logs_dir = app_paths.data_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Create main logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Console formatter
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    if enable_file_logging:
        # File handler for all logs
        log_file = logs_dir / f"curtain_quoter_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # File formatter (more detailed)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Rotating file handler for debug logs (keep last 5 files, max 10MB each)
        debug_file = logs_dir / "debug.log"
        debug_handler = logging.handlers.RotatingFileHandler(
            debug_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(file_formatter)
        logger.addHandler(debug_handler)
        
        # Log the log file locations
        logger.info(f"Log files created:")
        logger.info(f"  Daily log: {log_file}")
        logger.info(f"  Debug log: {debug_file}")
    
    # Set specific logger levels
    logging.getLogger('PySide6').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    
    return logger

def get_logger(name):
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)

def log_function_call(func):
    """Decorator to log function calls for debugging."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned: {result}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {e}", exc_info=True)
            raise
    return wrapper

def log_database_operation(operation, table, record_id=None, details=None):
    """Log database operations for debugging."""
    logger = get_logger('database')
    message = f"DB {operation.upper()}: {table}"
    if record_id:
        message += f" (ID: {record_id})"
    if details:
        message += f" - {details}"
    logger.debug(message)

def log_business_operation(operation, details=None, user_id=None):
    """Log business operations for auditing."""
    logger = get_logger('business')
    message = f"BUSINESS {operation.upper()}"
    if user_id:
        message += f" (User: {user_id})"
    if details:
        message += f" - {details}"
    logger.info(message)

def log_error(error, context=None, user_id=None):
    """Log errors with context information."""
    logger = get_logger('errors')
    message = f"ERROR: {error}"
    if context:
        message += f" | Context: {context}"
    if user_id:
        message += f" | User: {user_id}"
    logger.error(message, exc_info=True)

def log_performance(operation, duration_ms, details=None):
    """Log performance metrics."""
    logger = get_logger('performance')
    message = f"PERFORMANCE: {operation} took {duration_ms:.2f}ms"
    if details:
        message += f" | {details}"
    logger.info(message)
