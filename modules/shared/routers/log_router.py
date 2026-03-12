"""Log Router - Extraktion aus main.py

Enthält alle Log-bezogenen Endpoints:
- GET /api/logs - Logs mit Filtern
- GET /api/logs/stats - Log-Statistiken
- GET /api/logs/export - Export Logs als JSON/CSV
- POST /api/logs/cleanup - Alte Logs löschen
"""

import csv
from io import StringIO
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from modules.shared import log_service, app_logger


def get_log_router() -> APIRouter:
    """Erstellt den Log Router.
    
    Returns:
        APIRouter mit allen Log-Endpoints
    """
    router = APIRouter(prefix="/api/logs", tags=["Logs"])
    
    @router.get("")
    async def get_logs(
        job_id: Optional[str] = Query(None, description="Filter by job_id"),
        level: Optional[str] = Query(None, description="Filter by log level"),
        limit: int = Query(100, ge=1, le=10000),
        offset: int = Query(0, ge=0)
    ):
        """Logs mit Filtern"""
        return log_service.get_logs(job_id, level, limit, offset)
    
    @router.get("/stats")
    async def get_log_stats(
        job_id: Optional[str] = Query(None),
        days: int = Query(7, ge=1, le=365)
    ):
        """Log-Statistiken"""
        return log_service.get_statistics(job_id, days)
    
    @router.get("/export")
    async def export_logs(
        job_id: Optional[str] = Query(None),
        format: str = Query("json", regex="^(json|csv)$"),
        days: int = Query(7, ge=1, le=365)
    ):
        """Export Logs als JSON/CSV"""
        try:
            logs = log_service.get_logs(job_id=job_id, limit=10000)

            if format == "csv":
                output = StringIO()
                fieldnames = logs[0].keys() if logs else []
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(logs)

                return {
                    "status": "ok",
                    "format": "csv",
                    "data": output.getvalue()
                }

            return {
                "status": "ok",
                "format": "json",
                "data": logs
            }
        except Exception as e:
            app_logger.error(f"Export Logs Fehler: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/cleanup")
    async def cleanup_logs(days: int = 30):
        """Lösche alte Logs"""
        try:
            deleted = log_service.cleanup_old_logs(days)
            return {"status": "ok", "deleted": deleted}
        except Exception as e:
            app_logger.error(f"Cleanup Logs Fehler: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    return router