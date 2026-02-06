"""CSV Verarbeiter Module Configuration - Paths and Constants"""

import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# CSV Verarbeiter Data Directory
DATA_DIR = PROJECT_ROOT / 'data'
CSV_DATA_DIR = DATA_DIR / 'csv_verarbeiter'

# CSV Subdirectories
CSV_EINGANG_DIR = CSV_DATA_DIR / 'eingang'
CSV_AUSGANG_DIR = CSV_DATA_DIR / 'ausgang'
CSV_REPORTS_DIR = CSV_DATA_DIR / 'reports'

# CSV Processing Configuration
CSV_DELIMITER = os.getenv('CSV_DELIMITER', ';')  # DATEV Standard: Semikolon
CSV_INPUT_ENCODING = os.getenv('CSV_INPUT_ENCODING', 'auto')  # auto = chardet detection
CSV_OUTPUT_ENCODING = os.getenv('CSV_OUTPUT_ENCODING', 'cp1252')  # DATEV Standard: Windows-1252

# DATEV CSV Column Names (Standard-Spaltennamen)
DATEV_COLUMN_BELEG = 'Belegfeld 1'  # Amazon OrderID Spalte
DATEV_COLUMN_GEGENKONTO = 'Gegenkonto (ohne BU-Schlüssel)'  # Konten-Prüfung (0-20)
DATEV_COLUMN_KONTO = 'Konto'  # Optional: Haupt-Kontonummer

# Processing Options
SKIP_CRITICAL_ACCOUNTS = os.getenv('SKIP_CRITICAL_ACCOUNTS', 'true').lower() == 'true'
CRITICAL_ACCOUNT_RANGE = (0, 20)  # Konten 0-20 nicht verändern

# Report Settings
REPORT_CLEANUP_DAYS = int(os.getenv('REPORT_CLEANUP_DAYS', '30'))  # Reports älter als X Tage löschen


def ensure_directories():
    """Create all required directories if they don't exist."""
    CSV_EINGANG_DIR.mkdir(parents=True, exist_ok=True)
    CSV_AUSGANG_DIR.mkdir(parents=True, exist_ok=True)
    CSV_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# Ensure directories on import
ensure_directories()
