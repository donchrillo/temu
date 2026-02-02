"""
Unified API Gateway - TEMU ERP System

Kombiniert alle Module:
- PDF-Reader (modules/pdf_reader)
- TEMU Integration (modules/temu)
- Job Scheduler (workers)
- Shared Services (modules/shared)

Läuft auf Port 8000
"""

import sys
import asyncio
from pathlib import Path
from typing import List
from fastapi import FastAPI, WebSocket, UploadFile, File
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

# Root zum Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent))

# ═══════════════════════════════════════════════════════════════
# Imports
# ═══════════════════════════════════════════════════════════════

from workers.worker_service import SchedulerService
from modules.shared import log_service, app_logger

# Module imports
from modules.pdf_reader import get_router as get_pdf_router
from modules.temu import get_router as get_temu_router, register_jobs as register_temu_jobs

# ═══════════════════════════════════════════════════════════════
# Scheduler
# ═══════════════════════════════════════════════════════════════

scheduler = SchedulerService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup und Shutdown Events"""

    try:
        # Lade Jobs aus Konfiguration
        scheduler.initialize_from_config()

        # Registriere TEMU-Jobs (falls noch nicht in Config)
        # register_temu_jobs(scheduler)

        scheduler.start()
        app_logger.info("Scheduler gestartet")
    except Exception as e:
        app_logger.error(f"Fehler beim Starten des Schedulers: {e}", exc_info=True)
        raise

    yield

    try:
        scheduler.stop()
        app_logger.info("Scheduler gestoppt")
    except Exception as e:
        app_logger.error(f"Fehler beim Stoppen des Schedulers: {e}", exc_info=True)

# ═══════════════════════════════════════════════════════════════
# FastAPI App
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="TEMU ERP System",
    description="Unified API Gateway für PDF-Processing & TEMU Integration",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════
# Module einbinden (include_router)
# ═══════════════════════════════════════════════════════════════

# PDF-Reader Modul
app.include_router(
    get_pdf_router(),
    prefix="/api/pdf",
    tags=["PDF Processor"]
)

# TEMU Modul
app.include_router(
    get_temu_router(),
    prefix="/api/temu",
    tags=["TEMU Integration"]
)

# ═══════════════════════════════════════════════════════════════
# Job Management Endpoints
# ═══════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health():
    """Gateway Health Check"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "modules": ["pdf-reader", "temu"]
    }

@app.get("/api/jobs")
async def get_jobs():
    """Liste aller Jobs"""
    return scheduler.get_all_jobs()

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Details zu einem Job"""
    return scheduler.get_job_status(job_id)

@app.post("/api/jobs/{job_id}/run-now")
async def trigger_job(
    job_id: str,
    parent_order_status: int = 2,
    days_back: int = 7,
    verbose: bool = False,
    log_to_db: bool = True,
    mode: str = "quick"
):
    """Job sofort triggern"""
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
    """Job-Schedule ändern"""
    scheduler.update_job_schedule(job_id, interval_minutes)
    return {"status": "updated", "job_id": job_id, "interval_minutes": interval_minutes}

@app.post("/api/jobs/{job_id}/toggle")
async def toggle_job(job_id: str, enabled: bool):
    """Job enable/disable"""
    scheduler.toggle_job(job_id, enabled)
    return {"status": "toggled", "job_id": job_id, "enabled": enabled}

# ═══════════════════════════════════════════════════════════════
# Log Endpoints
# ═══════════════════════════════════════════════════════════════

@app.get("/api/logs")
async def get_logs(job_id: str = None, level: str = None, limit: int = 100, offset: int = 0):
    """Logs mit Filtern"""
    return log_service.get_logs(job_id, level, limit, offset)

@app.get("/api/logs/stats")
async def get_log_stats(job_id: str = None, days: int = 7):
    """Log-Statistiken"""
    return log_service.get_statistics(job_id, days)

@app.get("/api/logs/export")
async def export_logs(job_id: str = None, format: str = "json", days: int = 7):
    """Export Logs als JSON/CSV"""
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

@app.post("/api/logs/cleanup")
async def cleanup_logs(days: int = 30):
    """Lösche alte Logs"""
    try:
        deleted = log_service.cleanup_old_logs(days)
        return {"status": "ok", "deleted": deleted}
    except Exception as e:
        app_logger.error(f"Cleanup Logs Fehler: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

# ═══════════════════════════════════════════════════════════════
# WebSocket für Live-Logs
# ═══════════════════════════════════════════════════════════════

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
            jobs_serializable = jsonable_encoder(jobs)
            await websocket.send_json({"type": "jobs_update", "data": jobs_serializable})

    except Exception as e:
        from starlette.websockets import WebSocketDisconnect
        from websockets.exceptions import ConnectionClosedOK, ConnectionClosed

        if isinstance(e, (WebSocketDisconnect, ConnectionClosedOK, ConnectionClosed)):
            return
        app_logger.error(f"WebSocket Fehler: {e}", exc_info=True)

    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

# ═══════════════════════════════════════════════════════════════
# Frontend Serving
# ═══════════════════════════════════════════════════════════════

frontend_dir = Path(__file__).resolve().parent / "frontend"

# Mount static files - DISABLED, using custom route instead
# app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

@app.get("/static/{filename}")
async def serve_module_static(filename: str):
    """Serve static files from modules or frontend"""
    allowed_extensions = {'.css', '.js', '.json', '.png', '.ico', '.svg', '.woff', '.woff2', '.ttf'}

    # Check if file extension is allowed
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(status_code=403, detail="File type not allowed")

    # Try module-specific files first (pdf.css, temu.js, etc.)
    base_dir = Path(__file__).parent

    # Check PDF module
    if filename.startswith('pdf.'):
        pdf_file = base_dir / "modules" / "pdf_reader" / "frontend" / filename
        if pdf_file.exists():
            return FileResponse(str(pdf_file))

    # Check TEMU module
    if filename.startswith('temu.'):
        temu_file = base_dir / "modules" / "temu" / "frontend" / filename
        if temu_file.exists():
            return FileResponse(str(temu_file))

    # Fallback to frontend directory
    frontend_file = frontend_dir / filename
    if frontend_file.exists():
        return FileResponse(str(frontend_file))

    raise HTTPException(status_code=404, detail=f"Static file not found: {filename}")

@app.get("/")
async def root():
    """Root Dashboard"""
    # Prüfe ob index-new.html existiert, sonst fallback auf index.html
    new_index = frontend_dir / "index-new.html"
    old_index = frontend_dir / "index.html"

    if new_index.exists():
        return FileResponse(str(new_index))
    elif old_index.exists():
        return FileResponse(str(old_index))
    else:
        return {
            "message": "TEMU ERP System Gateway",
            "version": "2.0.0",
            "modules": {
                "pdf": "/pdf",
                "temu": "/temu"
            },
            "docs": "/docs"
        }

@app.get("/pdf")
async def pdf_ui():
    """PDF-Reader UI - serviert direkt aus Modul"""
    pdf_html = Path(__file__).parent / "modules" / "pdf_reader" / "frontend" / "pdf.html"
    if not pdf_html.exists():
        raise HTTPException(status_code=404, detail="PDF Frontend not found")
    return FileResponse(str(pdf_html))

@app.get("/temu")
async def temu_ui():
    """TEMU Dashboard - serviert direkt aus Modul"""
    temu_html = Path(__file__).parent / "modules" / "temu" / "frontend" / "temu.html"
    if not temu_html.exists():
        raise HTTPException(status_code=404, detail="TEMU Frontend not found")
    return FileResponse(str(temu_html))

@app.get("/manifest.json")
async def get_manifest():
    """PWA Manifest"""
    file_path = frontend_dir / "manifest.json"
    if file_path.exists():
        return FileResponse(str(file_path))
    return {"error": "manifest.json nicht gefunden"}

@app.get("/{filename}")
async def serve_static(filename: str):
    """Serve CSS/JS/JSON aus frontend/"""
    file_path = frontend_dir / filename
    allowed_extensions = {'.css', '.js', '.html', '.json', '.png', '.ico', '.svg', '.woff', '.woff2', '.ttf'}
    if file_path.exists() and file_path.suffix.lower() in allowed_extensions:
        return FileResponse(str(file_path))

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

# ═══════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
