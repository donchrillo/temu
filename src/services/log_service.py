"""Log Service - Zentrale Log-Verwaltung mit Console Capture"""

import io
import sys
import logging
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
from typing import Optional, List, Dict
from src.db.repositories.common.log_repository import LogRepository
from src.services.logger import app_logger

class LogService:
    """Verwaltet strukturiertes Logging"""
    
    def __init__(self):
        self.repo = LogRepository()
        self.repo.ensure_table_exists()
        self.current_job_id: Optional[str] = None
        self.current_job_type: Optional[str] = None
        self.log_buffer: List[str] = []
    
    def start_job_capture(self, job_id: str, job_type: str):
        """Starte Capturing für einen Job"""
        self.current_job_id = job_id
        self.current_job_type = job_type
        self.log_buffer = []
        
        self.log(job_id, job_type, "INFO", f"Job gestartet: {job_type}")
    
    def log(self, job_id: str, job_type: str, level: str, message: str,
            status: str = None, duration: float = None, error_text: str = None):
        """Speichere Log-Eintrag in DB und optional in app_logger"""
        
        # In Memory Buffer
        self.log_buffer.append(message)
        
        # In SQL Server
        self.repo.insert_log(
            job_id=job_id,
            job_type=job_type,
            level=level,
            message=message,
            status=status,
            duration_seconds=duration,
            error_text=error_text
        )
        # ERROR zusätzlich in app_logger
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
    
    def get_statistics(self, job_id: str = None, days: int = 7) -> Dict:
        """Hole Job-Statistiken"""
        return self.repo.get_statistics(job_id, days)
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """Lösche alte Logs"""
        return self.repo.cleanup_old_logs(days)

# Globale LogService Instanz
log_service = LogService()
