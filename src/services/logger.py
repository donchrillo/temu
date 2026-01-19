"""Zentraler Logger - Exception & Error Tracking"""

import logging
import sys
from pathlib import Path
from typing import Optional

class DatabaseLogHandler(logging.Handler):
    """Custom Handler - schreibe Errors in SQL Server"""
    
    def __init__(self):
        super().__init__()
        self.db_available = False
        self._init_db()
    
    def _init_db(self):
        """Initialisiere DB Connection"""
        try:
            from src.db.repositories.log_repository import LogRepository
            self.repo = LogRepository()
            self.repo.ensure_table_exists()
            self.db_available = True
        except Exception as e:
            # DB nicht verfügbar - nur File/Console Fallback
            self.db_available = False
    
    def emit(self, record: logging.LogRecord):
        """Schreibe Log-Record in Datenbank (nur ERROR+)"""
        if not self.db_available or record.levelno < logging.ERROR:
            return
        
        try:
            self.repo.insert_error_log(
                level=record.levelname,
                message=record.getMessage(),
                module=record.module,
                function=record.funcName,
                line_number=record.lineno,
                exception_type=record.exc_info[0].__name__ if record.exc_info else None,
                traceback_text=self.format(record) if record.exc_info else None
            )
        except Exception:
            # Stille Fehler - nicht crashen wenn DB Fehler!
            pass

def setup_logger(name: str = __name__, level: int = logging.ERROR) -> logging.Logger:
    """
    Zentraler Logger Setup
    
    Args:
        name: Logger Name (meist __name__)
        level: Log Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Konfigurierter Logger
    """
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Verhindere doppelte Handler
    if logger.hasHandlers():
        return logger
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%d.%m.%Y %H:%M:%S'
    )
    
    # 1. Console Handler (nur FEHLER!)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 2. File Handler (error.log)
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    file_handler = logging.FileHandler(log_dir / "error.log", encoding='utf-8')
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 3. Database Handler (SQL Server - nur bei ERROR+)
    db_handler = DatabaseLogHandler()
    db_handler.setLevel(logging.ERROR)
    db_handler.setFormatter(formatter)
    logger.addHandler(db_handler)
    
    return logger

# Globaler Logger
app_logger = setup_logger('TEMU_APP')
