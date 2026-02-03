"""
src/db/repositories/base.py
Basis-Klasse für alle Repositories (DRY Prinzip)
"""

from typing import Optional, Any, Union
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.sql.elements import TextClause
from ..connection import get_engine
from ...config.settings import DB_TOCI 

class BaseRepository:
    """
    Abstrakte Basisklasse für Repositories.
    Stellt Helper-Methoden für Transaktionen und Queries bereit.
    """
    
    def __init__(self, connection: Optional[Connection] = None, db_name: str = DB_TOCI):
        self._conn = connection
        self._db_name = db_name

    def _prepare_statement(self, sql: Union[str, TextClause]):
        """Helper: Wandelt Strings in TextClause um, lässt Objekte unverändert."""
        if isinstance(sql, str):
            return text(sql)
        return sql

    def _execute_stmt(self, sql: Union[str, TextClause], params: dict = None):
        """Helper für UPDATE/DELETE/INSERT (ohne Return Value)"""
        params = params or {}
        stmt = self._prepare_statement(sql)
        
        if self._conn:
            return self._conn.execute(stmt, params)
        else:
            engine = get_engine(self._db_name)
            with engine.connect() as conn:
                result = conn.execute(stmt, params)
                conn.commit()
                return result

    def _fetch_one(self, sql: Union[str, TextClause], params: dict = None):
        """Helper für SELECT Single Row"""
        params = params or {}
        stmt = self._prepare_statement(sql)
        
        if self._conn:
            return self._conn.execute(stmt, params).first()
        else:
            engine = get_engine(self._db_name)
            with engine.connect() as conn:
                return conn.execute(stmt, params).first()

    def _fetch_all(self, sql: Union[str, TextClause], params: dict = None):
        """Helper für SELECT Multi Row"""
        params = params or {}
        stmt = self._prepare_statement(sql)
        
        if self._conn:
            return self._conn.execute(stmt, params).all()
        else:
            engine = get_engine(self._db_name)
            with engine.connect() as conn:
                return conn.execute(stmt, params).all()