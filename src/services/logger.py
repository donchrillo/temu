"""
Zentraler Logger - nur Konsole und File
funtkioniert auch ohne DB-Verbindung.

Es werden nur ERROR und CRITICAL Logs erfasst.
"""
import logging
import sys
from pathlib import Path

def setup_logger(name: str = __name__, level: int = logging.ERROR) -> logging.Logger:
    """
    Zentraler Logger Setup (ohne DB-Handler)
    
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

    return logger

# Globaler Logger
app_logger = setup_logger('TEMU_APP')