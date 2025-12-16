"""APScheduler Service - Job Management"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import Dict, List
import asyncio
import io
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from dashboard.scheduler_config import SchedulerConfig
from dashboard.job_models import JobType, JobStatusEnum, JobConfig, JobSchedule  # ← KORRIGIERT: job_models statt jobs!
from src.services.log_service import log_service
from src.services.logger import app_logger

class SchedulerService:
    """Verwaltet alle geplanten Jobs"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.jobs: Dict[str, JobConfig] = {}
        self.job_logs: Dict[str, List[str]] = {}
        self.job_status: Dict[str, dict] = {}
    
    def initialize_from_config(self):
        """✅ NEU: Lade Jobs aus gespeicherter Konfiguration"""
        job_configs = SchedulerConfig.load_jobs()
        
        for job_config in job_configs:
            self.add_job(
                job_type=JobType(job_config['job_type']),
                interval_minutes=job_config['interval_minutes'],
                description=job_config['description'],
                enabled=job_config.get('enabled', True)
            )
    
    def add_job(self, job_type: JobType, interval_minutes: int, description: str, enabled: bool = True):
        """Fügt einen neuen Job hinzu"""
        
        # VORHER:
        # job_id = f"{job_type}_{int(datetime.now().timestamp())}"
        
        # NACHHER: ← .value nutzen!
        job_id = f"{job_type.value}_{int(datetime.now().timestamp())}"
        
        config = JobConfig(
            job_type=job_type,
            schedule=JobSchedule(
                interval_minutes=interval_minutes,
                enabled=enabled
            ),
            description=description
        )
        
        self.jobs[job_id] = config
        self.job_logs[job_id] = []
        self.job_status[job_id] = {
            "status": JobStatusEnum.IDLE,
            "last_run": None,
            "next_run": None,
            "last_error": None,
            "last_duration": None
        }
        
        # Registriere im Scheduler
        self.scheduler.add_job(
            self._run_job,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=job_id,
            args=[job_id, 2, 7, False, True],  # ← Standard-Parameter!
            next_run_time=datetime.now() if enabled else None,
            misfire_grace_time=None,  # ✅ Ignoriere verpasste Zyklen komplett
            coalesce=True,  # ✅ Springe verpasste Ausführungen
            max_instances=1  # ✅ Nur 1 Instanz gleichzeitig
        )
        
        if not enabled:
            job = self.scheduler.get_job(job_id)
            if job:
                job.pause()
        
        return job_id
    
    async def _async_wrapper(self, sync_func, *args, **kwargs):
        """Wrapper für synchrone Funktionen mit Arguments"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: sync_func(*args, **kwargs))
    
    async def _run_job(self, job_id: str, parent_order_status: int = 2, 
                       days_back: int = 7, verbose: bool = False, 
                       log_to_db: bool = True):
        """✅ Mit strukturiertem Logging in SQL Server"""
        
        start_time = datetime.now()
        self.job_status[job_id]["status"] = JobStatusEnum.RUNNING
        job_type = self.jobs[job_id].job_type
        
        # ✅ Starte Log-Capturing in SQL Server
        log_service.start_job_capture(job_id, job_type.value)
        
        try:
            # Capture stdout/stderr
            log_buffer = io.StringIO()
            
            with redirect_stdout(log_buffer), redirect_stderr(log_buffer):
                job_type = self.jobs[job_id].job_type
                
                # Füge root-Ordner zum Path hinzu
                root_path = Path(__file__).parent.parent
                if str(root_path) not in sys.path:
                    sys.path.insert(0, str(root_path))
                
                app_logger.info(f"[{start_time.isoformat()}] Job gestartet: {job_type}")
                
                # Führe entsprechenden Job aus
                if job_type == JobType.SYNC_ORDERS:
                    #from main import run_full_workflow_refactored
                    # neuer workflow
                    from workflows.temu_orders import run_temu_orders
                    result = await self._async_wrapper(
                        run_temu_orders,
                        parent_order_status=parent_order_status,  # ← Parameter!
                        days_back=days_back,                      # ← Parameter!
                        verbose=verbose                           # ← Parameter!
                    )
                    app_logger.info(f"Job Ergebnis: {result}")
                elif job_type == JobType.SYNC_INVENTORY:
                    app_logger.info("ℹ Inventur-Sync noch nicht implementiert")
                elif job_type == JobType.FETCH_INVOICES:
                    app_logger.info("ℹ Rechnungs-Fetch noch nicht implementiert")
            
            # ✅ Speichere Logs in SQL Server
            logs = log_buffer.getvalue().split('\n')
            for log_line in logs:
                if log_line.strip():
                    # Bestimme Level
                    level = "INFO"
                    if "✗" in log_line or "Fehler" in log_line:
                        level = "ERROR"
                    elif "⚠" in log_line:
                        level = "WARNING"
                    
                    log_service.log(job_id, job_type.value, level, log_line)
            
            # Erfolg
            duration = (datetime.now() - start_time).total_seconds()
            self.job_status[job_id]["status"] = JobStatusEnum.SUCCESS
            self.job_status[job_id]["last_duration"] = duration
            
            # ✅ Speichere Success-Status in DB
            log_service.end_job_capture(success=True, duration=duration)
            
        except Exception as e:
            import traceback
            self.job_status[job_id]["status"] = JobStatusEnum.FAILED
            self.job_status[job_id]["last_error"] = str(e)
            
            # ✅ Speichere Error in DB + Logger
            log_service.end_job_capture(success=False, duration=(datetime.now() - start_time).total_seconds(), error=str(e))
            log_service.log(job_id, job_type.value, "ERROR", traceback.format_exc())
            app_logger.error(f"Job {job_id} fehlgeschlagen: {e}", exc_info=True)
        
        finally:
            # ✅ Aktualisiere recent_logs aus DB
            self.job_logs[job_id] = log_service.get_recent_logs(job_id, 50)
            
            self.job_status[job_id]["last_run"] = start_time
            job = self.scheduler.get_job(job_id)
            if job:
                # ✅ KORRIGIERT: Berechne next_run neu basierend auf JETZT + Intervall!
                interval_minutes = self.jobs[job_id].schedule.interval_minutes
                from datetime import timedelta
                next_run = datetime.now() + timedelta(minutes=interval_minutes)
                
                # Neuplanen mit aktueller Zeit
                job.reschedule(trigger=IntervalTrigger(minutes=interval_minutes), next_run_time=next_run)
                self.job_status[job_id]["next_run"] = next_run
    
    def start(self):
        """Starte Scheduler"""
        self.scheduler.start()
    
    def stop(self):
        """Stoppe Scheduler"""
        self.scheduler.shutdown()
    
    def get_job_status(self, job_id: str) -> dict:
        """Gib Job-Status zurück"""
        if job_id not in self.jobs:
            return {"error": "Job nicht gefunden"}
        
        return {
            "job_id": job_id,
            "config": self.jobs[job_id].dict(),
            "status": self.job_status[job_id],
            "recent_logs": self.job_logs[job_id][-20:]
        }
    
    def get_all_jobs(self) -> List[dict]:
        """Gib alle Jobs zurück"""
        return [self.get_job_status(job_id) for job_id in self.jobs.keys()]
    
    def trigger_job_now(self, job_id: str, parent_order_status: int = 2, 
                        days_back: int = 7, verbose: bool = False, 
                        log_to_db: bool = True):
        """Triggere Job SOFORT mit optionalen Parametern"""
        job = self.scheduler.get_job(job_id)
        if job:
            # Speichere alte Konfiguration
            trigger = job.trigger
            func = job.func
            args = job.args
            
            # Entferne alten Job
            self.scheduler.remove_job(job_id)
            
            # Füge neu hinzu mit sofortigem Start UND neuen Parametern!
            self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                args=[job_id, parent_order_status, days_back, verbose, log_to_db],  # ← NEU!
                next_run_time=datetime.now()
            )
    
    def update_job_schedule(self, job_id: str, interval_minutes: int):
        """Ändere Job-Schedule und speichere"""
        job = self.scheduler.get_job(job_id)
        if job:
            job.reschedule(trigger=IntervalTrigger(minutes=interval_minutes))
            self.jobs[job_id].schedule.interval_minutes = interval_minutes
            
            # ✅ NEU: Speichere in Config-Datei!
            self._save_config()
    
    def toggle_job(self, job_id: str, enabled: bool):
        """Enable/Disable Job und speichere"""
        job = self.scheduler.get_job(job_id)
        if job:
            if enabled:
                job.resume()
            else:
                job.pause()
            self.jobs[job_id].schedule.enabled = enabled
            
            # ✅ NEU: Speichere in Config-Datei!
            self._save_config()
    
    def _save_config(self):
        """✅ NEU: Speichere aktuelle Job-Konfigurationen"""
        jobs_list = []
        
        for job_id, job_config in self.jobs.items():
            jobs_list.append({
                'job_type': job_config.job_type.value,
                'interval_minutes': job_config.schedule.interval_minutes,
                'enabled': job_config.schedule.enabled,
                'description': job_config.description
            })
        
        SchedulerConfig.save_jobs(jobs_list)
        # ✅ Kein Print mehr - erfolgreiche Speicherung wird im Log_Service geloggt