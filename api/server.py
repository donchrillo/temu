"""FastAPI Server - TEMU Worker Dashboard"""

import sys
import time
from pathlib import Path
from typing import List
from fastapi import FastAPI, WebSocket, UploadFile, File
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
from src.services import app_logger
from src.modules.pdf_reader.config import (
    ORDNER_EINGANG_RECHNUNGEN,
    ORDNER_EINGANG_WERBUNG,
    ORDNER_AUSGANG,
    ORDNER_LOG,
    ensure_directories,
)
from src.modules.pdf_reader.werbung_extraction_service import extract_and_save_first_page
from src.modules.pdf_reader.werbung_service import process_ad_pdfs
from src.modules.pdf_reader.rechnungen_service import process_rechnungen
from src.modules.pdf_reader.config import ORDNER_EINGANG_RECHNUNGEN as _DIR_INV
from src.modules.pdf_reader.config import ORDNER_EINGANG_WERBUNG as _DIR_ADS
from src.modules.pdf_reader.config import TMP_ORDNER as _DIR_TMP

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

# ===== PDF READER ENDPOINTS =====

async def _save_uploads(files: List[UploadFile], target_dir: Path) -> list[str]:
    """Speichere Uploads in das Zielverzeichnis."""
    ensure_directories()
    saved = []
    target_dir.mkdir(parents=True, exist_ok=True)
    for f in files:
        dest = target_dir / f.filename
        content = await f.read()
        with open(dest, "wb") as out:
            out.write(content)
        saved.append(str(dest))
    return saved


@app.post("/api/pdf/werbung/upload")
async def upload_werbung(files: List[UploadFile] = File(default=[]), process: bool = False):
    job_id = f"pdf_werbung_{int(time.time())}"
    try:
        saved_paths = await _save_uploads(files, ORDNER_EINGANG_WERBUNG)
        log_service.log(job_id, "pdf_upload", "INFO", f"{len(saved_paths)} Werbung-PDFs gespeichert")

        result = None
        extracted = []
        if process:
            extracted = extract_and_save_first_page()
            result = process_ad_pdfs()
            log_service.log(job_id, "pdf_upload", "INFO", f"Werbung verarbeitet: {len(result) if hasattr(result, '__len__') else 0} Einträge")

        return {
            "status": "ok",
            "saved": saved_paths,
            "extracted": [str(p) for p in extracted],
            "processed": bool(result is not None)
        }
    except Exception as e:
        app_logger.error(f"Werbung Upload Fehler: {e}", exc_info=True)
        log_service.log(job_id, "pdf_upload", "ERROR", f"Werbung Upload Fehler: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/pdf/rechnungen/upload")
async def upload_rechnungen(files: List[UploadFile] = File(default=[]), process: bool = False):
    job_id = f"pdf_rechnungen_{int(time.time())}"
    try:
        saved_paths = await _save_uploads(files, ORDNER_EINGANG_RECHNUNGEN)
        log_service.log(job_id, "pdf_upload", "INFO", f"{len(saved_paths)} Rechnungs-PDFs gespeichert")

        result = None
        if process:
            result = process_rechnungen()
            log_service.log(job_id, "pdf_upload", "INFO", f"Rechnungen verarbeitet: {len(result) if hasattr(result, '__len__') else 0} Einträge")

        return {
            "status": "ok",
            "saved": saved_paths,
            "processed": bool(result is not None)
        }
    except Exception as e:
        app_logger.error(f"Rechnungen Upload Fehler: {e}", exc_info=True)
        log_service.log(job_id, "pdf_upload", "ERROR", f"Rechnungen Upload Fehler: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/pdf/werbung/extract")
async def extract_werbung():
    """Extrahiere erste Seiten von bereits hochgeladenen Werbungs-PDFs."""
    job_id = f"pdf_extract_{int(time.time())}"
    try:
        extracted = extract_and_save_first_page()
        log_service.log(job_id, "pdf_upload", "INFO", f"Extrahiert: {len(extracted)} Dateien")
        return {
            "status": "ok",
            "extracted": [str(p) for p in extracted]
        }
    except Exception as e:
        app_logger.error(f"Werbung Extract Fehler: {e}", exc_info=True)
        log_service.log(job_id, "pdf_upload", "ERROR", f"Extract Fehler: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/pdf/werbung/process")
async def process_werbung():
    """Verarbeite extrahierte Werbungs-PDFs zu Excel."""
    job_id = f"pdf_process_{int(time.time())}"
    try:
        result = process_ad_pdfs()
        log_service.log(job_id, "pdf_upload", "INFO", f"Verarbeitet: {len(result) if hasattr(result, '__len__') else 0} Einträge")
        return {
            "status": "ok",
            "processed": True,
            "count": len(result) if hasattr(result, '__len__') else 0
        }
    except Exception as e:
        app_logger.error(f"Werbung Process Fehler: {e}", exc_info=True)
        log_service.log(job_id, "pdf_upload", "ERROR", f"Process Fehler: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/pdf/rechnungen/process")
async def process_rechnungen_endpoint():
    """Verarbeite Rechnungs-PDFs zu Excel."""
    job_id = f"pdf_process_{int(time.time())}"
    try:
        result = process_rechnungen()
        log_service.log(job_id, "pdf_upload", "INFO", f"Verarbeitet: {len(result) if hasattr(result, '__len__') else 0} Einträge")
        return {
            "status": "ok",
            "processed": True,
            "count": len(result) if hasattr(result, '__len__') else 0
        }
    except Exception as e:
        app_logger.error(f"Rechnungen Process Fehler: {e}", exc_info=True)
        log_service.log(job_id, "pdf_upload", "ERROR", f"Process Fehler: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/api/pdf/logs/{logfile}")
async def get_pdf_log(logfile: str):
    """Serviere PDF-Reader Logfiles (werbung_read.log, werbung_extraction.log, rechnung_read.log)."""
    ensure_directories()
    allowed_files = {"werbung_read.log", "werbung_extraction.log", "rechnung_read.log"}
    if logfile not in allowed_files:
        return {"status": "error", "message": "Invalid logfile"}
    
    log_path = ORDNER_LOG / logfile
    if not log_path.exists():
        return {"status": "empty", "content": ""}
    
    try:
        content = log_path.read_text(encoding="utf-8")
        return {"status": "ok", "content": content}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/pdf/werbung/result")
async def get_werbung_result():
    excel_path = ORDNER_AUSGANG / "werbung.xlsx"
    if excel_path.exists():
        return FileResponse(str(excel_path), filename="werbung.xlsx")
    return {"status": "not_found"}


@app.get("/api/pdf/rechnungen/result")
async def get_rechnungen_result():
    excel_path = ORDNER_AUSGANG / "rechnungen.xlsx"
    if excel_path.exists():
        return FileResponse(str(excel_path), filename="rechnungen.xlsx")
    return {"status": "not_found"}


def _dir_status(dir_path: Path) -> dict:
    files = [p for p in dir_path.glob("*") if p.is_file()]
    return {"path": str(dir_path), "count": len(files), "files": [p.name for p in files[:5]]}


@app.get("/api/pdf/status")
async def pdf_status():
    """Status der Upload-/TMP-Verzeichnisse (Anzahl Dateien)."""
    ensure_directories()
    return {
        "werbung": _dir_status(_DIR_ADS),
        "rechnungen": _dir_status(_DIR_INV),
        "tmp": _dir_status(_DIR_TMP),
    }


@app.post("/api/pdf/cleanup")
async def pdf_cleanup():
    """Leert Upload- und TMP-Verzeichnisse sowie Logfiles für pdf_reader."""
    ensure_directories()
    cleared = {}
    for d in [_DIR_ADS, _DIR_INV, _DIR_TMP]:
        removed = 0
        for p in d.glob("*"):
            try:
                if p.is_file():
                    p.unlink()
                    removed += 1
                elif p.is_dir():
                    # Sicherheits-halber nur leere Unterordner entfernen
                    if not any(p.iterdir()):
                        p.rmdir()
            except Exception as e:
                app_logger.error(f"Cleanup Fehler in {p}: {e}")
        cleared[str(d)] = removed
    
    # Delete log files
    logs_removed = 0
    if ORDNER_LOG.exists():
        for logfile in ["werbung_read.log", "werbung_extraction.log", "rechnung_read.log"]:
            log_path = ORDNER_LOG / logfile
            if log_path.exists():
                try:
                    log_path.unlink()
                    logs_removed += 1
                except Exception as e:
                    app_logger.error(f"Logfile Cleanup Fehler: {e}")
    
    # Re-create empty log files
    from pathlib import Path
    from datetime import datetime
    log_header = f"[Logs cleared at {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}]\n"
    for logfile in ["werbung_read.log", "werbung_extraction.log", "rechnung_read.log"]:
        log_path = ORDNER_LOG / logfile
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(log_header)
        except Exception as e:
            app_logger.error(f"Fehler beim Neu-Erstellen der Log-Datei {logfile}: {e}")
    
    # Reinitialize logger handlers to point to new files
    try:
        from src.modules.pdf_reader.logger import reinitialize_loggers
        reinitialize_loggers()
    except Exception as e:
        app_logger.error(f"Fehler beim Reinitialize der Logger-Handler: {e}")
    
    return {"status": "ok", "cleared": cleared, "logs_removed": logs_removed}

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
        from websockets.exceptions import ConnectionClosedOK, ConnectionClosed

        # Ignoriere normale Verbindungsabbrüche (Browser tab geschlossen etc.)
        if isinstance(e, (WebSocketDisconnect, ConnectionClosedOK, ConnectionClosed)):
            return
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
