"""TEMU Module Configuration - Paths, Constants and Business Rules"""

import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# ═══════════════════════════════════════════════════════════════
# Pfade
# ═══════════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════════
# TEMU API Konvertierungsfaktoren
# ═══════════════════════════════════════════════════════════════

# TEMU liefert Beträge in Cent (Integer) → / 100 für Euro
AMOUNT_DIVISOR = 100

# TEMU liefert MwSt-Sätze als Integer (z.B. 19000000 = 19%) → / 1_000_000
TAX_RATE_DIVISOR = 1_000_000

# Default MwSt-Satz (TEMU-Format), wenn API keinen liefert
DEFAULT_TAX_RATE_RAW = 19_000_000

# Default MwSt-Satz in Prozent
DEFAULT_TAX_RATE_PERCENT = 19.00

# ═══════════════════════════════════════════════════════════════
# Order Status Validierung & Mapping
# ═══════════════════════════════════════════════════════════════

# Alle gültigen TEMU Parent Order Status Codes
VALID_ORDER_STATUSES = {0, 1, 2, 3, 4, 5}

# Status-Codes, die der Workflow verarbeiten kann (shipped, cancelled, etc.)
WORKFLOW_ORDER_STATUSES = {2, 3, 4, 5}

# TEMU Status Code → interner Status-String
ORDER_STATUS_MAP = {
    1: 'pending',
    2: 'processing',
    3: 'cancelled',
    4: 'shipped',
    5: 'delivered',
}

# ═══════════════════════════════════════════════════════════════
# Versanddienstleister / Carrier Mapping
# ═══════════════════════════════════════════════════════════════

# TEMU Carrier IDs für Tracking-Upload
CARRIER_MAPPING = {
    'dhl': 141252268,
    'dpd': 998264853,
    'ups': 960246690,
    'hermes': 123456789,
    'default': 141252268,
}

# ═══════════════════════════════════════════════════════════════
# Scheduler Defaults
# ═══════════════════════════════════════════════════════════════

ORDER_SYNC_INTERVAL_MINUTES = 30
INVENTORY_SYNC_INTERVAL_MINUTES = 60
MAX_DAYS_BACK = 90

# Länder-Mapping (Name → ISO-2)
LAND_ISO_MAP = {
    'Germany': 'DE', 'Austria': 'AT', 'France': 'FR', 'Netherlands': 'NL',
    'Poland': 'PL', 'Italy': 'IT', 'Spain': 'ES', 'Belgium': 'BE',
    'Sweden': 'SE', 'Denmark': 'DK', 'United Kingdom': 'GB',
    'Switzerland': 'CH', 'Czech Republic': 'CZ', 'Hungary': 'HU',
    'Romania': 'RO', 'Bulgaria': 'BG', 'Greece': 'GR', 'Portugal': 'PT',
}


def ensure_directories():
    """Create all required directories if they don't exist."""
    TEMU_DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEMU_XML_DIR.mkdir(parents=True, exist_ok=True)
    TEMU_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    TEMU_API_RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
