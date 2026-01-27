"""Shared logger setup for pdf_reader module.

DEPRECATED: Use src.modules.pdf_reader.logger instead.
This file kept for backward compatibility.

Provides rotating file logging plus forwarding of ERROR+ to the PDF Reader logger.
"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from .config import ORDNER_LOG, ensure_directories
from src.modules.pdf_reader.logger import pdf_reader_logger


class _ForwardToPdfReaderLogger(logging.Handler):
    """Forward ERROR+ records to the PDF Reader logger."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            pdf_reader_logger.log(record.levelno, msg)
        except Exception:
            pass


def get_pdf_logger(name: str, logfile: str, level: int = logging.INFO,
                   max_bytes: int = 512_000, backups: int = 3) -> logging.Logger:
    """Return a configured logger for pdf_reader with rotation and forwarding.

    Ensures directories exist, avoids duplicate handlers on repeated imports.
    """
    ensure_directories()

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    log_path = Path(ORDNER_LOG) / logfile
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # mode="a" behält alte Logs bis cleanup
    rotating = RotatingFileHandler(log_path, mode="a", maxBytes=max_bytes,
                                   backupCount=backups, encoding="utf-8")
    rotating.setFormatter(formatter)
    rotating.setLevel(level)
    logger.addHandler(rotating)

    forward = _ForwardToPdfReaderLogger()
    forward.setFormatter(formatter)
    forward.setLevel(logging.ERROR)
    logger.addHandler(forward)

    logger.propagate = False
    return logger
