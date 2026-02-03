"""
PDF Reader API Router

REST API Endpoints für PDF-Verarbeitung:
- Upload (Werbung/Rechnungen)
- Extraktion (erste Seite)
- Verarbeitung (Excel-Export)
- Status & Logs
- Download Ergebnisse
"""

import time
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from modules.shared import log_service, app_logger

# Import Services aus eigenem Modul
from .services.config import (
    ORDNER_EINGANG_RECHNUNGEN,
    ORDNER_EINGANG_WERBUNG,
    ORDNER_AUSGANG,
    ORDNER_LOG,
    ensure_directories,
    TMP_ORDNER as _DIR_TMP
)
from .services.werbung_extraction_service import extract_and_save_first_page
from .services.werbung_service import process_ad_pdfs
from .services.rechnungen_service import process_rechnungen

# Router erstellen
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

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

def _dir_status(dir_path: Path) -> dict:
    """Status eines Verzeichnisses (Anzahl Dateien)."""
    files = [p for p in dir_path.glob("*") if p.is_file()]
    return {"path": str(dir_path), "count": len(files), "files": [p.name for p in files[:5]]}

# ═══════════════════════════════════════════════════════════════
# HEALTH & STATUS
# ═══════════════════════════════════════════════════════════════

@router.get("/health")
async def health_check():
    """Health Check für PDF-Reader Modul"""
    return {
        "status": "healthy",
        "module": "pdf-reader",
        "version": "1.0.0",
        "directories": {
            "werbung": str(ORDNER_EINGANG_WERBUNG),
            "rechnungen": str(ORDNER_EINGANG_RECHNUNGEN),
            "ausgang": str(ORDNER_AUSGANG)
        }
    }

@router.get("/status")
async def pdf_status():
    """Status der Upload-/TMP-Verzeichnisse (Anzahl Dateien)."""
    ensure_directories()
    return {
        "werbung": _dir_status(ORDNER_EINGANG_WERBUNG),
        "rechnungen": _dir_status(ORDNER_EINGANG_RECHNUNGEN),
        "tmp": _dir_status(_DIR_TMP),
    }

# ═══════════════════════════════════════════════════════════════
# WERBUNG (ADVERTISING) ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/werbung/upload")
async def upload_werbung(files: List[UploadFile] = File(default=[]), process: bool = False):
    """Upload Werbungs-PDFs (optional mit sofortiger Verarbeitung)"""
    job_id = f"pdf_werbung_{int(time.time())}"
    try:
        saved_paths = await _save_uploads(files, ORDNER_EINGANG_WERBUNG)
        log_service.log(job_id, "pdf_upload", "INFO", f"{len(saved_paths)} Werbung-PDFs gespeichert")

        result = None
        filename_mapping = {}
        if process:
            filename_mapping = extract_and_save_first_page()
            result = process_ad_pdfs(filename_mapping=filename_mapping)
            log_service.log(job_id, "pdf_upload", "INFO", f"Werbung verarbeitet: {len(result) if hasattr(result, '__len__') else 0} Einträge")

        return {
            "status": "ok",
            "saved": saved_paths,
            "extracted": [str(p) for p in filename_mapping.keys()],
            "processed": bool(result is not None)
        }
    except Exception as e:
        app_logger.error(f"Werbung Upload Fehler: {e}", exc_info=True)
        log_service.log(job_id, "pdf_upload", "ERROR", f"Werbung Upload Fehler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/werbung/extract")
async def extract_werbung():
    """Extrahiere erste Seiten von bereits hochgeladenen Werbungs-PDFs."""
    job_id = f"pdf_extract_{int(time.time())}"
    try:
        filename_mapping = extract_and_save_first_page()
        log_service.log(job_id, "pdf_extract", "INFO", f"Extrahiert: {len(filename_mapping)} Dateien")
        return {
            "status": "ok",
            "extracted": [str(p) for p in filename_mapping.keys()]
        }
    except Exception as e:
        app_logger.error(f"Werbung Extract Fehler: {e}", exc_info=True)
        log_service.log(job_id, "pdf_extract", "ERROR", f"Extract Fehler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/werbung/process")
async def process_werbung():
    """Verarbeite extrahierte Werbungs-PDFs zu Excel."""
    job_id = f"pdf_process_{int(time.time())}"
    try:
        result = process_ad_pdfs()
        log_service.log(job_id, "pdf_process", "INFO", f"Verarbeitet: {len(result) if hasattr(result, '__len__') else 0} Einträge")
        return {
            "status": "ok",
            "processed": True,
            "count": len(result) if hasattr(result, '__len__') else 0
        }
    except Exception as e:
        app_logger.error(f"Werbung Process Fehler: {e}", exc_info=True)
        log_service.log(job_id, "pdf_process", "ERROR", f"Process Fehler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/werbung/result")
async def get_werbung_result():
    """Download Werbungs-Excel-Export"""
    excel_path = ORDNER_AUSGANG / "werbung.xlsx"
    if excel_path.exists():
        return FileResponse(str(excel_path), filename="werbung.xlsx")
    raise HTTPException(status_code=404, detail="Kein Ergebnis verfügbar. Bitte zuerst verarbeiten.")

# ═══════════════════════════════════════════════════════════════
# RECHNUNGEN (INVOICES) ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/rechnungen/upload")
async def upload_rechnungen(files: List[UploadFile] = File(default=[]), process: bool = False):
    """Upload Rechnungs-PDFs (optional mit sofortiger Verarbeitung)"""
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
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rechnungen/process")
async def process_rechnungen_endpoint():
    """Verarbeite Rechnungs-PDFs zu Excel."""
    job_id = f"pdf_process_{int(time.time())}"
    try:
        result = process_rechnungen()
        log_service.log(job_id, "pdf_process", "INFO", f"Verarbeitet: {len(result) if hasattr(result, '__len__') else 0} Einträge")
        return {
            "status": "ok",
            "processed": True,
            "count": len(result) if hasattr(result, '__len__') else 0
        }
    except Exception as e:
        app_logger.error(f"Rechnungen Process Fehler: {e}", exc_info=True)
        log_service.log(job_id, "pdf_process", "ERROR", f"Process Fehler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rechnungen/result")
async def get_rechnungen_result():
    """Download Rechnungs-Excel-Export"""
    excel_path = ORDNER_AUSGANG / "rechnungen.xlsx"
    if excel_path.exists():
        return FileResponse(str(excel_path), filename="rechnungen.xlsx")
    raise HTTPException(status_code=404, detail="Kein Ergebnis verfügbar. Bitte zuerst verarbeiten.")

# ═══════════════════════════════════════════════════════════════
# LOGS & CLEANUP
# ═══════════════════════════════════════════════════════════════

@router.get("/logs/{logfile}")
async def get_pdf_log(logfile: str):
    """Serviere PDF-Reader Logfiles (werbung_read.log, werbung_extraction.log, rechnung_read.log)."""
    ensure_directories()
    allowed_files = {"werbung_read.log", "werbung_extraction.log", "rechnung_read.log"}
    if logfile not in allowed_files:
        raise HTTPException(status_code=400, detail="Invalid logfile")

    log_path = ORDNER_LOG / logfile
    if not log_path.exists():
        return {"status": "empty", "content": ""}

    try:
        content = log_path.read_text(encoding="utf-8")
        return {"status": "ok", "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup")
async def pdf_cleanup():
    """Leert Upload- und TMP-Verzeichnisse sowie Logfiles für pdf_reader."""
    ensure_directories()
    cleared = {}
    for d in [ORDNER_EINGANG_WERBUNG, ORDNER_EINGANG_RECHNUNGEN, _DIR_TMP]:
        removed = 0
        for p in d.glob("*"):
            try:
                if p.is_file():
                    p.unlink()
                    removed += 1
                elif p.is_dir():
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
    from datetime import datetime
    log_header = f"[Logs cleared at {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}]\n"
    for logfile in ["werbung_read.log", "werbung_extraction.log", "rechnung_read.log"]:
        log_path = ORDNER_LOG / logfile
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(log_header)
        except Exception as e:
            app_logger.error(f"Fehler beim Neu-Erstellen der Log-Datei {logfile}: {e}")

    # Reinitialize logger handlers
    try:
        from .services.logger import reinitialize_loggers
        reinitialize_loggers()
    except Exception as e:
        app_logger.error(f"Fehler beim Reinitialize der Logger-Handler: {e}")

    return {"status": "ok", "cleared": cleared, "logs_removed": logs_removed}

# ═══════════════════════════════════════════════════════════════
# EXPORT FUNCTION (für Gateway Integration)
# ═══════════════════════════════════════════════════════════════

def get_router() -> APIRouter:
    """Wird vom Gateway aufgerufen"""
    return router
