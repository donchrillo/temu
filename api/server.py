"""FastAPI Server - TEMU Worker Dashboard"""

import sys
from pathlib import Path
from fastapi import FastAPI, WebSocket
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from workers.worker_service import SchedulerService
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
                      verbose: bool = False, log_to_db: bool = True, mode: str = "quick"):
    """Triggere Job SOFORT mit optionalen Parametern"""
    scheduler.trigger_job_now(job_id, parent_order_status, days_back, verbose, log_to_db, mode)
    return {
        "status": "triggered", 
        "job_id": job_id,
        "params": {
            "parent_order_status": parent_order_status,
            "days_back": days_back,
            "verbose": verbose,
            "log_to_db": log_to_db,
            "mode": mode
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
            # ✅ Nutze jsonable_encoder, um Enums/Datetimes serialisierbar zu machen
            jobs_serializable = jsonable_encoder(jobs)
            await websocket.send_json({"type": "jobs_update", "data": jobs_serializable})
    
    except Exception as e:
        # ✅ KORRIGIERT: Nur echte Fehler loggen, nicht normale Disconnects!
        from starlette.websockets import WebSocketDisconnect
        from uvicorn.protocols.utils import ClientDisconnected
        
        if not isinstance(e, (WebSocketDisconnect, ClientDisconnected)):
            # Echter Fehler - loggen!
            app_logger.error(f"WebSocket Fehler: {e}", exc_info=True)
    
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

# ===== SERVE FRONTEND (KORRIGIERT) =====

# Pfad absolut auflösen: /home/chx/temu/frontend
# .parent.parent, da server.py in /api/ liegt
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

# Mount static files (CSS, JS, etc.)
# Wichtig: directory muss als String übergeben werden
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

@app.get("/")
async def root():
    """Serve index.html"""
    return FileResponse(str(frontend_dir / "index.html"))

@app.get("/temu")
async def temu_dashboard():
    """Serve TEMU dashboard page"""
    return FileResponse(str(frontend_dir / "temu.html"))

@app.get("/manifest.json")
async def get_manifest():
    """Explizite Route für das Manifest"""
    file_path = frontend_dir / "manifest.json"
    if file_path.exists():
        return FileResponse(str(file_path))
    return {"error": f"manifest.json nicht gefunden in {frontend_dir}"}

@app.get("/{filename}")
async def serve_static(filename: str):
    """Serve CSS/JS/JSON direkt aus frontend/"""
    file_path = frontend_dir / filename
    # Erlaube alle gängigen Frontend-Dateien
    allowed_extensions = {'.css', '.js', '.html', '.json', '.png', '.ico', '.svg', '.woff', '.woff2', '.ttf'}
    if file_path.exists() and file_path.suffix.lower() in allowed_extensions:
        return FileResponse(str(file_path))
    
    # Debugging: Wenn Datei nicht gefunden wird, zeigen wir im JSON, wo gesucht wurde
    return {
        "error": "File not found", 
        "requested_file": filename,
        "searched_in": str(frontend_dir)
    }

@app.get("/icons/{filename}")
async def serve_icons(filename: str):
    """Serve Icons aus frontend/icons/"""
    file_path = frontend_dir / "icons" / filename
    allowed_extensions = {'.png', '.svg', '.ico'}
    if file_path.exists() and file_path.suffix.lower() in allowed_extensions:
        return FileResponse(str(file_path))
    
    return {
        "error": "Icon not found",
        "requested_file": filename,
        "searched_in": str(frontend_dir / "icons")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
