"""
PDF Reader Module Logger
Logs für alle PDF-spezifischen Operationen (Werbung, Rechnungen)
"""
import logging
from src.services.logger import create_module_logger

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

def reinitialize_loggers():
    """Reinitialize logger handlers (needed after file deletion/recreation)"""
    global werbung_logger, werbung_extraction_logger, rechnung_logger
    
    # Clear existing handlers
    for logger in [werbung_logger, werbung_extraction_logger, rechnung_logger]:
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