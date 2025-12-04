"""Kompletter Workflow: CSV → DB → XML → Tracking → Excel"""

import sys
from datetime import datetime
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

def run_full_workflow():
    """Vollständiger Workflow"""
    
    start_time = datetime.now()
    
    print_header("TEMU ORDER PROCESSING - PHASE 2")
    print(f"Start: {start_time.strftime('%d.%m.%Y %H:%M:%S')}\n")
    
    total_steps = 4
    results = {
        'import': False,
        'xml': False,
        'tracking': False,
        'excel': False
    }
    
    # Schritt 1: CSV Import
    print_step(1, total_steps, "CSV → Datenbank")
    try:
        results['import'] = run_api_to_db()
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
    
    # Zusammenfassung
    end_time = datetime.now()
    duration = end_time - start_time
    
    print_header("WORKFLOW ABGESCHLOSSEN")
    print(f"Ende: {end_time.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"Dauer: {duration.total_seconds():.1f}s")
    print("\nErgebnisse:")
    print(f"  1. CSV Import:    {'✓' if results['import'] else '✗'}")
    print(f"  2. XML-Export:    {'✓' if results['xml'] else '✗'}")
    print(f"  3. Tracking-Update: {'✓' if results['tracking'] else '✗'}")
    print(f"  4. Excel-Export:  {'✓' if results['excel'] else '✗'}")
    
    success_count = sum(results.values())
    print(f"\n{success_count}/{total_steps} erfolgreich")
    print("=" * 70 + "\n")
    
    return success_count == total_steps

if __name__ == "__main__":
    try:
        success = run_full_workflow()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠ Abgebrochen")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
