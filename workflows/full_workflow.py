"""Kompletter Workflow: CSV → DB → XML → Tracking → Excel"""

import sys
from datetime import datetime

from workflows.csv_to_db import run_csv_to_db
from workflows.api_to_db import run_api_to_db
from workflows.db_to_xml import run_db_to_xml
from workflows.update_tracking import run_update_tracking
from workflows.db_to_excel import run_db_to_excel

def print_header(title):
    """Header ausgeben"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_step(step_num, total, description):
    """Schritt ausgeben"""
    print(f"\n[Schritt {step_num}/{total}] {description}")
    print("-" * 70)

def run_full_workflow(use_api=False):
    """
    Vollständiger Workflow
    
    Args:
        use_api: True = API Import, False = CSV Import
    """
    
    start_time = datetime.now()
    
    import_method = "API" if use_api else "CSV"
    print_header(f"TEMU ORDER PROCESSING - {import_method} Import")
    print(f"Start: {start_time.strftime('%d.%m.%Y %H:%M:%S')}\n")
    
    total_steps = 5
    results = {
        'import': False,
        'xml': False,
        'tracking': False,
        'excel': False,
        'stornierte': True
    }
    
    # Schritt 1: Import (CSV oder API)
    print_step(1, total_steps, f"{import_method} → Datenbank")
    try:
        if use_api:
            results['import'] = run_api_to_db()
        else:
            results['import'] = run_csv_to_db()
    except Exception as e:
        print(f"✗ FEHLER: {e}")
    
    # Schritt 2: XML Generierung
    print_step(2, total_steps, "Datenbank → XML")
    try:
        results['xml'] = run_db_to_xml()
    except Exception as e:
        print(f"✗ FEHLER: {e}")
    
    # Schritt 3: Tracking Update
    print_step(3, total_steps, "JTL → Tracking")
    try:
        results['tracking'] = run_update_tracking()
    except Exception as e:
        print(f"✗ FEHLER: {e}")
    
    # Schritt 4: Excel Export
    print_step(4, total_steps, "Datenbank → Excel")
    try:
        results['excel'] = run_db_to_excel()
    except Exception as e:
        print(f"✗ FEHLER: {e}")
    
    # Schritt 5: Stornierte Check
    print_step(5, total_steps, "Stornierte Bestellungen prüfen")
    try:
        from scripts.stornierte_bestellungen import show_stornierte_bestellungen
        show_stornierte_bestellungen()
    except Exception as e:
        print(f"✗ FEHLER: {e}")
        results['stornierte'] = False
    
    # Zusammenfassung
    end_time = datetime.now()
    duration = end_time - start_time
    
    print_header("WORKFLOW ABGESCHLOSSEN")
    print(f"Ende: {end_time.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"Dauer: {duration.total_seconds():.1f}s")
    print("\nErgebnisse:")
    print(f"  1. {import_method} Import:   {'✓' if results['import'] else '✗'}")
    print(f"  2. XML-Export:    {'✓' if results['xml'] else '✗'}")
    print(f"  3. Tracking Update: {'✓' if results['tracking'] else '✗'}")
    print(f"  4. Excel-Export:  {'✓' if results['excel'] else '✗'}")
    print(f"  5. Storno-Check:  {'✓' if results['stornierte'] else '✗'}")
    
    success_count = sum(results.values())
    print(f"\n{success_count}/{total_steps} erfolgreich")
    print("=" * 70 + "\n")
    
    return success_count == total_steps

if __name__ == "__main__":
    try:
        # Use_api Flag: True = API, False = CSV
        use_api = '--api' in sys.argv
        success = run_full_workflow(use_api=use_api)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠ Abgebrochen")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
