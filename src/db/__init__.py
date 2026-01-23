"""
Database Module Initialization
Exportiert die wichtigsten DB-Funktionen für einfacheren Zugriff.
"""
from src.db.connection import (
    get_engine,
    db_connect,
    close_all_engines,
    get_db  # Falls du die FastAPI Dependency auch exportieren willst
)

__all__ = ["get_engine", "db_connect", "close_all_engines", "get_db"]