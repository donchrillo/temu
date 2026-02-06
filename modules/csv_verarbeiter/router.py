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
import os
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Body
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
    
    Workflow (file-by-file wie Original):
    1. Für jede Datei (inkl. ZIP-Extraktion):
       - Metazeile lesen
       - CSV laden (skiprows=1)
       - Zusatzfelder initialisieren
       - OrderIDs ersetzen
       - Mit Metazeile speichern (optional "#_" Präfix)
       - Datei archivieren
    2. Excel-Report mit 4 Sheets erstellen
    
    Query Params:
    - job_id: Job ID from upload
    - skip_critical: Skip files with accounts 0-20 (default: true)
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
        
        # ReportCollector für alle Dateien
        from modules.csv_verarbeiter.services.report_service import ReportCollector
        report_collector = ReportCollector()
        
        # ReplacementService initialisieren
        from modules.csv_verarbeiter.services.replacement_service import ReplacementService
        replacer = ReplacementService()
        
        verarbeitete_dateien = []
        
        # Sammle alle zu verarbeitenden CSV-Dateien
        csv_dateien = []
        for file_path_str in job["files"]:
            file_path = Path(file_path_str)
            
            # Handle ZIP
            if file_path.suffix.lower() == '.zip':
                log_service.log(job_id, "csv_process", "INFO", f"📦 Extrahiere ZIP: {file_path.name}")
                extracted = csv_io.extract_zip(file_path)
                csv_dateien.extend([f for f in extracted if f.suffix.lower() == '.csv'])
            elif file_path.suffix.lower() == '.csv':
                csv_dateien.append(file_path)
        
        if not csv_dateien:
            raise ValueError("No valid CSV data loaded")
        
        log_service.log(job_id, "csv_process", "INFO", f"📄 {len(csv_dateien)} CSV-Dateien gefunden")
        
        # Verarbeite jede CSV-Datei einzeln
        for csv_file in csv_dateien:
            try:
                dateiname = csv_file.name
                log_service.log(job_id, "csv_process", "INFO", f"→ Verarbeite: {dateiname}")
                
                # 1. Metazeile lesen (DATEV-Header)
                metazeile, meta_ok = csv_io.lese_metazeile(csv_file)
                if not meta_ok:
                    report_collector.log_fehler(dateiname, "Metazeile konnte nicht gelesen werden")
                    continue
                
                # 2. CSV laden (ohne Metazeile)
                df, load_ok = csv_io.lade_csv_daten(csv_file)
                if not load_ok or df.empty:
                    report_collector.log_fehler(dateiname, "CSV-Daten konnten nicht geladen werden")
                    continue
                
                # 3. Zusatzfelder initialisieren
                df = replacer.initialisiere_zusatzfelder(df)
                
                # 4. OrderIDs ersetzen
                result = replacer.ersetze_amazon_order_ids(df, dateiname, skip_critical_accounts=False)
                
                # ReportCollector füllen
                for aenderung in result.get('aenderungen', []):
                    report_collector.log_aenderung(
                        dateiname, 
                        aenderung['zeile'],
                        aenderung['alt'],
                        aenderung['neu']
                    )
                
                for nicht_gefunden in result.get('nicht_gefunden', []):
                    report_collector.log_nicht_gefunden(
                        dateiname,
                        nicht_gefunden['zeile'],
                        nicht_gefunden['order_id']
                    )
                
                # 5. Kritisches Konto prüfen
                hat_kritisches_konto = result['hat_kritisches_konto']
                
                if skip_critical and hat_kritisches_konto:
                    log_service.log(job_id, "csv_process", "WARN", 
                                  f"⚠️ Überspringe {dateiname} - Kritisches Gegenkonto")
                    report_collector.log_fehler(dateiname, "Kritisches Gegenkonto (0-20) - übersprungen")
                    continue
                
                # 6. Dateiname mit Präfix (falls kritisch)
                ausgabe_dateiname = replacer.get_dateiname_mit_praefix(dateiname, hat_kritisches_konto)
                ausgabe_pfad = csv_io.ausgang_dir / ausgabe_dateiname
                
                # 7. CSV mit Metazeile speichern
                erfolg = csv_io.schreibe_csv_mit_metazeile(df, metazeile, ausgabe_pfad)
                
                if erfolg:
                    verarbeitete_dateien.append(str(ausgabe_pfad))
                    
                    # 8. Ursprungsdatei archivieren
                    csv_io.archiviere_datei(csv_file)
                    
                    # 9. Mini-Report Eintrag
                    report_collector.log_report(
                        dateiname=dateiname,
                        ersetzt=result['ersetzt'],
                        offen=result['offen'],
                        hat_kritisches_konto=hat_kritisches_konto,
                        pruefmarke_gesetzt=(result['ersetzt'] > 0)
                    )
                    
                    log_service.log(job_id, "csv_process", "INFO", 
                                  f"✓ {dateiname}: {result['ersetzt']} ersetzt, {result['offen']} offen")
                else:
                    report_collector.log_fehler(dateiname, "Fehler beim Speichern")
                    
            except Exception as e:
                err_msg = f"Fehler bei {csv_file.name}: {str(e)}"
                log_service.log(job_id, "csv_process", "ERROR", f"❌ {err_msg}")
                report_collector.log_fehler(csv_file.name, str(e))
        
        # 10. Excel-Report erstellen
        report_pfad = report_collector.speichere(csv_io.reports_dir)
        
        # Update job
        result = {
            "processed_files": verarbeitete_dateien,
            "report": str(report_pfad) if report_pfad else None,
            "files_count": len(csv_dateien),
            "successful_count": len(verarbeitete_dateien)
        }
        
        _update_job(job_id, status="completed", result=result)
        
        log_service.log(job_id, "csv_process", "INFO", 
                       f"✓ Verarbeitung abgeschlossen: {len(verarbeitete_dateien)}/{len(csv_dateien)} Dateien")
        
        return {
            "job_id": job_id,
            "status": "completed",
            "result": result,
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
# REPORT DETAILS (wie Streamlit gui_utils.py)
# ═══════════════════════════════════════════════════════════════

@router.get("/report/latest")
async def get_latest_report():
    """
    Liefert den neuesten Excel-Report inkl. aller Sheets als JSON.
    
    Rückgabe:
    {
        "filename": "auswertung_YYYY-MM-DD_HHMM.xlsx",
        "created_at": "...",
        "sheets": {
            "Mini-Report": [...],
            "Änderungen": [...],
            "Fehler": [...],
            "Nicht gefunden": [...]
        }
    }
    """
    try:
        reports = reporter.list_reports()
        if not reports:
            return {"filename": None, "created_at": None, "sheets": {}}
        
        latest = sorted(reports, key=lambda x: x.get("created_at", ""), reverse=True)[0]
        report_path = Path(latest["path"])
        
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report file not found")
        
        sheets_df = pd.read_excel(report_path, sheet_name=None)
        sheets = {}
        
        for name, df in sheets_df.items():
            if df is None:
                sheets[name] = []
            else:
                df_clean = df.where(pd.notnull(df), None)
                sheets[name] = df_clean.to_dict(orient="records")
        
        return {
            "filename": latest["filename"],
            "created_at": latest["created_at"],
            "sheets": sheets
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_service.log("SYSTEM", "report_latest", "ERROR", f"❌ {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# LOGS (wie Streamlit Letztes Logfile)
# ═══════════════════════════════════════════════════════════════

@router.get("/logs/latest")
async def get_latest_log():
    """
    Liefert das zuletzt geänderte Logfile (Inhalt + Dateiname).
    """
    try:
        project_root = Path(__file__).parent.parent.parent
        log_dirs = [
            project_root / "logs" / "app",
            project_root / "logs"
        ]
        
        log_files = []
        for log_dir in log_dirs:
            if log_dir.exists():
                for file in log_dir.glob("*.log"):
                    log_files.append(file)
                for file in log_dir.glob("log_*.txt"):
                    log_files.append(file)
        
        if not log_files:
            return {"filename": None, "content": ""}
        
        latest = sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
        
        with open(latest, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        
        # Begrenze Ausgabe, falls sehr groß
        max_chars = 20000
        if len(content) > max_chars:
            content = content[-max_chars:]
        
        return {
            "filename": latest.name,
            "content": content
        }
        
    except Exception as e:
        log_service.log("SYSTEM", "logs_latest", "ERROR", f"❌ {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/db")
async def get_db_logs(prefix: str = Query("csv", description="Prefix fuer job_id oder job_type"),
                      limit: int = Query(200, description="Maximale Anzahl Eintraege")):
    """
    Liefert Logs aus der Datenbank, gefiltert nach Prefix (job_id/job_type).
    """
    try:
        logs = log_service.get_logs_by_prefix(prefix, limit=limit, offset=0)
        return {
            "prefix": prefix,
            "total": len(logs),
            "logs": logs
        }
    except Exception as e:
        log_service.log("SYSTEM", "logs_db", "ERROR", f"❌ {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# CLEANUP ALL (wie Streamlit leere_verzeichnisse)
# ═══════════════════════════════════════════════════════════════

@router.post("/cleanup-all")
async def cleanup_all_dirs():
    """
    Leert alle relevanten Verzeichnisse (eingang, ausgang, reports, tmp, archive).
    """
    def _clear_dir(dir_path: Path, errors: List[Dict]) -> int:
        deleted = 0
        if not dir_path.exists():
            return deleted
        for entry in dir_path.iterdir():
            if entry.is_file():
                try:
                    entry.unlink()
                    deleted += 1
                except Exception as e:
                    errors.append({"path": str(entry), "error": str(e)})
        return deleted
    
    try:
        errors = []
        deleted = 0
        
        dirs_to_clean = [
            csv_io.eingang_dir,
            csv_io.ausgang_dir,
            csv_io.reports_dir,
            csv_io.archive_dir,
            csv_io.data_dir / "tmp",
            csv_io.data_dir / "ausgang_archive"
        ]
        
        for d in dirs_to_clean:
            deleted += _clear_dir(d, errors)
        
        return {
            "deleted": deleted,
            "errors": errors
        }
    
    except Exception as e:
        log_service.log("SYSTEM", "cleanup_all", "ERROR", f"❌ {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# EXPORT WORKFLOW ENDPOINTS (wie Original Streamlit)
# ═══════════════════════════════════════════════════════════════

@router.get("/list-processed-files")
async def list_processed_files():
    """
    Liste alle verarbeiteten CSV-Dateien im Ausgangsordner.
    
    Diese Dateien können für Export-ZIP ausgewählt werden.
    """
    try:
        csv_files = sorted([
            f.name for f in csv_io.ausgang_dir.glob("*.csv")
        ])
        
        return {
            "total": len(csv_files),
            "files": csv_files
        }
        
    except Exception as e:
        log_service.log("SYSTEM", "list_processed", "ERROR", f"❌ {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-export-zip")
async def create_export_zip(
    csv_files: List[str] = Body(..., description="Liste von CSV-Dateinamen"),
    zip_name: str = Body(..., description="Name für ZIP (ohne .zip)"),
    include_report: bool = Body(False, description="Report beilegen?"),
    include_log: bool = Body(False, description="Logfile beilegen?")
):
    """
    Erstellt Export-ZIP mit ausgewählten CSV-Dateien und optionalen Beilagen.
    
    Workflow wie Original Streamlit:
    1. Erstelle ZIP mit CSV-Dateien aus ausgang/
    2. Optional: Füge letzten Report hinzu
    3. Optional: Füge Logfile hinzu
    4. Verschiebe CSV-Dateien nach ausgang_archive/
    5. ZIP bleibt in ausgang/ für Download
    
    Body:
    ```json
    {
        "csv_files": ["datei1.csv", "datei2.csv"],
        "zip_name": "export_DE_2024",
        "include_report": true,
        "include_log": true
    }
    ```
    """
    try:
        if not csv_files:
            raise HTTPException(status_code=400, detail="Keine CSV-Dateien ausgewählt")
        
        if not zip_name.strip():
            raise HTTPException(status_code=400, detail="ZIP-Name fehlt")
        
        log_service.log("SYSTEM", "create_export_zip", "INFO", 
                       f"→ Erstelle Export-ZIP: {zip_name} mit {len(csv_files)} Dateien")
        
        # Finde letzten Report
        latest_report = None
        if include_report:
            reports = reporter.list_reports()
            if reports:
                # Sortiere nach Datum (neuestes zuerst)
                reports_sorted = sorted(reports, key=lambda x: x.get('created', ''), reverse=True)
                latest_report = csv_io.reports_dir / reports_sorted[0]['filename']
        
        # ZIP erstellen
        success, result = csv_io.create_export_zip(
            csv_files=csv_files,
            zip_name=zip_name,
            include_report=include_report,
            include_log=include_log,
            latest_report_path=latest_report
        )
        
        if success:
            log_service.log("SYSTEM", "create_export_zip", "INFO", 
                           f"✓ Export-ZIP erstellt: {result}")
            
            return {
                "success": True,
                "zip_filename": result,
                "download_url": f"/api/csv/download-zip/{result}",
                "archived_files": csv_files
            }
        else:
            raise HTTPException(status_code=500, detail=result)
        
    except HTTPException:
        raise
    except Exception as e:
        err_msg = str(e)
        log_service.log("SYSTEM", "create_export_zip", "ERROR", f"❌ {err_msg}")
        raise HTTPException(status_code=500, detail=err_msg)


@router.get("/download-zip/{filename}")
async def download_zip(filename: str):
    """
    Download Export-ZIP-Datei aus Ausgangsordner.
    
    Path Param:
    - filename: Name der ZIP-Datei (inkl. .zip)
    """
    try:
        zip_path = csv_io.ausgang_dir / filename
        
        if not zip_path.exists():
            raise HTTPException(status_code=404, detail=f"ZIP-Datei nicht gefunden: {filename}")
        
        if not filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="Nur ZIP-Dateien können heruntergeladen werden")
        
        log_service.log("SYSTEM", "download_zip", "INFO", f"→ Download: {filename}")
        
        return FileResponse(
            path=zip_path,
            filename=filename,
            media_type="application/zip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_service.log("SYSTEM", "download_zip", "ERROR", f"❌ {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# FRONTEND ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/", tags=["Frontend"])
async def serve_frontend_index():
    """Serve frontend HTML interface"""
    frontend_dir = Path(__file__).parent / "frontend"
    index_file = frontend_dir / "csv.html"
    
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    
    return FileResponse(
        index_file,
        media_type="text/html"
    )

# CSS and JS served via /static/ routes in main.py

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
