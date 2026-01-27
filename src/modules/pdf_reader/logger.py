"""
PDF Reader Module Logger
Logs für alle PDF-spezifischen Operationen (Werbung, Rechnungen)
"""
import logging
from src.services.logger import create_module_logger

# PDF Reader Logger: INFO+ → logs/pdf_reader/pdf_reader.log, ERROR+ → Console
pdf_reader_logger = create_module_logger(
    module_name='PDF_READER',
    log_subdir='pdf_reader',
    console_level=logging.ERROR,
    file_level=logging.INFO,
    file_name='pdf_reader.log'
)

# Convenience functions
def debug(msg: str, *args, **kwargs):
    """Log DEBUG message"""
    pdf_reader_logger.debug(msg, *args, **kwargs)

def info(msg: str, *args, **kwargs):
    """Log INFO message"""
    pdf_reader_logger.info(msg, *args, **kwargs)

def warning(msg: str, *args, **kwargs):
    """Log WARNING message"""
    pdf_reader_logger.warning(msg, *args, **kwargs)

def error(msg: str, *args, **kwargs):
    """Log ERROR message"""
    pdf_reader_logger.error(msg, *args, **kwargs)

def critical(msg: str, *args, **kwargs):
    """Log CRITICAL message"""
    pdf_reader_logger.critical(msg, *args, **kwargs)
