"""Centralized paths for pdf_reader module.

Creates a dedicated subtree under data/pdf_reader and logs/pdf_reader.
"""
from pathlib import Path

# Root project directory (two levels up from this file: src/modules/pdf_reader)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Data and logs roots
DATA_ROOT = PROJECT_ROOT / "data" / "pdf_reader"
LOGS_ROOT = PROJECT_ROOT / "logs" / "pdf_reader"

# Subfolders
ORDNER_EINGANG_RECHNUNGEN = DATA_ROOT / "eingang" / "rechnungen"
ORDNER_EINGANG_WERBUNG = DATA_ROOT / "eingang" / "werbung"
ORDNER_LOG = LOGS_ROOT
ORDNER_AUSGANG = DATA_ROOT / "ausgang"
TMP_ORDNER = DATA_ROOT / "tmp"

def ensure_directories() -> None:
    for p in [DATA_ROOT, LOGS_ROOT, ORDNER_EINGANG_RECHNUNGEN, ORDNER_EINGANG_WERBUNG, ORDNER_AUSGANG, TMP_ORDNER]:
        p.mkdir(parents=True, exist_ok=True)

# Ensure dirs at import time
ensure_directories()
