"""APScheduler Service - Job Management"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import Dict, List
import asyncio
import sys
from pathlib import Path

from workers.workers_config import WorkersConfig
from workers.job_models import JobType, JobStatusEnum, JobConfig, JobSchedule  # ← KORRIGIERT: job_models statt jobs!
from modules.shared.logging.log_service import log_service


class SchedulerService:
    """Verwaltet alle geplanten Jobs"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.jobs: Dict[str, JobConfig] = {}
        self.job_logs: Dict[str, List[str]] = {}
        self.job_status: Dict[str, dict] = {}
    
    def initialize_from_config(self):
        """✅ NEU: Lade Jobs aus gespeicherter Konfiguration"""
        job_configs = WorkersConfig.load_jobs()
        
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
            args=[job_id, 2, 7, False, True, "quick"],  # ← Standard-Parameter + mode!
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
                       log_to_db: bool = True, mode: str = "quick"):
        """✅ Mit strukturiertem Logging in SQL Server"""
        
        start_time = datetime.now()
        self.job_status[job_id]["status"] = JobStatusEnum.RUNNING
        job_type = self.jobs[job_id].job_type
        
        # ✅ Starte Log-Capturing in SQL Server
        log_service.start_job_capture(job_id, job_type.value)
        
        try:
            # Füge root-Ordner zum Path hinzu (BEVOR wir importieren!)
            root_path = Path(__file__).parent.parent
            if str(root_path) not in sys.path:
                sys.path.insert(0, str(root_path))

            # Führe entsprechenden Job aus (Workflows loggen selbst strukturiert)
            if job_type == JobType.SYNC_ORDERS:
                from modules.temu.services.order_workflow_service import OrderWorkflowService
                service = OrderWorkflowService()
                result = await self._async_wrapper(
                    service.run_complete_workflow,
                    parent_order_status=parent_order_status,
                    days_back=days_back,
                    verbose=verbose
                )
                # Ergebnis-Zusammenfassung
                log_service.log(job_id, job_type.value, "INFO", f"Job Ergebnis: {result}")

            elif job_type == JobType.SYNC_INVENTORY:
                from modules.temu.services.inventory_workflow_service import InventoryWorkflowService
                service = InventoryWorkflowService()
                result = await self._async_wrapper(
                    service.run_complete_workflow,
                    mode=mode,
                    verbose=verbose
                )
                log_service.log(job_id, job_type.value, "INFO", f"Inventory Sync abgeschlossen (mode={mode})")

            elif job_type == JobType.FETCH_INVOICES:
                log_service.log(job_id, job_type.value, "INFO", "Rechnungs-Fetch noch nicht implementiert")
            
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
                        log_to_db: bool = True, mode: str = "quick"):
        """Triggere Job SOFORT mit optionalen Parametern"""
        job = self.scheduler.get_job(job_id)
        if job:
            # Speichere alte Konfiguration
            trigger = job.trigger
            func = job.func
            
            # Entferne alten Job
            self.scheduler.remove_job(job_id)
            
            # Füge neu hinzu mit sofortigem Start UND neuen Parametern!
            self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                args=[job_id, parent_order_status, days_back, verbose, log_to_db, mode],  # ← NEU: mode hinzugefügt!
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
        
        WorkersConfig.save_jobs(jobs_list)
        # ✅ Kein Print mehr - erfolgreiche Speicherung wird im Log_Service geloggt