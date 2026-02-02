"""
Database Utilities - Re-Export Layer

Stellt die bewährte src/db/ Funktionalität bereit:
- SQLAlchemy Engine mit Connection Pooling
- Context Manager für Transaktionen
- BaseRepository mit SQL Server 2100 Parameter Limit Handling
- Support für 2 Datenbanken (toci, eazybusiness)
"""

from src.db.connection import (
    get_engine,
    db_connect,
    get_db,
    close_all_engines,
    _parse_server,
    _build_connection_url
)

from src.db.repositories.base import BaseRepository

__all__ = [
    "get_engine",
    "db_connect",
    "get_db",
    "close_all_engines",
    "BaseRepository"
]
