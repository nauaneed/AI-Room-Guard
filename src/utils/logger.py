"""
Logging utility module for the AI Guard Agent.
Provides centralized logging configuration and utilities.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from config.settings import SystemConfig

def setup_logging(log_level: str = SystemConfig.LOG_LEVEL, 
                 log_file: str = SystemConfig.LOG_FILE,
                 console_output: bool = True) -> logging.Logger:
    """
    Setup centralized logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        console_output: Whether to also output to console
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('guard_agent')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        # Colorized formatter for console (optional)
        try:
            import colorama
            colorama.init()
            
            class ColorizedFormatter(logging.Formatter):
                """Colorized log formatter"""
                
                COLORS = {
                    'DEBUG': '\033[36m',    # Cyan
                    'INFO': '\033[32m',     # Green
                    'WARNING': '\033[33m',  # Yellow
                    'ERROR': '\033[31m',    # Red
                    'CRITICAL': '\033[35m', # Magenta
                }
                RESET = '\033[0m'
                
                def format(self, record):
                    if record.levelname in self.COLORS:
                        record.levelname = (
                            f"{self.COLORS[record.levelname]}"
                            f"{record.levelname}{self.RESET}"
                        )
                    return super().format(record)
            
            console_formatter = ColorizedFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            
        except ImportError:
            # Fallback to regular formatter if colorama not available
            console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
    
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module"""
    return logging.getLogger(f'guard_agent.{name}')

class PerformanceLogger:
    """Utility class for performance logging"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.start_times = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation"""
        self.start_times[operation] = datetime.now()
        self.logger.debug(f"Started timing: {operation}")
    
    def end_timer(self, operation: str, log_level: int = logging.INFO):
        """End timing an operation and log the duration"""
        if operation not in self.start_times:
            self.logger.warning(f"No start time found for operation: {operation}")
            return
        
        duration = datetime.now() - self.start_times[operation]
        duration_ms = duration.total_seconds() * 1000
        
        self.logger.log(log_level, f"Operation '{operation}' took {duration_ms:.2f}ms")
        del self.start_times[operation]
    
    def time_operation(self, operation: str):
        """Context manager for timing operations"""
        return TimedOperation(self, operation)

class TimedOperation:
    """Context manager for timing operations"""
    
    def __init__(self, perf_logger: PerformanceLogger, operation: str):
        self.perf_logger = perf_logger
        self.operation = operation
    
    def __enter__(self):
        self.perf_logger.start_timer(self.operation)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.perf_logger.end_timer(self.operation)
        else:
            self.perf_logger.end_timer(self.operation, logging.ERROR)

# Test function
def test_logging():
    """Test logging functionality"""
    
    # Setup logging
    logger = setup_logging(log_level="DEBUG")
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test performance logging
    perf_logger = PerformanceLogger(logger)
    
    # Test manual timing
    perf_logger.start_timer("test_operation")
    import time
    time.sleep(0.1)
    perf_logger.end_timer("test_operation")
    
    # Test context manager timing
    with perf_logger.time_operation("context_test"):
        time.sleep(0.05)
    
    logger.info("Logging test completed")
    
    # Check if log file was created
    if os.path.exists(SystemConfig.LOG_FILE):
        print(f"Log file created at: {SystemConfig.LOG_FILE}")
        with open(SystemConfig.LOG_FILE, 'r') as f:
            lines = f.readlines()
            print(f"Log file contains {len(lines)} lines")
    
    return True

if __name__ == "__main__":
    test_logging()