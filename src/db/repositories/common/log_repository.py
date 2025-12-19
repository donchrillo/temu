"""Log Repository - Data Access Layer für strukturiertes Logging"""

from typing import Optional, Dict, List
from datetime import datetime, timedelta
from src.db.connection import get_db_connection
from src.services.logger import app_logger
from config.settings import DB_TOCI

class LogRepository:
    """Data Access Layer - Strukturiertes Logging in SQL Server"""
    
    def __init__(self, connection=None):
        self._conn = connection
    
    def _get_conn(self):
        """Hole Connection"""
        if self._conn:
            return self._conn
        return get_db_connection(DB_TOCI)
    
    def ensure_table_exists(self) -> bool:
        """✅ Erstelle Logs-Tabelle wenn nicht vorhanden"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Tabelle 1: scheduler_logs (Jobs)
            cursor.execute("""
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
            
            # Entfernt: Tabelle error_logs nicht mehr anlegen
            
            return True
        
        except Exception as e:
            app_logger.error(f"Table Creation Error: {e}", exc_info=True)
            return False
    
    def insert_log(self, job_id: str, job_type: str, level: str, message: str, 
                   status: str = None, duration_seconds: float = None, 
                   error_text: str = None) -> bool:
        """Speichere Log-Entry in Datenbank"""
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO [dbo].[scheduler_logs]
                (job_id, job_type, level, message, status, duration_seconds, error_text, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (job_id, job_type, level, message, status, duration_seconds, error_text))
            
            return True
        
        except Exception as e:
            app_logger.error(f"Insert Log Error: {e}", exc_info=True)
            return False
    
    def get_logs(self, job_id: str = None, level: str = None, 
                 limit: int = 100, offset: int = 0) -> List[Dict]:
        """Hole Logs mit optionalen Filtern"""
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Dynamische WHERE Clause
            where_clauses = []
            params = []
            
            if job_id:
                where_clauses.append("job_id = ?")
                params.append(job_id)
            
            if level:
                where_clauses.append("level = ?")
                params.append(level)
            
            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            # ✅ KORRIGIERT: OFFSET...FETCH NEXT statt TOP + OFFSET!
            # TOP und OFFSET können nicht zusammen verwendet werden in T-SQL
            query = f"""
                SELECT
                    [log_id], [job_id], [job_type], [level], [message],
                    [timestamp], [duration_seconds], [status], [error_text]
                FROM [dbo].[scheduler_logs]
                {where_sql}
                ORDER BY [timestamp] DESC, [log_id] DESC
                OFFSET ? ROWS
                FETCH NEXT ? ROWS ONLY
            """
            
            # Params: WHERE params + OFFSET + LIMIT
            params.extend([offset, limit])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                {
                    'log_id': row[0],
                    'job_id': row[1],
                    'job_type': row[2],
                    'level': row[3],
                    'message': row[4],
                    'timestamp': row[5].isoformat() if row[5] else None,
                    'duration_seconds': row[6],
                    'status': row[7],
                    'error_text': row[8]
                }
                for row in rows
            ]
        
        except Exception as e:
            app_logger.error(f"Get Logs Error: {e}", exc_info=True)
            return []
    
    def get_job_logs(self, job_id: str, limit: int = 50) -> List[str]:
        """Hole Logs für einen Job (einfaches Format für Dashboard)"""
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # ✅ KORRIGIERT: TOP (?) statt TOP ? in T-SQL!
            cursor.execute("""
                SELECT TOP (?)
                    [message]
                FROM [dbo].[scheduler_logs]
                WHERE job_id = ?
                ORDER BY [timestamp] DESC, [log_id] DESC
            """, (limit, job_id))
            
            rows = cursor.fetchall()
            # Neueste zuerst zurückgeben (keine Reverse)
            return [row[0] for row in rows]
        
        except Exception as e:
            app_logger.error(f"Get Job Logs Error: {e}", exc_info=True)
            return []
    
    def get_statistics(self, job_id: str = None, days: int = 7) -> Dict:
        """Hole Statistiken für Jobs"""
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            where_sql = f"WHERE timestamp >= DATEADD(day, -{days}, GETDATE())"
            if job_id:
                where_sql += f" AND job_id = '{job_id}'"
            
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total_runs,
                    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_runs,
                    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed_runs,
                    AVG(duration_seconds) as avg_duration,
                    MAX(duration_seconds) as max_duration,
                    MIN(duration_seconds) as min_duration
                FROM [dbo].[scheduler_logs]
                {where_sql}
            """)
            
            row = cursor.fetchone()
            
            if row:
                return {
                    'total_runs': row[0] or 0,
                    'successful_runs': row[1] or 0,
                    'failed_runs': row[2] or 0,
                    'avg_duration': round(row[3], 2) if row[3] else 0,
                    'max_duration': round(row[4], 2) if row[4] else 0,
                    'min_duration': round(row[5], 2) if row[5] else 0,
                    'success_rate': round(((row[1] or 0) / (row[0] or 1)) * 100, 1)
                }
            
            return {}
        
        except Exception as e:
            app_logger.error(f"Statistics Error: {e}", exc_info=True)
            return {}
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """Lösche alte Logs (älter als X Tage)"""
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM [dbo].[scheduler_logs]
                WHERE timestamp < DATEADD(day, ?, GETDATE())
            """, -days)
            
            deleted = cursor.rowcount
            app_logger.info(f"✓ {deleted} alte Logs gelöscht")
            return deleted
        
        except Exception as e:
            app_logger.error(f"Cleanup Error: {e}", exc_info=True)
            return 0
    
    # Entfernt: insert_error_log – Error-Logs werden nicht mehr unterstützt
    
    # Entfernt: get_error_logs – Error-Logs werden nicht mehr unterstützt
