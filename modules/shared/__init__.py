"""
Shared Module - Re-Export Layer für gemeinsame Funktionen

Dieses Modul bietet einen einfachen Import-Layer für alle gemeinsamen
Funktionen (Database, Logging, Config), ohne die bestehende Architektur
in src/ zu verändern.

Verwendung in neuen Modulen:
    from shared import db_connect, BaseRepository, setup_logger, settings
"""

# Database (re-export von src/db/)
from src.db.connection import get_engine, db_connect, get_db, close_all_engines
from src.db.repositories.base import BaseRepository

# Logging (re-export von src/services/)
from src.services.logger import create_module_logger
from src.services.log_service import log_service
from src.services import app_logger

# Config (re-export von config/)
from config.settings import (
    SQL_SERVER,
    SQL_USERNAME,
    SQL_PASSWORD,
    DB_TOCI,
    DB_JTL,
    TABLE_ORDERS,
    TABLE_ORDER_ITEMS,
    TABLE_XML_EXPORT,
    JTL_WAEHRUNG,
    JTL_SPRACHE,
    JTL_K_BENUTZER,
    JTL_K_FIRMA,
    TEMU_APP_KEY,
    TEMU_APP_SECRET,
    TEMU_ACCESS_TOKEN,
    TEMU_API_ENDPOINT
)

# Public API
__all__ = [
    # Database
    "get_engine",
    "db_connect",
    "get_db",
    "close_all_engines",
    "BaseRepository",

    # Logging
    "create_module_logger",
    "log_service",
    "app_logger",

    # Config - SQL Server
    "SQL_SERVER",
    "SQL_USERNAME",
    "SQL_PASSWORD",
    "DB_TOCI",
    "DB_JTL",

    # Config - Tables
    "TABLE_ORDERS",
    "TABLE_ORDER_ITEMS",
    "TABLE_XML_EXPORT",

    # Config - JTL
    "JTL_WAEHRUNG",
    "JTL_SPRACHE",
    "JTL_K_BENUTZER",
    "JTL_K_FIRMA",

    # Config - TEMU
    "TEMU_APP_KEY",
    "TEMU_APP_SECRET",
    "TEMU_ACCESS_TOKEN",
    "TEMU_API_ENDPOINT"
]

# Version
__version__ = "0.1.0"
