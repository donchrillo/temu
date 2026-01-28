"""
PDF Reader Module Logger
Logs für alle PDF-spezifischen Operationen (Werbung, Rechnungen)
"""
import logging
from src.services.logger import create_module_logger

# Allgemeiner PDF Reader Logger: INFO+ → logs/pdf_reader/pdf_reader.log
pdf_reader_logger = create_module_logger(
    module_name='PDF_READER',
    log_subdir='pdf_reader',
    console_level=logging.ERROR,
    file_level=logging.INFO,
    file_name='pdf_reader.log'
)

# Service-spezifische Logger
werbung_logger = create_module_logger(
    module_name='PDF_READER_WERBUNG',
    log_subdir='pdf_reader',
    console_level=logging.ERROR,
    file_level=logging.INFO,
    file_name='werbung_read.log'
)

werbung_extraction_logger = create_module_logger(
    module_name='PDF_READER_WERBUNG_EXTRACTION',
    log_subdir='pdf_reader',
    console_level=logging.ERROR,
    file_level=logging.INFO,
    file_name='werbung_extraction.log'
)

rechnung_logger = create_module_logger(
    module_name='PDF_READER_RECHNUNG',
    log_subdir='pdf_reader',
    console_level=logging.ERROR,
    file_level=logging.INFO,
    file_name='rechnung_read.log'
)

# Convenience functions (allgemeiner Logger)
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
def reinitialize_loggers():
    """Reinitialize logger handlers (needed after file deletion/recreation)"""
    global werbung_logger, werbung_extraction_logger, rechnung_logger, pdf_reader_logger
    
    # Clear existing handlers
    for logger in [werbung_logger, werbung_extraction_logger, rechnung_logger, pdf_reader_logger]:
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
    
    # Recreate loggers with fresh handlers
    werbung_logger = create_module_logger(
        module_name='PDF_READER_WERBUNG',
        log_subdir='pdf_reader',
        console_level=logging.ERROR,
        file_level=logging.INFO,
        file_name='werbung_read.log'
    )
    
    werbung_extraction_logger = create_module_logger(
        module_name='PDF_READER_WERBUNG_EXTRACTION',
        log_subdir='pdf_reader',
        console_level=logging.ERROR,
        file_level=logging.INFO,
        file_name='werbung_extraction.log'
    )
    
    rechnung_logger = create_module_logger(
        module_name='PDF_READER_RECHNUNG',
        log_subdir='pdf_reader',
        console_level=logging.ERROR,
        file_level=logging.INFO,
        file_name='rechnung_read.log'
    )
    
    pdf_reader_logger = create_module_logger(
        module_name='PDF_READER',
        log_subdir='pdf_reader',
        console_level=logging.ERROR,
        file_level=logging.INFO,
        file_name='pdf_reader.log'
    )