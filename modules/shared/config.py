"""
Configuration - Re-Export Layer

Stellt die zentrale Konfiguration aus config/settings.py bereit.
Alle Werte werden aus der .env Datei geladen.
"""

from config.settings import (
    # SQL Server Connection
    SQL_SERVER,
    SQL_USERNAME,
    SQL_PASSWORD,

    # Database Names
    DB_TOCI,
    DB_JTL,

    # Table Names
    TABLE_ORDERS,
    TABLE_ORDER_ITEMS,
    TABLE_XML_EXPORT,

    # JTL Configuration
    JTL_WAEHRUNG,
    JTL_SPRACHE,
    JTL_K_BENUTZER,
    JTL_K_FIRMA,

    # TEMU API
    TEMU_APP_KEY,
    TEMU_APP_SECRET,
    TEMU_ACCESS_TOKEN,
    TEMU_API_ENDPOINT
)

__all__ = [
    # SQL Server
    "SQL_SERVER",
    "SQL_USERNAME",
    "SQL_PASSWORD",

    # Databases
    "DB_TOCI",
    "DB_JTL",

    # Tables
    "TABLE_ORDERS",
    "TABLE_ORDER_ITEMS",
    "TABLE_XML_EXPORT",

    # JTL
    "JTL_WAEHRUNG",
    "JTL_SPRACHE",
    "JTL_K_BENUTZER",
    "JTL_K_FIRMA",

    # TEMU
    "TEMU_APP_KEY",
    "TEMU_APP_SECRET",
    "TEMU_ACCESS_TOKEN",
    "TEMU_API_ENDPOINT"
]
