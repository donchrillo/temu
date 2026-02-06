"""
CSV Verarbeiter API Router

REST API Endpoints für CSV-Verarbeitung (Amazon DATEV Exporte):
- Upload (CSV/ZIP files)
- Processing Trigger
- Status / Results
- Download
- Reports
"""

import uuid
import time
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse

from modules.shared import log_service, app_logger

# Import Services aus eigenem Modul
from .services.config import CSV_DATA_DIR, CSV_EINGANG_DIR, CSV_AUSGANG_DIR, CSV_REPORTS_DIR
from .services.csv_io_service import CsvIoService
from .services.validation_service import ValidationService
from .services.replacement_service import ReplacementService
from .services.report_service import ReportService

# Initialize Services
csv_io = CsvIoService(CSV_DATA_DIR)
validator = ValidationService()
reporter = ReportService(CSV_REPORTS_DIR)

# Router erstellen
router = APIRouter()

# Job Registry (in-memory für Phase 3, später DB)
_job_registry: Dict[str, Dict] = {}


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _generate_job_id() -> str:
    """Generiere eindeutige Job ID"""
    return f"csv-{uuid.uuid4().hex[:12]}"


async def _save_uploads(files: List[UploadFile], target_dir: Path) -> List[str]:
    """Speichere Uploads in das Zielverzeichnis."""
    target_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    
    for f in files:
        dest = target_dir / f.filename
        content = await f.read()
        with open(dest, "wb") as out:
            out.write(content)
        saved.append(str(dest))
    
    return saved


def _register_job(job_id: str, status: str, files: List[str]) -> Dict:
    """Registriere Job im in-memory Registry"""
    job_info = {
        "job_id": job_id,
        "status": status,  # started, processing, completed, failed
        "files": files,
        "created_at": time.time(),
        "result": None,
        "error": None
    }
    _job_registry[job_id] = job_info
    return job_info


def _get_job(job_id: str) -> Optional[Dict]:
    """Hole Job Info"""
    return _job_registry.get(job_id)


def _update_job(job_id: str, **kwargs):
    """Update Job Info"""
    if job_id in _job_registry:
        _job_registry[job_id].update(kwargs)


# ═══════════════════════════════════════════════════════════════
# HEALTH & STATUS
# ═══════════════════════════════════════════════════════════════

@router.get("/health")
async def health_check():
    """Health Check für CSV Verarbeiter Modul"""
    return {
        "status": "healthy",
        "module": "csv-verarbeiter",
        "version": "1.0.0",
        "format": "Amazon DATEV Exporte",
        "features": {
            "validation": "OrderID Pattern (XXX-XXXXXXX-XXXXXXX)",
            "replacement": "Amazon OrderID → JTL Kundennummer",
            "reporting": "Excel with Statistics"
        }
    }


@router.get("/status")
async def csv_status():
    """Status der CSV Verarbeiter Verzeichnisse"""
    return {
        "input": {
            "path": str(CSV_EINGANG_DIR),
            "files": len(list(CSV_EINGANG_DIR.glob("*.csv"))) + len(list(CSV_EINGANG_DIR.glob("*.zip")))
        },
        "output": {
            "path": str(CSV_AUSGANG_DIR),
            "files": len(list(CSV_AUSGANG_DIR.glob("*.csv")))
        },
        "reports": {
            "path": str(CSV_REPORTS_DIR),
            "files": len(list(CSV_REPORTS_DIR.glob("*.xlsx")))
        },
        "active_jobs": len([j for j in _job_registry.values() if j["status"] in ["started", "processing"]])
    }


# ═══════════════════════════════════════════════════════════════
# UPLOAD ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.post("/upload")
async def upload_csv_files(files: List[UploadFile] = File(...)):
    """
    Upload CSV oder ZIP Dateien zur Verarbeitung.
    
    Unterstützte Formate:
    - *.csv - Einzelne Amazon DATEV CSV Datei
    - *.zip - Mehrere CSV Dateien in ZIP
    
    Returns:
        Job Info mit Upload Status
    """
    job_id = _generate_job_id()
    
    try:
        log_service.log(job_id, "csv_upload", "INFO", 
                       f"→ Uploade {len(files)} Dateien...")
        
        # Validiere Dateiendungen
        for f in files:
            if not f.filename.endswith(('.csv', '.zip', '.CSV', '.ZIP')):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file format: {f.filename}. Only .csv and .zip supported."
                )
        
        # Speichere Uploads
        saved_files = await _save_uploads(files, CSV_EINGANG_DIR)
        
        log_service.log(job_id, "csv_upload", "INFO", 
                       f"✓ {len(saved_files)} Dateien hochgeladen")
        
        # Registriere Job
        job_info = _register_job(job_id, "uploaded", saved_files)
        
        return {
            "job_id": job_id,
            "status": "uploaded",
            "files_count": len(saved_files),
            "files": [Path(f).name for f in saved_files],
            "message": "Files ready for processing. Use /api/csv/process to start."
        }
        
    except HTTPException as e:
        log_service.log(job_id, "csv_upload", "ERROR", f"❌ Upload Error: {e.detail}")
        raise
    except Exception as e:
        err_msg = str(e)
        log_service.log(job_id, "csv_upload", "ERROR", f"❌ Upload Error: {err_msg}")
        raise HTTPException(status_code=500, detail=err_msg)


# ═══════════════════════════════════════════════════════════════
# PROCESS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.post("/process")
async def process_csv(
    job_id: str = Query(..., description="Job ID from upload endpoint"),
    skip_critical: bool = Query(True, description="Skip critical accounts (0-20)")
):
    """
    Starte Verarbeitung der hochgeladenen CSV Dateien.
    
    Workflow:
    1. Load CSV files
    2. Validate structure & OrderID patterns
    3. Check for critical accounts
    4. Replace OrderIDs with JTL customer numbers
    5. Generate report with statistics
    
    Query Params:
    - job_id: Job ID from upload
    - skip_critical: Skip accounts 0-20 (default: true)
    """
    
    # Hole Job Info
    job = _get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    if job["status"] not in ["uploaded", "failed"]:
        raise HTTPException(status_code=400, detail=f"Invalid job status: {job['status']}")
    
    try:
        _update_job(job_id, status="processing")
        log_service.log(job_id, "csv_process", "INFO", "→ Starte Verarbeitung...")
        
        # 1. Load CSV files
        combined_df = None
        for file_path in job["files"]:
            file_path = Path(file_path)
            
            # Handle ZIP
            if file_path.suffix.lower() == '.zip':
                csv_files = csv_io.extract_zip(file_path, job_id)
                for csv_file in csv_files:
                    df = csv_io.read_csv(csv_file, job_id)
                    if df is not None:
                        combined_df = df if combined_df is None else combined_df.append(df, ignore_index=True)
            else:
                df = csv_io.read_csv(file_path, job_id)
                if df is not None:
                    combined_df = df if combined_df is None else combined_df.append(df, ignore_index=True)
        
        if combined_df is None or combined_df.empty:
            raise ValueError("No valid CSV data loaded")
        
        # 2. Validate structure
        valid, missing = validator.validate_csv_structure(combined_df, job_id)
        if not valid:
            raise ValueError(f"Missing columns: {', '.join(missing)}")
        
        # 3. Validate data
        validation_result = validator.validate_dataframe(combined_df, job_id)
        if not validation_result['success'] and validation_result['errors']:
            log_service.log(job_id, "csv_process", "ERROR", 
                           f"❌ Validation errors: {len(validation_result['errors'])}")
        
        # 4. Replace OrderIDs
        from modules.shared.database.repositories.jtl_common.jtl_repository import JtlRepository
        jtl_repo = JtlRepository()
        replacer = ReplacementService(jtl_repo)
        
        combined_df = replacer.replace_amazon_order_ids(
            combined_df,
            job_id,
            skip_critical_accounts=skip_critical
        )
        replacement_stats = replacer.get_replacement_stats()
        
        # 5. Save processed CSV
        output_file = f"processed_{job_id}.csv"
        output_path = csv_io.write_csv(combined_df, output_file, job_id)
        
        if output_path is None:
            raise ValueError("Failed to write output CSV")
        
        # 6. Generate report
        report_path = reporter.generate_processing_report(
            job_id,
            validation_result,
            replacement_stats,
            input_file=", ".join([Path(f).name for f in job["files"]]),
            output_file=output_file
        )
        
        # Cleanup
        csv_io.cleanup_temp_files(job_id)
        
        # Update job
        result = {
            "output_csv": str(output_path),
            "output_file": output_file,
            "report": str(report_path) if report_path else None,
            "validation": validation_result,
            "replacement": replacement_stats
        }
        
        _update_job(job_id, status="completed", result=result)
        
        log_service.log(job_id, "csv_process", "INFO", "✓ Verarbeitung abgeschlossen")
        
        return {
            "job_id": job_id,
            "status": "completed",
            "result": result,
            "download_csv": f"/api/csv/download/{job_id}?type=csv",
            "download_report": f"/api/csv/download/{job_id}?type=report"
        }
        
    except Exception as e:
        err_msg = str(e)
        log_service.log(job_id, "csv_process", "ERROR", f"❌ Processing Error: {err_msg}")
        _update_job(job_id, status="failed", error=err_msg)
        raise HTTPException(status_code=500, detail=err_msg)


# ═══════════════════════════════════════════════════════════════
# STATUS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Hole Status eines CSV Processing Jobs.
    
    Status Werte:
    - uploaded: Files hochgeladen, bereit zum Verarbeiten
    - processing: Verarbeitung läuft
    - completed: Erfolgreich abgeschlossen
    - failed: Fehler während Verarbeitung
    """
    job = _get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "created_at": job["created_at"],
        "files": job["files"],
        "result": job["result"],
        "error": job["error"]
    }


# ═══════════════════════════════════════════════════════════════
# DOWNLOAD ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/download/{job_id}")
async def download_result(
    job_id: str,
    file_type: str = Query("csv", regex="^(csv|report)$")
):
    """
    Download verarbeitete Dateien (CSV oder Report).
    
    Query Params:
    - file_type: 'csv' oder 'report' (default: csv)
    """
    job = _get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job not completed: {job['status']}")
    
    if not job["result"]:
        raise HTTPException(status_code=500, detail="No result available")
    
    try:
        if file_type == "csv":
            file_path = Path(job["result"]["output_csv"])
        else:  # report
            file_path = Path(job["result"]["report"])
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="Report not found")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        log_service.log(job_id, "csv_download", "INFO", f"→ Download: {file_path.name}")
        
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="text/csv" if file_type == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        log_service.log(job_id, "csv_download", "ERROR", f"❌ Download Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# REPORTS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/reports")
async def list_reports(job_id: Optional[str] = Query(None, description="Filter by Job ID")):
    """
    Liste verfügbare Reports.
    
    Query Params:
    - job_id: Optional - Filter nach spezifischem Job
    """
    try:
        # ReportService.list_reports() nimmt keine Parameter
        all_reports = reporter.list_reports()
        
        # Optional: Filter nach job_id (manuell)
        if job_id:
            all_reports = [r for r in all_reports if job_id in r.get('filename', '')]
        
        return {
            "total": len(all_reports),
            "reports": all_reports
        }
        
    except Exception as e:
        log_service.log("SYSTEM", "csv_reports", "ERROR", f"❌ Error listing reports: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# CLEANUP ENDPOINT (Admin)
# ═══════════════════════════════════════════════════════════════

@router.post("/cleanup")
async def cleanup_old_reports(days: int = Query(30, description="Delete reports older than X days")):
    """
    Lösche alte Reports (Admin nur).
    
    Query Params:
    - days: Löschen von Reports älter als X Tage (default: 30)
    """
    try:
        deleted = reporter.cleanup_old_reports(days)
        
        log_service.log("ADMIN", "csv_cleanup", "INFO", f"✓ {deleted} alte Reports gelöscht")
        
        return {
            "deleted": deleted,
            "older_than_days": days
        }
        
    except Exception as e:
        log_service.log("ADMIN", "csv_cleanup", "ERROR", f"❌ Cleanup Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# FRONTEND ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/", tags=["Frontend"])
async def serve_frontend_index():
    """Serve frontend HTML interface"""
    frontend_dir = Path(__file__).parent / "frontend"
    index_file = frontend_dir / "index.html"
    
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    
    return FileResponse(
        index_file,
        media_type="text/html"
    )

@router.get("/style.css", tags=["Frontend"])
async def serve_frontend_css():
    """Serve frontend CSS"""
    frontend_dir = Path(__file__).parent / "frontend"
    css_file = frontend_dir / "style.css"
    
    if not css_file.exists():
        raise HTTPException(status_code=404, detail="CSS not found")
    
    return FileResponse(
        css_file,
        media_type="text/css"
    )

@router.get("/script.js", tags=["Frontend"])
async def serve_frontend_js():
    """Serve frontend JavaScript"""
    frontend_dir = Path(__file__).parent / "frontend"
    js_file = frontend_dir / "script.js"
    
    if not js_file.exists():
        raise HTTPException(status_code=404, detail="JavaScript not found")
    
    return FileResponse(
        js_file,
        media_type="application/javascript"
    )
