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

from dashboard.config import SchedulerConfig
from dashboard.jobs import JobType, JobStatusEnum, JobConfig, JobSchedule

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
        
        job_id = f"{job_type}_{int(datetime.now().timestamp())}"
        
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
            args=[job_id],
            next_run_time=datetime.now() if enabled else None
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
    
    async def _run_job(self, job_id: str):
        """Führt einen Job aus und captured Logs"""
        
        start_time = datetime.now()
        self.job_status[job_id]["status"] = JobStatusEnum.RUNNING
        
        # Capture stdout/stderr
        log_buffer = io.StringIO()
        
        try:
            with redirect_stdout(log_buffer), redirect_stderr(log_buffer):
                job_type = self.jobs[job_id].job_type
                
                # Füge root-Ordner zum Path hinzu
                root_path = Path(__file__).parent.parent
                if str(root_path) not in sys.path:
                    sys.path.insert(0, str(root_path))
                
                print(f"[{start_time.isoformat()}] Job gestartet: {job_type}")
                
                # Führe entsprechenden Job aus
                if job_type == JobType.SYNC_ORDERS:
                    # ✅ KORRIGIERT: Nutze _async_wrapper mit kwargs!
                    from main import run_full_workflow_refactored
                    result = await self._async_wrapper(
                        run_full_workflow_refactored,
                        parent_order_status=2,
                        days_back=7
                    )
                    print(f"Job Ergebnis: {result}")
                elif job_type == JobType.SYNC_INVENTORY:
                    print("ℹ Inventur-Sync noch nicht implementiert")
                elif job_type == JobType.FETCH_INVOICES:
                    print("ℹ Rechnungs-Fetch noch nicht implementiert")
            
            # Erfolg
            duration = (datetime.now() - start_time).total_seconds()
            self.job_status[job_id]["status"] = JobStatusEnum.SUCCESS
            self.job_status[job_id]["last_duration"] = duration
            print(f"[Job] ✓ Erfolgreich (Dauer: {duration:.1f}s)")
            
        except Exception as e:
            # Fehler - mit vollständigem Traceback
            import traceback
            self.job_status[job_id]["status"] = JobStatusEnum.FAILED
            self.job_status[job_id]["last_error"] = str(e)
            error_msg = f"\n✗ Job Fehler: {e}\n{traceback.format_exc()}"
            log_buffer.write(error_msg)
            print(error_msg)
        
        finally:
            # Speichere Logs
            logs = log_buffer.getvalue().split('\n')
            self.job_logs[job_id] = [l for l in logs if l.strip()][-100:]
            
            self.job_status[job_id]["last_run"] = start_time
            job = self.scheduler.get_job(job_id)
            if job:
                self.job_status[job_id]["next_run"] = job.next_run_time
    
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
    
    def trigger_job_now(self, job_id: str):
        """Triggere Job SOFORT (nicht nur reschedule)"""
        job = self.scheduler.get_job(job_id)
        if job:
            # ✅ WICHTIG: remove_job + add_job mit SOFORT Lauf!
            # Das zwingt den Scheduler sofort auszuführen!
            
            # Speichere alte Konfiguration
            trigger = job.trigger
            func = job.func
            args = job.args
            
            # Entferne alten Job
            self.scheduler.remove_job(job_id)
            
            # Füge neu hinzu mit sofortigem Start
            self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                args=args,
                next_run_time=datetime.now()  # ← JETZT ausführen!
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
        print("✓ Job-Konfiguration gespeichert")