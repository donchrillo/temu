"""TEMU Module Configuration - Paths and Constants"""

import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# TEMU Data Directory
DATA_DIR = PROJECT_ROOT / 'data'
TEMU_DATA_DIR = DATA_DIR / 'temu'

# TEMU Subdirectories
TEMU_XML_DIR = TEMU_DATA_DIR / 'xml'
TEMU_EXPORT_DIR = TEMU_DATA_DIR / 'export'
TEMU_API_RESPONSES_DIR = TEMU_DATA_DIR / 'api_responses'

# File Paths
CSV_INPUT_PATH = DATA_DIR / os.getenv('CSV_INPUT_PATH', 'order_export.csv')
XML_OUTPUT_PATH = TEMU_XML_DIR / os.getenv('XML_OUTPUT_PATH', 'jtl_temu_bestellungen.xml')
TRACKING_EXPORT_PATH = DATA_DIR / os.getenv('TRACKING_EXPORT_PATH', 'temu_tracking_export.xlsx')


def ensure_directories():
    """Create all required directories if they don't exist."""
    TEMU_DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEMU_XML_DIR.mkdir(parents=True, exist_ok=True)
    TEMU_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    TEMU_API_RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
