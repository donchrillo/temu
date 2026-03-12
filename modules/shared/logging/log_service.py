"""Log Service - Zentrale Log-Verwaltung mit Console Capture"""

from typing import Optional, List, Dict
from ..database.repositories.common.log_repository import LogRepository
from .logger import app_logger

class LogService:
    """Verwaltet strukturiertes Logging"""
    
    def __init__(self):
        self.repo = LogRepository()
        self._table_checked = False
        self.current_job_id: Optional[str] = None
        self.current_job_type: Optional[str] = None
        self.log_buffer: List[str] = []
    
    def _ensure_table(self):
        """Lazy Table Check - nur einmal beim ersten Log-Aufruf"""
        if not self._table_checked:
            try:
                self.repo.ensure_table_exists()
                self._table_checked = True
            except Exception as e:
                app_logger.error(f"Log-Tabelle konnte nicht erstellt werden: {e}")
    
    def start_job_capture(self, job_id: str, job_type: str):
        """Starte Capturing für einen Job"""
        self.current_job_id = job_id
        self.current_job_type = job_type
        self.log_buffer = []
        
        self.log(job_id, job_type, "INFO", f"Job gestartet: {job_type}")
    
    def log(self, job_id: str, job_type: str, level: str, message: str,
            status: str = None, duration: float = None, error_text: str = None):
        """Speichere Log-Eintrag in DB und Fehler-Datei"""

        if not job_id or not job_type:
            raise ValueError("job_id und job_type muessen gesetzt sein")
        
        # Lazy Table Check beim ersten Aufruf
        self._ensure_table()
        
        # In Memory Buffer
        self.log_buffer.append(message)
        
        # In SQL Server: immer loggen (Integration in zentrale Umgebung)
        try:
            self.repo.insert_log(
                job_id=job_id,
                job_type=job_type,
                level=level,
                message=message,
                status=status,
                duration_seconds=duration,
                error_text=error_text
            )
        except Exception as e:
            # Falls DB-Logging fehlschlaegt, nur in app.log schreiben
            app_logger.error(f"DB-Logging fehlgeschlagen: {str(e)} | {message}")
        
        # ERROR-Level immer in zentrale app.log schreiben
        if level == "ERROR":
            app_logger.error(message)
    
    def end_job_capture(self, success: bool = True, duration: float = 0, error: str = None):
        """Beende Job Capturing"""
        
        if not self.current_job_id:
            return
        
        status = "SUCCESS" if success else "FAILED"
        self.log(
            self.current_job_id,
            self.current_job_type,
            "ERROR" if not success else "INFO",
            f"Job beendet: {status}",
            status=status,
            duration=duration,  # ✅ KORRIGIERT: duration statt duration_seconds
            error_text=error
        )
    
    def get_recent_logs(self, job_id: str, limit: int = 50) -> List[Dict]:
        """Hole letzte Logs für Job (für Dashboard)"""
        return self.repo.get_recent_logs(job_id, limit)
    
    def get_logs(self, job_id: str = None, level: str = None, 
                 limit: int = 100, offset: int = 0) -> List[Dict]:
        """Hole Logs mit Filtern"""
        return self.repo.get_logs(job_id, level, limit, offset)

    def get_logs_by_prefix(self, prefix: str, limit: int = 200, offset: int = 0) -> List[Dict]:
        """Hole Logs nach Prefix in job_id oder job_type."""
        return self.repo.get_logs_by_prefix(prefix, limit, offset)
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """Lösche alte Logs"""
        return self.repo.clean_old_logs(days)

    def get_statistics(self, job_id: str = None, days: int = 7) -> Dict:
        """Hole Log-Statistiken für einen Zeitraum.
        
        Args:
            job_id: Optional filter by specific job_id
            days: Number of days to look back (default 7)
        
        Returns:
            Dict mit Statistiken (total_logs, error_count, job_count, etc.)
        """
        try:
            self._ensure_table()
            
            # Nutze get_job_stats wenn job_id angegeben
            if job_id:
                stats = self.repo.get_job_stats(job_id)
                return {
                    "job_id": job_id,
                    "total_runs": stats.get("total_runs", 0),
                    "successful": stats.get("successful", 0),
                    "errors": stats.get("errors", 0),
                    "avg_duration": stats.get("avg_duration"),
                    "max_duration": stats.get("max_duration"),
                    "last_run": stats.get("last_run")
                }
            
            # Sonst: hol alle Logs für den Zeitraum und zähle
            logs = self.repo.get_logs(limit=10000)
            
            # Filter by days
            from datetime import datetime, timedelta
            cutoff = datetime.now() - timedelta(days=days)
            
            filtered_logs = [
                log for log in logs 
                if log.get("timestamp") and log.get("timestamp") >= cutoff
            ]
            
            error_count = sum(1 for log in filtered_logs if log.get("level") == "ERROR")
            success_count = sum(1 for log in filtered_logs if log.get("status") == "SUCCESS")
            unique_jobs = len(set(log.get("job_id") for log in filtered_logs if log.get("job_id")))
            
            return {
                "period_days": days,
                "total_logs": len(filtered_logs),
                "error_count": error_count,
                "success_count": success_count,
                "unique_jobs": unique_jobs
            }
        except Exception as e:
            app_logger.error(f"get_statistics failed: {e}")
            return {"error": str(e)}


# Globale LogService Instanz
log_service = LogService()
