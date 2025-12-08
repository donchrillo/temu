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

from dashboard.jobs import JobType, JobStatusEnum, JobConfig, JobSchedule

class SchedulerService:
    """Verwaltet alle geplanten Jobs"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.jobs: Dict[str, JobConfig] = {}
        self.job_logs: Dict[str, List[str]] = {}
        self.job_status: Dict[str, dict] = {}
    
    def add_job(self, job_type: JobType, interval_minutes: int, description: str):
        """Fügt einen neuen Job hinzu"""
        
        job_id = f"{job_type}_{int(datetime.now().timestamp())}"
        
        config = JobConfig(
            job_type=job_type,
            schedule=JobSchedule(
                interval_minutes=interval_minutes,
                enabled=True
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
            next_run_time=datetime.now()
        )
        
        return job_id
    
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
                    from main import run_full_workflow
                    result = await self._async_wrapper(run_full_workflow)
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
    
    async def _async_wrapper(self, sync_func):
        """Wrapper für synchrone Funktionen"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_func)
    
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
        """Triggere Job sofort"""
        job = self.scheduler.get_job(job_id)
        if job:
            job.reschedule(next_run_time=datetime.now())
    
    def update_job_schedule(self, job_id: str, interval_minutes: int):
        """Ändere Job-Schedule"""
        job = self.scheduler.get_job(job_id)
        if job:
            job.reschedule(trigger=IntervalTrigger(minutes=interval_minutes))
            self.jobs[job_id].schedule.interval_minutes = interval_minutes
    
    def toggle_job(self, job_id: str, enabled: bool):
        """Enable/Disable Job"""
        job = self.scheduler.get_job(job_id)
        if job:
            if enabled:
                job.resume()
            else:
                job.pause()
            self.jobs[job_id].schedule.enabled = enabled