"""FastAPI Server - TEMU Worker Dashboard"""

import sys
from pathlib import Path
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.scheduler import SchedulerService
from src.services.log_service import log_service
from src.services.logger import app_logger

# Globaler Scheduler
scheduler = SchedulerService()

# Lifespan Context Manager (moderner als @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup und Shutdown Events"""
    
    try:
        # ✅ NEU: Lade Jobs aus gespeicherter Konfiguration
        scheduler.initialize_from_config()
        scheduler.start()
    except Exception as e:
        app_logger.error(f"Fehler beim Starten des Schedulers: {e}", exc_info=True)
        raise
    
    yield
    
    try:
        scheduler.stop()
    except Exception as e:
        app_logger.error(f"Fehler beim Stoppen des Schedulers: {e}", exc_info=True)

# Initialisiere FastAPI
app = FastAPI(
    title="TEMU Worker",
    version="1.0.1",
    lifespan=lifespan
)

# CORS aktivieren (für localhost Entwicklung)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API Endpoints

@app.get("/api/health")
async def health():
    """Health Check"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api/jobs")
async def get_jobs():
    """Gib alle Jobs zurück"""
    return scheduler.get_all_jobs()

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Gib einen Job zurück"""
    return scheduler.get_job_status(job_id)

@app.post("/api/jobs/{job_id}/run-now")
async def trigger_job(job_id: str, parent_order_status: int = 2, days_back: int = 7, 
                      verbose: bool = False, log_to_db: bool = True):
    """Triggere Job SOFORT mit optionalen Parametern"""
    scheduler.trigger_job_now(job_id, parent_order_status, days_back, verbose, log_to_db)
    return {
        "status": "triggered", 
        "job_id": job_id,
        "params": {
            "parent_order_status": parent_order_status,
            "days_back": days_back,
            "verbose": verbose,
            "log_to_db": log_to_db
        }
    }

@app.post("/api/jobs/{job_id}/schedule")
async def update_schedule(job_id: str, interval_minutes: int):
    """Ändere Job-Schedule"""
    scheduler.update_job_schedule(job_id, interval_minutes)
    return {"status": "updated", "job_id": job_id, "interval_minutes": interval_minutes}

@app.post("/api/jobs/{job_id}/toggle")
async def toggle_job(job_id: str, enabled: bool):
    """Enable/Disable Job"""
    scheduler.toggle_job(job_id, enabled)
    return {"status": "toggled", "job_id": job_id, "enabled": enabled}

# ===== LOG ENDPOINTS =====

@app.get("/api/logs")
async def get_logs(job_id: str = None, level: str = None, limit: int = 100, offset: int = 0):
    """Hole Logs mit Filtern"""
    return log_service.get_logs(job_id, level, limit, offset)

@app.get("/api/logs/export")
async def export_logs(job_id: str = None, format: str = "json", days: int = 7):
    """✅ Export Logs als JSON/CSV"""
    import csv
    from io import StringIO
    
    try:
        logs = log_service.get_logs(job_id=job_id, limit=10000)
        
        if format == "csv":
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=logs[0].keys() if logs else [])
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
        return {"status": "error", "message": str(e)}

# ===== NEU: ERROR LOGS ENDPOINT =====

@app.get("/api/logs/errors")
async def get_error_logs(limit: int = 100, offset: int = 0, level: str = None, days: int = 7):
    """Hole Error-Logs aus error_logs Tabelle"""
    from src.db.repositories.log_repository import LogRepository
    repo = LogRepository()
    return {
        "status": "ok",
        "data": repo.get_error_logs(limit=limit, offset=offset, level=level, days=days),
        "total": len(repo.get_error_logs(limit=10000, offset=0, level=level, days=days))
    }

@app.get("/api/logs/all")
async def get_all_logs(limit: int = 100, offset: int = 0, days: int = 7):
    """Hole Job-Logs UND Error-Logs kombiniert"""
    from src.db.repositories.log_repository import LogRepository
    repo = LogRepository()
    
    job_logs = repo.get_logs(limit=limit, offset=offset)
    error_logs = repo.get_error_logs(limit=limit, offset=offset, days=days)
    
    return {
        "status": "ok",
        "job_logs": job_logs,
        "error_logs": error_logs
    }

@app.get("/api/logs/stats")
async def get_log_stats(job_id: str = None, days: int = 7):
    """Hole Log-Statistiken"""
    return log_service.get_statistics(job_id, days)

@app.get("/api/logs/export")
async def export_logs(job_id: str = None, format: str = "json", days: int = 7):
    """✅ Export Logs als JSON/CSV"""
    import csv
    from io import StringIO
    
    try:
        logs = log_service.get_logs(job_id=job_id, limit=10000)
        
        if format == "csv":
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=logs[0].keys() if logs else [])
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
        return {"status": "error", "message": str(e)}

# ===== MAINTENANCE =====

@app.post("/api/logs/cleanup")
async def cleanup_logs(days: int = 30):
    """Lösche alte Logs"""
    try:
        deleted = log_service.cleanup_old_logs(days)
        return {"status": "ok", "deleted": deleted}
    except Exception as e:
        app_logger.error(f"Cleanup Logs Fehler: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

# WebSocket für Live-Logs
connected_clients: list[WebSocket] = []

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket für Live-Log-Streaming"""
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        while True:
            await asyncio.sleep(2)
            jobs = scheduler.get_all_jobs()
            
            jobs_serializable = []
            for job in jobs:
                job_dict = job.copy()
                if job_dict.get("status"):
                    status = job_dict["status"]
                    if status.get("last_run") and isinstance(status["last_run"], datetime):
                        status["last_run"] = status["last_run"].isoformat()
                    if status.get("next_run") and isinstance(status["next_run"], datetime):
                        status["next_run"] = status["next_run"].isoformat()
                jobs_serializable.append(job_dict)
            
            await websocket.send_json({"type": "jobs_update", "data": jobs_serializable})
    
    except Exception as e:
        # ✅ KORRIGIERT: Nur echte Fehler loggen, nicht WebSocket-Disconnects!
        error_msg = str(e)
        
        # WebSocket-Disconnects sind NORMAL - nicht loggen!
        if "ClientDisconnected" not in error_msg and "ConnectionClosed" not in error_msg:
            app_logger.error(f"WebSocket Fehler: {e}", exc_info=True)
    
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

# Serve Frontend
frontend_dir = Path(__file__).parent.parent / "frontend"

if (frontend_dir / "dist").exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir / "dist")), name="static")
    
    @app.get("/")
    async def root():
        """Serve index.html"""
        return FileResponse(str(frontend_dir / "dist" / "index.html"))
else:
    # Fallback wenn frontend/dist nicht existiert
    @app.get("/")
    async def root():
        """Einfache HTML Fallback-Seite"""
        return FileResponse(str(frontend_dir / "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
