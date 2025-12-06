"""Kompletter Workflow: CSV → DB → XML → Tracking → Excel"""

import sys
from datetime import datetime

from workflows.api_to_json import run_api_to_json
from workflows.csv_to_db import run_csv_to_db
from workflows.api_to_db import run_api_to_db
from workflows.db_to_xml import run_db_to_xml
from workflows.update_tracking import run_update_tracking
from workflows.db_to_api import run_db_to_api
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

def run_full_workflow(use_api=False, parent_order_status=0, days_back=7):
    """
    Vollständiger Workflow
    
    Args:
        use_api: True = API Import, False = CSV Import
        parent_order_status: Order Status Filter (nur bei API: 0=All, 1=PENDING, 2=UN_SHIPPING, etc.)
        days_back: Wie viele Tage zurück (Standard: 7 Tage)
    """
    
    start_time = datetime.now()
    
    import_method = "API" if use_api else "CSV"
    print_header(f"TEMU ORDER PROCESSING - {import_method} Import")
    print(f"Start: {start_time.strftime('%d.%m.%Y %H:%M:%S')}\n")
    
    if use_api:
        print(f"Abfrage-Zeitraum: {days_back} Tage zurück")
        print(f"  Status Filter: {parent_order_status}\n")
    
    # Bestimme Gesamtanzahl Schritte
    total_steps = 5 if use_api else 6
    
    results = {
        'fetch': True,
        'import': False,
        'xml': False,
        'tracking': False,
        'excel': False,
        'stornierte': True
    }
    
    # Schritt 0 (nur bei API): API → JSON
    if use_api:
        print_step(1, total_steps, "API → JSON (speichern)")
        try:
            results['fetch'] = run_api_to_json(
                parent_order_status=parent_order_status,
                days_back=days_back
            )
        except Exception as e:
            print(f"✗ FEHLER: {e}")
            results['fetch'] = False
    
    # Schritt 1: Import (CSV oder API)
    import_step = 2 if use_api else 1
    print_step(import_step, total_steps, f"{import_method} → Datenbank")
    try:
        if use_api:
            results['import'] = run_api_to_db()
        else:
            results['import'] = run_csv_to_db()
    except Exception as e:
        print(f"✗ FEHLER: {e}")
    
    # Schritt 2: XML Generierung
    xml_step = 3 if use_api else 2
    print_step(xml_step, total_steps, "Datenbank → XML")
    try:
        results['xml'] = run_db_to_xml()
    except Exception as e:
        print(f"✗ FEHLER: {e}")
    
    # Schritt 3: Tracking Update
    tracking_step = 4 if use_api else 3
    tracking_desc = "JTL → Tracking"
    print_step(tracking_step, total_steps, tracking_desc)
    try:
        results['tracking'] = run_update_tracking()
    except Exception as e:
        print(f"✗ FEHLER: {e}")
    
    # Schritt 4: Excel oder API Export 

    excel_step = 4 if use_api else 5
    print_step(excel_step, total_steps, "Tracking Export → TEMU")
    try:
        if use_api:
            results['api'] = run_db_to_api()   
        else:
            results['excel'] = run_db_to_excel()           
        
    except Exception as e:
        print(f"✗ FEHLER: {e}")
    
    # Schritt 5: Stornierte Check (nur bei CSV Import)
    if not use_api:
        storno_step = 5
        print_step(storno_step, total_steps, "Stornierte Bestellungen prüfen")
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
    
    step_num = 1
    if use_api:
        print(f"  {step_num}. API → JSON:      {'✓' if results['fetch'] else '✗'}")
        step_num += 1
    
    print(f"  {step_num}. {import_method} Import:   {'✓' if results['import'] else '✗'}")
    step_num += 1
    print(f"  {step_num}. XML-Export:    {'✓' if results['xml'] else '✗'}")
    step_num += 1
    print(f"  {step_num}. Tracking Update: {'✓' if results['tracking'] else '✗'}")
    step_num += 1
    
    if not use_api:
        print(f"  {step_num}. Excel-Export:  {'✓' if results['excel'] else '✗'}")
        step_num += 1
        print(f"  {step_num}. Storno-Check:  {'✓' if results['stornierte'] else '✗'}")
    
    success_count = sum(results.values())
    print(f"\n{success_count}/{total_steps} erfolgreich")
    print("=" * 70 + "\n")
    
    return success_count == total_steps

if __name__ == "__main__":
    try:
        use_api = '--api' in sys.argv
        
        # Parse optionale Parameter
        parent_order_status = 0
        days_back = 7  # Standard: 7 Tage zurück
        
        # Beispiele:
        # python main.py --api
        # python main.py --api --status 4
        # python main.py --api --status 4 --days 30
        
        if '--status' in sys.argv:
            idx = sys.argv.index('--status')
            if idx + 1 < len(sys.argv):
                parent_order_status = int(sys.argv[idx + 1])
        
        if '--days' in sys.argv:
            idx = sys.argv.index('--days')
            if idx + 1 < len(sys.argv):
                days_back = int(sys.argv[idx + 1])
        
        success = run_full_workflow(
            use_api=use_api,
            parent_order_status=parent_order_status,
            days_back=days_back
        )
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠ Abgebrochen")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)