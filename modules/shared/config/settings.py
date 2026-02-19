"""
config/settings.py
Zentrale Konfigurationsverwaltung

"""

import os
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

config_dir = Path(__file__).parent
env_file = config_dir / '.env'
load_dotenv(env_file)

# === SQL Server Connection ===
SQL_SERVER: Optional[str] = os.getenv('SQL_SERVER')
SQL_USERNAME: Optional[str] = os.getenv('SQL_USERNAME')
SQL_PASSWORD: Optional[str] = os.getenv('SQL_PASSWORD')

# === Database Names ===
DB_TOCI: str = 'toci'
DB_JTL: str = 'eazybusiness'

# === Table Names ===
TABLE_ORDERS: str = os.getenv('TABLE_ORDERS', 'temu_orders')
TABLE_ORDER_ITEMS: str = os.getenv('TABLE_ORDER_ITEMS', 'temu_order_items')
TABLE_XML_EXPORT: str = os.getenv('TABLE_XML_EXPORT', 'temu_xml_export')

# === JTL Configuration ===
JTL_WAEHRUNG: str = os.getenv('JTL_WAEHRUNG', 'EUR')
JTL_SPRACHE: str = os.getenv('JTL_SPRACHE', 'ger')
JTL_K_BENUTZER: str = os.getenv('JTL_K_BENUTZER', '1')
JTL_K_FIRMA: str = os.getenv('JTL_K_FIRMA', '1')

# === TEMU API Credentials ===
TEMU_APP_KEY: str = os.getenv('TEMU_APP_KEY', '')
TEMU_APP_SECRET: str = os.getenv('TEMU_APP_SECRET', '')
TEMU_ACCESS_TOKEN: str = os.getenv('TEMU_ACCESS_TOKEN', '')
TEMU_API_ENDPOINT: str = os.getenv('TEMU_API_ENDPOINT', 'https://openapi-b-eu.temu.com/openapi/router')

# === Logging Configuration ===
LOG_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5
