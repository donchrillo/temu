"""Log Repository - SQLAlchemy + Raw SQL (Final)"""

from typing import Optional, Dict, List
from sqlalchemy import text
from sqlalchemy.engine import Connection
from src.services.logger import app_logger
from src.db.connection import get_engine
from config.settings import DB_TOCI

class LogRepository:
    """Data Access Layer - Strukturiertes Logging in SQL Server"""
    
    def __init__(self, connection: Optional[Connection] = None):
        self._conn = connection
    
    def _execute_sql(self, sql: str, params: dict = None):
        """
        Führt SQL aus. 
        - Nutzt injizierte Connection (ohne Commit, Teil einer Transaktion)
        - ODER erstellt eigene Connection (mit Commit, atomar)
        """
        if params is None:
            params = {}
            
        if self._conn:
            # Fall 1: Externe Transaktion (Service Layer steuert Commit)
            return self._conn.execute(text(sql), params)
        else:
            # Fall 2: Standalone (Auto-Commit nötig)
            engine = get_engine(DB_TOCI)
            with engine.connect() as conn:
                result = conn.execute(text(sql), params)
                conn.commit()  # WICHTIG!
                return result

    def ensure_table_exists(self) -> bool:
        """Erstelle Logs-Tabelle wenn nicht vorhanden"""
        try:
            self._execute_sql("""
                IF OBJECT_ID('dbo.scheduler_logs', 'U') IS NULL
                BEGIN
                    CREATE TABLE [dbo].[scheduler_logs] (
                        [log_id] INT PRIMARY KEY IDENTITY(1,1),
                        [job_id] VARCHAR(255) NOT NULL,
                        [job_type] VARCHAR(100) NOT NULL,
                        [level] VARCHAR(20) NOT NULL,
                        [message] NVARCHAR(MAX) NOT NULL,
                        [timestamp] DATETIME2 NOT NULL DEFAULT GETDATE(),
                        [duration_seconds] FLOAT NULL,
                        [status] VARCHAR(20) NULL,
                        [error_text] NVARCHAR(MAX) NULL,
                        
                        INDEX idx_job_id (job_id),
                        INDEX idx_timestamp (timestamp),
                        INDEX idx_level (level)
                    );
                END
            """)
            return True
        except Exception as e:
            app_logger.error(f"LogRepository ensure_table_exists: {e}", exc_info=True)
            return False
    
    def insert_log(self, job_id: str, job_type: str, level: str, message: str, 
                   status: str = None, duration_seconds: float = None, 
                   error_text: str = None) -> bool:
        """Speichere Log-Entry"""
        try:
            self._execute_sql("""
                INSERT INTO [dbo].[scheduler_logs]
                (job_id, job_type, level, message, status, duration_seconds, error_text, timestamp)
                VALUES (:job_id, :job_type, :level, :message, :status, :duration_seconds, :error_text, GETDATE())
            """, {
                "job_id": job_id,
                "job_type": job_type,
                "level": level,
                "message": message,
                "status": status,
                "duration_seconds": duration_seconds,
                "error_text": error_text
            })
            return True
        except Exception as e:
            app_logger.error(f"LogRepository insert_log: {e}", exc_info=True)
            return False
    
    def get_logs(self, job_id: str = None, level: str = None, 
                 limit: int = 100, offset: int = 0) -> List[Dict]:
        """Hole Logs mit optionalen Filtern (Read-Only)"""
        try:
            where_clauses = []
            params = {}
            
            if job_id:
                where_clauses.append("job_id = :job_id")
                params["job_id"] = job_id
            
            if level:
                where_clauses.append("level = :level")
                params["level"] = level
            
            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            params["limit"] = limit
            params["offset"] = offset
            
            sql = f"""
                SELECT log_id, job_id, job_type, level, message, timestamp, 
                       duration_seconds, status, error_text
                FROM [dbo].[scheduler_logs]
                {where_sql}
                ORDER BY timestamp DESC
                OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
            """
            
            # Für Selects brauchen wir kein Commit, aber wir nutzen der Einfachheit halber
            # die Logik: Wenn self._conn da ist -> nimm sie. Wenn nicht -> nimm Engine direkt (Connect).
            if self._conn:
                result = self._conn.execute(text(sql), params)
            else:
                with get_engine(DB_TOCI).connect() as conn:
                    result = conn.execute(text(sql), params)
                    # Hier Mappings holen, bevor Connection zugeht!
                    return [dict(row) for row in result.mappings().all()]

            return [dict(row) for row in result.mappings().all()]

        except Exception as e:
            app_logger.error(f"LogRepository get_logs: {e}", exc_info=True)
            return []
    
    def get_recent_logs(self, job_id: str, limit: int = 50) -> List[Dict]:
        """Hole aktuelle Logs für einen Job"""
        try:
            # MS SQL: TOP muss hardcodiert sein, kann nicht parametrisiert werden!
            sql = f"""
                SELECT TOP {limit} log_id, job_id, job_type, level, message, timestamp, 
                       duration_seconds, status, error_text
                FROM [dbo].[scheduler_logs]
                WHERE job_id = :job_id
                ORDER BY timestamp DESC
            """
            params = {"job_id": job_id}

            if self._conn:
                result = self._conn.execute(text(sql), params)
                return [dict(row) for row in result.mappings().all()]
            else:
                with get_engine(DB_TOCI).connect() as conn:
                    result = conn.execute(text(sql), params)
                    return [dict(row) for row in result.mappings().all()]

        except Exception as e:
            app_logger.error(f"LogRepository get_recent_logs: {e}", exc_info=True)
            return []
    
    def get_job_stats(self, job_id: str) -> Dict:
        """Hole Statistiken für einen Job"""
        try:
            sql = """
                SELECT 
                    COUNT(*) as total_runs,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN level = 'ERROR' THEN 1 ELSE 0 END) as errors,
                    AVG(duration_seconds) as avg_duration,
                    MAX(duration_seconds) as max_duration,
                    MAX(timestamp) as last_run
                FROM [dbo].[scheduler_logs]
                WHERE job_id = :job_id
            """
            # Helper logic inline für Read
            if self._conn:
                 result = self._conn.execute(text(sql), {"job_id": job_id})
            else:
                 with get_engine(DB_TOCI).connect() as conn:
                     result = conn.execute(text(sql), {"job_id": job_id})
                     row = result.first()
                     return dict(row._mapping) if row else {} # ._mapping für RowMapping Access

            row = result.first()
            return dict(row._mapping) if row else {}
            
        except Exception as e:
            app_logger.error(f"LogRepository get_job_stats: {e}", exc_info=True)
            return {}
    
    def clean_old_logs(self, days: int = 30) -> int:
        """Lösche alte Logs"""
        try:
            # Hier wieder execute_sql nutzen (weil Write Operation!)
            result = self._execute_sql("""
                DELETE FROM [dbo].[scheduler_logs]
                WHERE timestamp < DATEADD(day, -:days, GETDATE())
            """, {"days": days})
            return result.rowcount
        except Exception as e:
            app_logger.error(f"LogRepository clean_old_logs: {e}", exc_info=True)
            return 0