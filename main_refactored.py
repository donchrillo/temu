"""
BEISPIEL: Kompletter Workflow mit neuer Architektur
Zeigt wie Repositories → Services → Workflows zusammenarbeiten
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

def print_header(title):
    """Header ausgeben"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_section(step_num, total, description):
    """Schritt ausgeben"""
    print(f"\n[Schritt {step_num}/{total}] {description}")
    print("-"*70)

def parse_arguments():
    """Parse Command Line Arguments"""
    parser = argparse.ArgumentParser(
        description='TEMU ERP Workflow - 5-Schritt Prozess',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python main_refactored.py
  python main_refactored.py --status 2 --days 7
  python main_refactored.py --status 1 --days 30
  python main_refactored.py -s 0 -d 90

TEMU Status Codes:
  0 = All Orders
  1 = PENDING (offen)
  2 = UN_SHIPPING (nicht versendet)
  3 = CANCELLED (storniert)
  4 = SHIPPED (versendet)
        """
    )
    
    parser.add_argument(
        '--status', '-s',
        type=int,
        default=2,
        help='TEMU Order Status Filter (0=All, 1=PENDING, 2=UN_SHIPPING, 3=CANCELLED, 4=SHIPPED) [default: 2]'
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
    
    return parser.parse_args()

def run_full_workflow_refactored(parent_order_status=2, days_back=7, verbose=False):
    """
    REFAKTORIERT: Vollständiger Workflow mit neuer Architektur
    
    Das ist wie der alte Code funktioniert, aber VIEL sauberer:
    
    API → Repositories → Services → Workflows
    
    Args:
        parent_order_status: TEMU Status Filter (0-4)
        days_back: Anzahl Tage zurück
        verbose: Debug Output
    """
    
    start_time = datetime.now()
    total_steps = 5
    
    # Validiere Status Code
    valid_status_codes = [0, 1, 2, 3, 4]
    if parent_order_status not in valid_status_codes:
        print(f"✗ Ungültiger Status Code: {parent_order_status}")
        print(f"  Gültige Werte: {valid_status_codes}")
        return False
    
    # Validiere Days
    if days_back < 1:
        print(f"✗ Days muss >= 1 sein")
        return False
    
    status_map = {
        0: 'All Orders',
        1: 'PENDING (offen)',
        2: 'UN_SHIPPING (nicht versendet)',
        3: 'CANCELLED (storniert)',
        4: 'SHIPPED (versendet)'
    }
    
    print_header("TEMU WORKFLOW - MIT NEUER ARCHITEKTUR")
    print(f"Start: {start_time.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"Abfrage-Zeitraum: {days_back} Tage")
    print(f"Status Filter: [{parent_order_status}] {status_map.get(parent_order_status, 'unknown')}")
    
    if verbose:
        print(f"Verbose Mode: ON")
    
    print()
    
    results = {}
    
    # ========================================
    # SCHRITT 1: API → JSON
    # ========================================
    print_section(1, total_steps, "TEMU API → JSON speichern")
    try:
        results['api_fetch'] = run_api_to_json(
            parent_order_status=parent_order_status,
            days_back=days_back
        )
        print(f"  ✓ API Responses gespeichert")
    except Exception as e:
        print(f"  ✗ Fehler: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        results['api_fetch'] = False
    
    # ========================================
    # SCHRITT 2: JSON → Datenbank (mit SERVICE!)
    # ========================================
    print_section(2, total_steps, "JSON → Datenbank (mit Service)")
    try:
        # Das ist jetzt so VIEL sauberer!
        # Alte Version: api_sync_service.py (DB + Business Logic gemischt)
        # Neue Version: 
        #   - OrderRepository: Nur DB Operationen
        #   - OrderItemRepository: Nur DB Operationen
        #   - OrderService: Nur Business Logic (nutzt Repositories)
        
        results['json_import'] = run_json_to_db()
        print(f"  ✓ Orders in DB importiert")
    except Exception as e:
        print(f"  ✗ Fehler: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        results['json_import'] = False
    
    # ========================================
    # SCHRITT 3: XML Export (mit SERVICE!)
    # ========================================
    print_section(3, total_steps, "Datenbank → XML Export (mit Service)")
    try:
        # Alte Version: xml_generator_service.py (DB + XML + JTL Import gemischt)
        # Neue Version:
        #   - OrderRepository: DB Reads
        #   - OrderItemRepository: DB Reads
        #   - XmlExportService: Nur Business Logic
        
        results['xml_export'] = run_db_to_xml()
        print(f"  ✓ XML exportiert")
    except Exception as e:
        print(f"  ✗ Fehler: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        results['xml_export'] = False
    
    # ========================================
    # SCHRITT 4: Tracking Update (mit SERVICE!)
    # ========================================
    print_section(4, total_steps, "JTL → Tracking Update (mit Service)")
    try:
        # Alte Version: tracking_service.py (JTL + TOCI DB gemischt)
        # Neue Version:
        #   - OrderRepository: TOCI DB Operations
        #   - TrackingService: Nur Business Logic (holt JTL Daten, delegiert Saves)
        
        results['tracking'] = run_update_tracking()
        print(f"  ✓ Tracking aktualisiert")
    except Exception as e:
        print(f"  ✗ Fehler: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        results['tracking'] = False
    
    # ========================================
    # SCHRITT 5: Tracking zu TEMU API
    # ========================================
    print_section(5, total_steps, "Tracking Export → TEMU API")
    try:
        results['api_export'] = run_db_to_api()
        print(f"  ✓ Tracking zu TEMU exportiert")
    except Exception as e:
        print(f"  ✗ Fehler: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        results['api_export'] = False
    
    # ========================================
    # ZUSAMMENFASSUNG
    # ========================================
    end_time = datetime.now()
    duration = end_time - start_time
    
    print_header("WORKFLOW ABGESCHLOSSEN")
    print(f"Ende: {end_time.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"Dauer: {duration.total_seconds():.1f}s\n")
    
    print("Ergebnisse:")
    print(f"  1. API → JSON:      {'✓' if results.get('api_fetch') else '✗'}")
    print(f"  2. JSON → DB:       {'✓' if results.get('json_import') else '✗'}")
    print(f"  3. DB → XML:        {'✓' if results.get('xml_export') else '✗'}")
    print(f"  4. JTL → Tracking:  {'✓' if results.get('tracking') else '✗'}")
    print(f"  5. Tracking → API:  {'✓' if results.get('api_export') else '✗'}")
    
    success_count = sum(1 for v in results.values() if v)
    print(f"\n✓ {success_count}/{total_steps} erfolgreich")
    print("="*70 + "\n")
    
    return success_count == total_steps

if __name__ == "__main__":
    try:
        # Parse Command Line Arguments
        args = parse_arguments()
        
        # Run Workflow mit Arguments
        success = run_full_workflow_refactored(
            parent_order_status=args.status,
            days_back=args.days,
            verbose=args.verbose
        )
        
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
