"""
BEISPIEL: Kompletter Workflow mit neuer Architektur
Zeigt wie Repositories → Services → Workflows zusammenarbeiten
Mit interaktiven Pausen nach jedem Schritt!
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

def wait_for_input(step_num: int, total_steps: int):
    """Warte auf User-Eingabe vor nächstem Schritt"""
    print("\n" + "="*70)
    if step_num < total_steps:
        print(f"✓ Schritt {step_num} abgeschlossen!")
        print(f"\nDrücke ENTER für Schritt {step_num + 1}, oder 'q' zum Abbrechen...")
        user_input = input(">>> ").strip().lower()
        
        if user_input == 'q':
            print("\n✗ Workflow abgebrochen vom Benutzer!")
            return False
    else:
        print(f"✓ Schritt {step_num} abgeschlossen!")
        print(f"\nDrücke ENTER zum Beenden...")
        input(">>> ")
    
    print("="*70)
    return True

def parse_arguments():
    """Parse Command Line Arguments"""
    parser = argparse.ArgumentParser(
        description='TEMU ERP Workflow - 5-Schritt Prozess',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python main_refactored.py
  python main_refactored.py --status 2 --days 7
  python main_refactored.py --status 4 --days 30
  python main_refactored.py -s 3 -d 90

TEMU Status Codes (GÜLTIG):
  2 = UN_SHIPPING (nicht versendet)
  3 = CANCELLED (storniert)
  4 = SHIPPED (versendet)
  5 = RECEIPTED (Order received)

NICHT NUTZEN:
  0 = All Orders (zu viel Daten!)
  1 = PENDING (offen - nicht versendet!)
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
        '--interactive', '-i',
        action='store_true',
        help='Interaktiv: Pause nach jedem Schritt für Kontrolle'
    )
    
    return parser.parse_args()

def run_full_workflow_refactored(parent_order_status=2, days_back=7, verbose=False, interactive=False):
    """
    REFAKTORIERT: Vollständiger Workflow mit neuer Architektur
    
    Das ist wie der alte Code funktioniert, aber VIEL sauberer:
    
    API → Repositories → Services → Workflows
    
    Args:
        parent_order_status: TEMU Status Filter (2, 3, 4, 5)
        days_back: Anzahl Tage zurück
        verbose: Debug Output
        interactive: Pause nach jedem Schritt
    """
    
    start_time = datetime.now()
    total_steps = 5
    
    # ===== Validiere Status Code =====
    # NUR diese Status Codes sind gültig!
    valid_status_codes = [2, 3, 4, 5]
    if parent_order_status not in valid_status_codes:
        print(f"✗ Ungültiger Status Code: {parent_order_status}")
        print(f"  Gültige Werte: {valid_status_codes}")
        print(f"  Erklärung:")
        print(f"    2 = UN_SHIPPING (nicht versendet)")
        print(f"    3 = CANCELLED (storniert)")
        print(f"    4 = SHIPPED (versendet)")
        print(f"    5 = RECEIPTED (Order received)")
        return False
    
    # Validiere Days
    if days_back < 1:
        print(f"✗ Days muss >= 1 sein")
        return False
    
    status_map = {
        2: 'UN_SHIPPING (nicht versendet)',
        3: 'CANCELLED (storniert)',
        4: 'SHIPPED (versendet)',
        5: 'RECEIPTED (Order received)'
    }
    
    print_header("TEMU WORKFLOW - MIT NEUER ARCHITEKTUR")
    print(f"Start: {start_time.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"Abfrage-Zeitraum: {days_back} Tage")
    print(f"Status Filter: [{parent_order_status}] {status_map.get(parent_order_status, 'unknown')}")
    
    if verbose:
        print(f"Verbose Mode: ON")
    
    if interactive:
        print(f"Interactive Mode: ON (Pause nach jedem Schritt)")
        print("\nCommands:")
        print("  ENTER → Nächster Schritt")
        print("  q     → Workflow abbrechen")
    
    print()
    
    results = {}
    
    # ========================================
    # SCHRITT 1: API → JSON
    # ========================================
    print_section(1, total_steps, "TEMU API → JSON speichern")
    try:
        # ✅ Propagiere verbose zu Workflow!
        results['api_fetch'] = run_api_to_json(
            parent_order_status=parent_order_status,
            days_back=days_back,
            verbose=verbose  # ← WICHTIG!
        )
        print(f"  ✓ API Responses gespeichert")
    except Exception as e:
        print(f"  ✗ Fehler: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        results['api_fetch'] = False
    
    if interactive:
        if not wait_for_input(1, total_steps):
            return False
    
    # ========================================
    # SCHRITT 2: JSON → Datenbank (mit SERVICE!)
    # ========================================
    print_section(2, total_steps, "JSON → Datenbank (mit Service)")
    try:
        results['json_import'] = run_json_to_db()
        print(f"  ✓ Orders in DB importiert")
    except Exception as e:
        print(f"  ✗ Fehler: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        results['json_import'] = False
    
    if interactive:
        if not wait_for_input(2, total_steps):
            return False
    
    # ========================================
    # SCHRITT 3: XML Export (mit SERVICE!)
    # ========================================
    print_section(3, total_steps, "Datenbank → XML Export (mit Service)")
    try:
        results['xml_export'] = run_db_to_xml()
        print(f"  ✓ XML exportiert")
    except Exception as e:
        print(f"  ✗ Fehler: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        results['xml_export'] = False
    
    if interactive:
        if not wait_for_input(3, total_steps):
            return False
    
    # ========================================
    # SCHRITT 4: Tracking Update (mit SERVICE!)
    # ========================================
    print_section(4, total_steps, "JTL → Tracking Update (mit Service)")
    try:
        results['tracking'] = run_update_tracking()
        print(f"  ✓ Tracking aktualisiert")
    except Exception as e:
        print(f"  ✗ Fehler: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        results['tracking'] = False
    
    if interactive:
        if not wait_for_input(4, total_steps):
            return False
    
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
    
    if interactive:
        wait_for_input(total_steps, total_steps)
    
    return success_count == total_steps

if __name__ == "__main__":
    try:
        # Parse Command Line Arguments
        args = parse_arguments()
        
        # Run Workflow mit Arguments
        success = run_full_workflow_refactored(
            parent_order_status=args.status,
            days_back=args.days,
            verbose=args.verbose,
            interactive=args.interactive
        )
        
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
