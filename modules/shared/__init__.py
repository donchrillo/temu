"""
Shared Module - Zentrale Infrastruktur für alle Module

Dieses Modul bietet gemeinsame Funktionen für Database, Logging, Config und Connectors.
Alle Module importieren von hier, nicht direkt von den Untermodulen.

Verwendung in neuen Modulen:
    from modules.shared import db_connect, BaseRepository, log_service
    from modules.shared.config.settings import TEMU_APP_KEY
"""

# Database (lokale Imports aus modules/shared/database/)
from .database.connection import get_engine, db_connect, get_db, close_all_engines
from .database.repositories.base import BaseRepository

# Logging (lokale Imports aus modules/shared/logging/)
from .logging import create_module_logger, log_service, app_logger

# Config (lokale Imports aus modules/shared/config/)
from .config.settings import (
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
__version__ = "1.0.0"
