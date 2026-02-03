"""
Log Repository - SQLAlchemy + Raw SQL (Final)
Data Access Layer - Strukturiertes Logging in SQL Server
"""

from typing import Dict, List
# Lazy import to avoid circular dependency
def _get_log_service():
    from ...logging.log_service import log_service
    return log_service
from ..base import BaseRepository

class LogRepository(BaseRepository):
    """
    Data Access Layer - Strukturiertes Logging.
    Erbt von BaseRepository (Standard DB = TOCI).
    """

    def ensure_table_exists(self) -> bool:
        """Erstelle Logs-Tabelle wenn nicht vorhanden"""
        try:
            self._execute_stmt("""
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
            # Nutze print als Fallback
            print(f"CRITICAL DB ERROR (Log Table): {e}")
            return False

    def insert_log(self, job_id: str, job_type: str, level: str, message: str, 
                   status: str = None, duration_seconds: float = None, 
                   error_text: str = None) -> bool:
        """Speichere Log-Entry"""
        try:
            sql = """
                INSERT INTO [dbo].[scheduler_logs]
                (job_id, job_type, level, message, status, duration_seconds, error_text, timestamp)
                VALUES (:job_id, :job_type, :level, :message, :status, :duration_seconds, :error_text, GETDATE())
            """
            params = {
                "job_id": job_id,
                "job_type": job_type,
                "level": level,
                "message": message,
                "status": status,
                "duration_seconds": duration_seconds,
                "error_text": error_text
            }
            self._execute_stmt(sql, params)
            return True
        except Exception as e:
            print(f"LOG INSERT FAILED: {e}")
            return False

    def get_logs(self, job_id: str = None, level: str = None, 
                 limit: int = 100, offset: int = 0) -> List[Dict]:
        """Hole Logs mit optionalen Filtern (Read-Only)"""
        try:
            where_clauses = []
            params = {}
            
            if job_id:
                # job_id kommt vom Frontend bereits als LIKE-Pattern z.B. "temu_orders%"
                # Wenn es kein % enthält, fügen wir % hinzu für Präfix-Matching
                if '%' in job_id:
                    where_clauses.append("job_id LIKE :job_id_pattern")
                    params["job_id_pattern"] = job_id
                else:
                    where_clauses.append("job_id LIKE :job_id_pattern")
                    params["job_id_pattern"] = f"{job_id}%"
            
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
            
            rows = self._fetch_all(sql, params)
            return [dict(row._mapping) for row in rows]

        except Exception as e:
            _get_log_service().log("SYSTEM_ERROR", "log_repository", "ERROR", f"LogRepository get_logs: {e}")
            return []

    def get_recent_logs(self, job_id: str, limit: int = 100) -> List[Dict]:
        """Hole aktuelle Logs für einen Job"""
        try:
            sql = f"""
                SELECT TOP {limit} log_id, job_id, job_type, level, message, timestamp, 
                       duration_seconds, status, error_text
                FROM [dbo].[scheduler_logs]
                WHERE job_id = :job_id
                ORDER BY timestamp DESC
            """
            rows = self._fetch_all(sql, {"job_id": job_id})
            return [dict(row._mapping) for row in rows]

        except Exception as e:
            _get_log_service().log("SYSTEM_ERROR", "log_repository", "ERROR", f"LogRepository get_recent_logs: {e}")
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
            
            row = self._fetch_one(sql, {"job_id": job_id})
            return dict(row._mapping) if row else {}
            
        except Exception as e:
            _get_log_service().log("SYSTEM_ERROR", "log_repository", "ERROR", f"LogRepository get_job_stats: {e}")
            return {}

    def clean_old_logs(self, days: int = 30) -> int:
        """Lösche alte Logs"""
        try:
            sql = """
                DELETE FROM [dbo].[scheduler_logs]
                WHERE timestamp < DATEADD(day, -:days, GETDATE())
            """
            result = self._execute_stmt(sql, {"days": days})
            return result.rowcount
        except Exception as e:
            _get_log_service().log("SYSTEM_ERROR", "log_repository", "ERROR", f"LogRepository clean_old_logs: {e}")
            return 0