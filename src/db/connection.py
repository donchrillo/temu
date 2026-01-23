"""
src/db/connection.py
Database Connection Manager - SQL Server via SQLAlchemy Engine (echtes Pooling).

"""

import platform
from contextlib import contextmanager
from typing import Dict
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, Connection

from config.settings import SQL_SERVER, SQL_USERNAME, SQL_PASSWORD

# Engine Cache pro Datenbank
_engines: Dict[str, Engine] = {}


def _parse_server():
    """Split host/port from SQL_SERVER setting."""
    parts = SQL_SERVER.replace(':', ',').split(',')
    host = parts[0]
    port = parts[1] if len(parts) > 1 else '1433'
    return host, port


def _build_connection_url(database: str) -> str:
    """Build SQLAlchemy URL for pyodbc with driver differences (Linux vs Windows)."""
    host, port = _parse_server()
    driver = 'ODBC Driver 18 for SQL Server' if platform.system() == 'Linux' else 'SQL Server'

    driver_enc = quote_plus(driver)
    trust_param = 'TrustServerCertificate=yes'
    base = f"mssql+pyodbc://{quote_plus(SQL_USERNAME)}:{quote_plus(SQL_PASSWORD)}@{host}:{port}/{database}"
    return f"{base}?driver={driver_enc}&{trust_param}"


def _create_engine(database: str) -> Engine:
    url = _build_connection_url(database)
    engine = create_engine(
        url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        future=True,
    )
    return engine


def get_engine(database: str = 'toci') -> Engine:
    """Get or create a pooled SQLAlchemy Engine for the given database."""
    if database not in _engines:
        _engines[database] = _create_engine(database)
    return _engines[database]


@contextmanager
def db_connect(database: str = 'toci'):
    """Context manager for worker code: yields a Connection with transaction handling."""
    conn: Connection = get_engine(database).connect()
    trans = conn.begin()
    try:
        yield conn
        trans.commit()
    except Exception:
        trans.rollback()
        raise
    finally:
        conn.close()


def get_db(database: str = 'toci'):
    """FastAPI dependency yielding a Connection with transaction handling."""
    with db_connect(database) as conn:
        yield conn


def close_all_engines():
    """Dispose all engines and close pooled connections (e.g., on shutdown)."""
    global _engines
    for engine in _engines.values():
        try:
            engine.dispose()
        except Exception:
            pass
    _engines = {}
