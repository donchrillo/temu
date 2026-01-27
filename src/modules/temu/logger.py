"""
TEMU Module Logger
Logs für alle TEMU-spezifischen Operationen (Orders, Inventory, API Calls)
"""
import logging
from src.services.logger import create_module_logger

# TEMU Logger: INFO+ → logs/temu/temu.log, ERROR+ → Console
temu_logger = create_module_logger(
    module_name='TEMU',
    log_subdir='temu',
    console_level=logging.ERROR,
    file_level=logging.INFO,
    file_name='temu.log'
)

# Convenience functions
def debug(msg: str, *args, **kwargs):
    """Log DEBUG message"""
    temu_logger.debug(msg, *args, **kwargs)

def info(msg: str, *args, **kwargs):
    """Log INFO message"""
    temu_logger.info(msg, *args, **kwargs)

def warning(msg: str, *args, **kwargs):
    """Log WARNING message"""
    temu_logger.warning(msg, *args, **kwargs)

def error(msg: str, *args, **kwargs):
    """Log ERROR message"""
    temu_logger.error(msg, *args, **kwargs)

def critical(msg: str, *args, **kwargs):
    """Log CRITICAL message"""
    temu_logger.critical(msg, *args, **kwargs)
