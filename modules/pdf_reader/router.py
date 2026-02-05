"""
PDF Reader API Router

REST API Endpoints für PDF-Verarbeitung:
- Upload (Werbung/Rechnungen)
- Extraktion (erste Seite)
- Verarbeitung (Excel-Export)
- Status
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
    job_id = f"pdf_werbung_upload_{int(time.time())}"
    log_service.start_job_capture(job_id, "pdf_werbung_upload")
    
    try:
        saved_paths = await _save_uploads(files, ORDNER_EINGANG_WERBUNG)
        log_service.log(job_id, "pdf_werbung_upload", "INFO", f"{len(saved_paths)} Werbung-PDFs gespeichert")

        result = None
        extracted_filenames = []
        
        if process:
            # Wenn process=True, machen wir alles in einem Job
            log_service.log(job_id, "pdf_werbung_upload", "INFO", "Starte automatische Verarbeitung...")
            
            extracted_files = extract_and_save_first_page(job_id)
            extracted_filenames = [p.name for p in extracted_files]
            
            result = process_ad_pdfs(job_id)
            
            count = len(result) if hasattr(result, '__len__') else 0
            log_service.log(job_id, "pdf_werbung_upload", "INFO", f"Werbung verarbeitet: {count} Einträge")

        log_service.end_job_capture(success=True)
        return {
            "status": "ok",
            "saved": saved_paths,
            "extracted": extracted_filenames,
            "processed": bool(result is not None),
            "job_id": job_id
        }
    except Exception as e:
        log_service.log(job_id, "pdf_werbung_upload", "ERROR", f"Werbung Upload Fehler: {e}")
        log_service.end_job_capture(success=False, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/werbung/extract")
async def extract_werbung():
    """Extrahiere erste Seiten von bereits hochgeladenen Werbungs-PDFs."""
    job_id = f"pdf_werbung_extract_{int(time.time())}"
    log_service.start_job_capture(job_id, "pdf_werbung_extract")
    
    try:
        extracted_files = extract_and_save_first_page(job_id)
        
        log_service.log(job_id, "pdf_werbung_extract", "INFO", f"Extrahiert: {len(extracted_files)} Dateien")
        log_service.end_job_capture(success=True)
        
        return {
            "status": "ok",
            "extracted": [p.name for p in extracted_files],
            "job_id": job_id
        }
    except Exception as e:
        log_service.log(job_id, "pdf_werbung_extract", "ERROR", f"Extract Fehler: {e}")
        log_service.end_job_capture(success=False, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/werbung/process")
async def process_werbung():
    """Verarbeite extrahierte Werbungs-PDFs zu Excel."""
    job_id = f"pdf_werbung_process_{int(time.time())}"
    log_service.start_job_capture(job_id, "pdf_werbung_process")
    
    try:
        result = process_ad_pdfs(job_id)
        
        count = len(result) if hasattr(result, '__len__') else 0
        log_service.log(job_id, "pdf_werbung_process", "INFO", f"Verarbeitet: {count} Einträge")
        log_service.end_job_capture(success=True)
        
        return {
            "status": "ok",
            "processed": True,
            "count": count,
            "job_id": job_id
        }
    except Exception as e:
        log_service.log(job_id, "pdf_werbung_process", "ERROR", f"Process Fehler: {e}")
        log_service.end_job_capture(success=False, error=str(e))
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
    job_id = f"pdf_rechnungen_upload_{int(time.time())}"
    log_service.start_job_capture(job_id, "pdf_rechnungen_upload")
    
    try:
        saved_paths = await _save_uploads(files, ORDNER_EINGANG_RECHNUNGEN)
        log_service.log(job_id, "pdf_rechnungen_upload", "INFO", f"{len(saved_paths)} Rechnungs-PDFs gespeichert")

        result = None
        if process:
            log_service.log(job_id, "pdf_rechnungen_upload", "INFO", "Starte automatische Verarbeitung...")
            result = process_rechnungen(job_id)
            
            count = len(result) if hasattr(result, '__len__') else 0
            log_service.log(job_id, "pdf_rechnungen_upload", "INFO", f"Rechnungen verarbeitet: {count} Einträge")

        log_service.end_job_capture(success=True)
        return {
            "status": "ok",
            "saved": saved_paths,
            "processed": bool(result is not None),
            "job_id": job_id
        }
    except Exception as e:
        log_service.log(job_id, "pdf_rechnungen_upload", "ERROR", f"Rechnungen Upload Fehler: {e}")
        log_service.end_job_capture(success=False, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rechnungen/process")
async def process_rechnungen_endpoint():
    """Verarbeite Rechnungs-PDFs zu Excel."""
    job_id = f"pdf_rechnungen_process_{int(time.time())}"
    log_service.start_job_capture(job_id, "pdf_rechnungen_process")
    
    try:
        result = process_rechnungen(job_id)
        
        count = len(result) if hasattr(result, '__len__') else 0
        log_service.log(job_id, "pdf_rechnungen_process", "INFO", f"Verarbeitet: {count} Einträge")
        log_service.end_job_capture(success=True)
        
        return {
            "status": "ok",
            "processed": True,
            "count": count,
            "job_id": job_id
        }
    except Exception as e:
        log_service.log(job_id, "pdf_rechnungen_process", "ERROR", f"Process Fehler: {e}")
        log_service.end_job_capture(success=False, error=str(e))
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

@router.post("/cleanup")
async def pdf_cleanup():
    """Leert Upload- und TMP-Verzeichnisse für pdf_reader."""
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

    return {"status": "ok", "cleared": cleared}

# ═══════════════════════════════════════════════════════════════
# EXPORT FUNCTION (für Gateway Integration)
# ═══════════════════════════════════════════════════════════════

def get_router() -> APIRouter:
    """Wird vom Gateway aufgerufen"""
    return router
