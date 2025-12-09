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
from dashboard.jobs import JobType

# Globaler Scheduler
scheduler = SchedulerService()

# Lifespan Context Manager (moderner als @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup und Shutdown Events"""
    
    # Startup
    print("🚀 Starte TEMU Worker...")
    
    # Definiere Standard-Jobs
    scheduler.add_job(
        JobType.SYNC_ORDERS,
        interval_minutes=15,
        description="Synchronisiere neue Aufträge von TEMU API"
    )
    
    scheduler.add_job(
        JobType.SYNC_INVENTORY,
        interval_minutes=5,
        description="Aktualisiere Bestandszahlen"
    )
    
    scheduler.add_job(
        JobType.FETCH_INVOICES,
        interval_minutes=60,
        description="Hole Rechnungen von TEMU"
    )
    
    scheduler.start()
    print("✓ Scheduler gestartet")
    
    yield
    
    # Shutdown
    print("🛑 Fahre TEMU Worker herunter...")
    scheduler.stop()
    print("✓ Scheduler gestoppt")

# Initialisiere FastAPI
app = FastAPI(
    title="TEMU Worker",
    version="1.0.0",
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
async def trigger_job(job_id: str):
    """Triggere Job sofort"""
    scheduler.trigger_job_now(job_id)
    return {"status": "triggered", "job_id": job_id}

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

# WebSocket für Live-Logs
connected_clients: list[WebSocket] = []

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket für Live-Log-Streaming"""
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        while True:
            # Sende aktuelle Jobs alle 2 Sekunden
            await asyncio.sleep(2)
            jobs = scheduler.get_all_jobs()
            
            # Konvertiere datetime zu ISO-String für JSON Serialisierung
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
        print(f"WebSocket Fehler: {e}")
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
        "api.main:app",
        "api.main:app",
        host="127.0.0.1",",
        port=8000,
        reload=Truee
    )
