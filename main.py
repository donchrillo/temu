"""
TEMU Workflow - Vollständig über Logging
Alle Ausgaben gehen direkt in SQL Server [dbo].[scheduler_logs]
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Importpfade
sys.path.insert(0, str(Path(__file__).parent))

# ===== WORKFLOWS (Orchestration) =====
from workflows.api_to_json import run_api_to_json
from workflows.json_to_db import run_json_to_db
from workflows.db_orders_to_xml import run_db_to_xml
from workflows.tracking_to_db import run_update_tracking
from workflows.db_tracking_to_api import run_db_to_api
from src.services.log_service import log_service

def parse_arguments():
    """Parse Command Line Arguments"""
    parser = argparse.ArgumentParser(
        description='TEMU ERP Workflow - 5-Schritt Prozess',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python main.py
  python main.py --status 2 --days 7
  python main.py --status 4 --days 30 --log-to-db
  python main.py -s 3 -d 90 -v --log-to-db

TEMU Status Codes (GÜLTIG):
  2 = UN_SHIPPING (nicht versendet)
  3 = CANCELLED (storniert)
  4 = SHIPPED (versendet)
  5 = RECEIPTED (Order received)

Mit --log-to-db:
  Alle Ausgaben werden in [dbo].[scheduler_logs] gespeichert
        """
    )
    
    parser.add_argument(
        '--status', '-s',
        type=int,
        default=2,
        help='TEMU Order Status (2=UN_SHIPPING, 3=CANCELLED, 4=SHIPPED, 5=RECEIPTED) [default: 2]'
    )
    
    parser.add_argument(
        '--days', '-d',
        type=int,
        default=7,
        help='Anzahl Tage zurück für Order-Abfrage [default: 7]'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose Output (Debug-Modus)'
    )
    
    parser.add_argument(
        '--log-to-db',
        action='store_true',
        help='Speichere Logs in SQL Server Datenbank (scheduler_logs Tabelle)'
    )
    
    return parser.parse_args()

def run_full_workflow_refactored(parent_order_status=2, days_back=7, verbose=False, log_to_db=False):
    """
    Vollständiger 5-Schritt Workflow
    
    Args:
        parent_order_status: TEMU Status Filter (2, 3, 4, 5)
        days_back: Anzahl Tage zurück
        verbose: Debug Output
        log_to_db: Speichere Logs in SQL Server
    """
    
    start_time = datetime.now()
    total_steps = 5
    
    # ===== Validiere Status Code =====
    valid_status_codes = [2, 3, 4, 5]
    if parent_order_status not in valid_status_codes:
        error_msg = f"Ungültiger Status Code: {parent_order_status}"
        if log_to_db:
            log_service.log(f"manual_run_{int(start_time.timestamp())}", "full_workflow", "ERROR", error_msg)
        print(f"✗ {error_msg}")
        return False
    
    if days_back < 1:
        error_msg = "Days muss >= 1 sein"
        if log_to_db:
            log_service.log(f"manual_run_{int(start_time.timestamp())}", "full_workflow", "ERROR", error_msg)
        print(f"✗ {error_msg}")
        return False
    
    status_map = {
        2: 'UN_SHIPPING (nicht versendet)',
        3: 'CANCELLED (storniert)',
        4: 'SHIPPED (versendet)',
        5: 'RECEIPTED (Order received)'
    }
    
    # ===== Starte Logging =====
    if log_to_db:
        job_id = f"manual_run_{int(start_time.timestamp())}"
        log_service.start_job_capture(job_id, "full_workflow")
        log_service.log(job_id, "full_workflow", "INFO", 
                       f"Start: {start_time.strftime('%d.%m.%Y %H:%M:%S')}")
        log_service.log(job_id, "full_workflow", "INFO", 
                       f"Abfrage-Zeitraum: {days_back} Tage")
        log_service.log(job_id, "full_workflow", "INFO", 
                       f"Status Filter: [{parent_order_status}] {status_map.get(parent_order_status, 'unknown')}")
        if verbose:
            log_service.log(job_id, "full_workflow", "INFO", "Verbose Mode: ON")
    else:
        job_id = None
    
    results = {}
    
    # ========================================
    # SCHRITT 1: API → JSON
    # ========================================
    if log_to_db:
        log_service.log(job_id, "full_workflow", "INFO", "[Schritt 1/5] TEMU API → JSON speichern")
    
    try:
        results['api_fetch'] = run_api_to_json(
            parent_order_status=parent_order_status,
            days_back=days_back,
            verbose=verbose,
            job_id=job_id  # ← JOB_ID HINZUFÜGEN!
        )
        if log_to_db:
            log_service.log(job_id, "full_workflow", "INFO", "✓ Schritt 1: API → JSON erfolgreich")
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        if log_to_db:
            log_service.log(job_id, "full_workflow", "ERROR", f"✗ Schritt 1 Fehler: {str(e)}")
            log_service.log(job_id, "full_workflow", "ERROR", error_trace)
        print(f"✗ Schritt 1 Fehler: {e}")
        results['api_fetch'] = False
    
    # ========================================
    # SCHRITT 2: JSON → Datenbank
    # ========================================
    if log_to_db:
        log_service.log(job_id, "full_workflow", "INFO", "[Schritt 2/5] JSON → Datenbank")
    
    try:
        results['json_import'] = run_json_to_db(job_id=job_id)  # ← job_id hinzufügen
        if log_to_db:
            log_service.log(job_id, "full_workflow", "INFO", "✓ Schritt 2: JSON → DB erfolgreich")
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        if log_to_db:
            log_service.log(job_id, "full_workflow", "ERROR", f"✗ Schritt 2 Fehler: {str(e)}")
            log_service.log(job_id, "full_workflow", "ERROR", error_trace)
        print(f"✗ Schritt 2 Fehler: {e}")
        results['json_import'] = False
    
    # ========================================
    # SCHRITT 3: DB → XML Export
    # ========================================
    if log_to_db:
        log_service.log(job_id, "full_workflow", "INFO", "[Schritt 3/5] Datenbank → XML Export")
    
    try:
        results['xml_export'] = run_db_to_xml(job_id=job_id)  # ← job_id hinzufügen
        if log_to_db:
            log_service.log(job_id, "full_workflow", "INFO", "✓ Schritt 3: DB → XML erfolgreich")
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        if log_to_db:
            log_service.log(job_id, "full_workflow", "ERROR", f"✗ Schritt 3 Fehler: {str(e)}")
            log_service.log(job_id, "full_workflow", "ERROR", error_trace)
        print(f"✗ Schritt 3 Fehler: {e}")
        results['xml_export'] = False
    
    # ========================================
    # SCHRITT 4: JTL → Tracking Update
    # ========================================
    if log_to_db:
        log_service.log(job_id, "full_workflow", "INFO", "[Schritt 4/5] JTL → Tracking Update")
    
    try:
        results['tracking'] = run_update_tracking(job_id=job_id)  # ← job_id hinzufügen
        if log_to_db:
            log_service.log(job_id, "full_workflow", "INFO", "✓ Schritt 4: Tracking Update erfolgreich")
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        if log_to_db:
            log_service.log(job_id, "full_workflow", "ERROR", f"✗ Schritt 4 Fehler: {str(e)}")
            log_service.log(job_id, "full_workflow", "ERROR", error_trace)
        print(f"✗ Schritt 4 Fehler: {e}")
        results['tracking'] = False
    
    # ========================================
    # SCHRITT 5: Tracking → TEMU API
    # ========================================
    if log_to_db:
        log_service.log(job_id, "full_workflow", "INFO", "[Schritt 5/5] Tracking Export → TEMU API")
    
    try:
        results['api_export'] = run_db_to_api(job_id=job_id)  # ← job_id hinzufügen
        if log_to_db:
            log_service.log(job_id, "full_workflow", "INFO", "✓ Schritt 5: Tracking → API erfolgreich")
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        if log_to_db:
            log_service.log(job_id, "full_workflow", "ERROR", f"✗ Schritt 5 Fehler: {str(e)}")
            log_service.log(job_id, "full_workflow", "ERROR", error_trace)
        print(f"✗ Schritt 5 Fehler: {e}")
        results['api_export'] = False
    
    # ========================================
    # ZUSAMMENFASSUNG
    # ========================================
    end_time = datetime.now()
    duration = end_time - start_time
    
    success_count = sum(1 for v in results.values() if v)
    
    if log_to_db:
        log_service.log(job_id, "full_workflow", "INFO", f"Ende: {end_time.strftime('%d.%m.%Y %H:%M:%S')}")
        log_service.log(job_id, "full_workflow", "INFO", f"Dauer: {duration.total_seconds():.1f}s")
        log_service.log(job_id, "full_workflow", "INFO", 
                       f"Ergebnisse: API→JSON={'✓' if results.get('api_fetch') else '✗'}, "
                       f"JSON→DB={'✓' if results.get('json_import') else '✗'}, "
                       f"DB→XML={'✓' if results.get('xml_export') else '✗'}, "
                       f"JTL→Tracking={'✓' if results.get('tracking') else '✗'}, "
                       f"Tracking→API={'✓' if results.get('api_export') else '✗'}")
        log_service.log(job_id, "full_workflow", "INFO", f"Erfolg: {success_count}/{total_steps}")
        
        # Finale Log
        if success_count == total_steps:
            log_service.end_job_capture(success=True, duration=duration.total_seconds())
        else:
            failed_steps = []
            if not results.get('api_fetch'): failed_steps.append("API → JSON")
            if not results.get('json_import'): failed_steps.append("JSON → DB")
            if not results.get('xml_export'): failed_steps.append("DB → XML")
            if not results.get('tracking'): failed_steps.append("JTL → Tracking")
            if not results.get('api_export'): failed_steps.append("Tracking → API")
            
            error_msg = f"Fehlgeschlagene Schritte: {', '.join(failed_steps)}"
            log_service.end_job_capture(success=False, duration=duration.total_seconds(), error=error_msg)
    
    # ✅ Nur Konsolen-Output wenn Fehler
    if success_count < total_steps:
        print(f"\n✗ Workflow FAILED: {success_count}/{total_steps} erfolgreich")
        return False
    
    return success_count == total_steps

if __name__ == "__main__":
    try:
        args = parse_arguments()
        
        success = run_full_workflow_refactored(
            parent_order_status=args.status,
            days_back=args.days,
            verbose=args.verbose,
            log_to_db=args.log_to_db
        )
        
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
