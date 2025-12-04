"""Zentrale Konfigurationsverwaltung"""

import os
from dotenv import load_dotenv
from pathlib import Path

config_dir = Path(__file__).parent
env_file = config_dir / '.env'
load_dotenv(env_file)

SQL_SERVER = os.getenv('SQL_SERVER')
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')

DB_TOCI = 'toci'
DB_JTL = 'eazybusiness'

TABLE_ORDERS = os.getenv('TABLE_ORDERS', 'temu_orders')
TABLE_ORDER_ITEMS = os.getenv('TABLE_ORDER_ITEMS', 'temu_order_items')
TABLE_XML_EXPORT = os.getenv('TABLE_XML_EXPORT', 'temu_xml_export')

JTL_WAEHRUNG = os.getenv('JTL_WAEHRUNG', 'EUR')
JTL_SPRACHE = os.getenv('JTL_SPRACHE', 'ger')
JTL_K_BENUTZER = os.getenv('JTL_K_BENUTZER', '1')
JTL_K_FIRMA = os.getenv('JTL_K_FIRMA', '1')

TEMU_APP_KEY = os.getenv('TEMU_APP_KEY')
TEMU_APP_SECRET = os.getenv('TEMU_APP_SECRET')
TEMU_ACCESS_TOKEN = os.getenv('TEMU_ACCESS_TOKEN')
TEMU_API_ENDPOINT = os.getenv('TEMU_API_ENDPOINT', 'https://open.temuglobal.com')

# --- Dateipfade (data/ Verzeichnis) ---
DATA_DIR = Path(__file__).parent.parent / 'data'
DATA_DIR.mkdir(exist_ok=True)

CSV_INPUT_PATH = DATA_DIR / os.getenv('CSV_INPUT_PATH', 'order_export.csv')
XML_OUTPUT_PATH = DATA_DIR / os.getenv('XML_OUTPUT_PATH', 'jtl_temu_bestellungen.xml')
TRACKING_EXPORT_PATH = DATA_DIR / os.getenv('TRACKING_EXPORT_PATH', 'temu_tracking_export.xlsx')
