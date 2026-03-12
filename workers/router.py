"""Job Management Router - Extraktion aus main.py

Enthält alle Job-bezogenen Endpoints:
- GET /api/jobs - Liste aller Jobs
- GET /api/jobs/{job_id} - Job Details
- POST /api/jobs/{job_id}/run-now - Job sofort triggern
- POST /api/jobs/{job_id}/schedule - Schedule ändern
- POST /api/jobs/{job_id}/toggle - Job enable/disable
"""

from fastapi import APIRouter, HTTPException

# Diese Imports werden zur Laufzeit aufgelöst (Lazy Import)
# um zirkuläre Imports zu vermeiden


def get_jobs_router(scheduler):
    """Erstellt den Job Management Router.
    
    Args:
        scheduler: Die SchedulerService Instanz
    
    Returns:
        APIRouter mit allen Job-Endpoints
    """
    router = APIRouter(prefix="/api/jobs", tags=["Jobs"])
    
    @router.get("")
    async def get_jobs():
        """Liste aller Jobs"""
        return scheduler.get_all_jobs()
    
    @router.get("/{job_id}")
    async def get_job(job_id: str):
        """Details zu einem Job"""
        return scheduler.get_job_status(job_id)
    
    @router.post("/{job_id}/run-now")
    async def trigger_job(
        job_id: str,
        parent_order_status: int = 2,
        days_back: int = 7,
        verbose: bool = False,
        mode: str = "quick"
    ):
        """Job sofort triggern"""
        scheduler.trigger_job_now(job_id, parent_order_status, days_back, verbose, mode)
        return {
            "status": "triggered",
            "job_id": job_id,
            "params": {
                "parent_order_status": parent_order_status,
                "days_back": days_back,
                "verbose": verbose,
                "mode": mode
            }
        }
    
    @router.post("/{job_id}/schedule")
    async def update_schedule(job_id: str, interval_minutes: int):
        """Job-Schedule ändern"""
        scheduler.update_job_schedule(job_id, interval_minutes)
        return {"status": "updated", "job_id": job_id, "interval_minutes": interval_minutes}
    
    @router.post("/{job_id}/toggle")
    async def toggle_job(job_id: str, enabled: bool):
        """Job enable/disable"""
        scheduler.toggle_job(job_id, enabled)
        return {"status": "toggled", "job_id": job_id, "enabled": enabled}
    
    return router