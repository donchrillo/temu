"""Kompletter Workflow: API → JSON → DB → XML → Tracking → API"""

import sys
import argparse
from datetime import datetime

from workflows.api_to_json import run_api_to_json
from workflows.json_to_db import run_json_to_db
from workflows.db_orders_to_xml import run_db_to_xml
from workflows.tracking_to_db import run_update_tracking
from workflows.db_tracking_to_api import run_db_to_api

# Status-Mapping für bessere Lesbarkeit
STATUS_CHOICES = {
    0: "All",
    1: "PENDING",
    2: "UN_SHIPPING",
    3: "CANCELED",
    4: "SHIPPED",
    5: "RECEIPTED"
}

def print_header(title):
    """Header ausgeben"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_step(step_num, total, description):
    """Schritt ausgeben"""
    print(f"\n[Schritt {step_num}/{total}] {description}")
    print("-" * 70)

def run_full_workflow(parent_order_status=0, days_back=7):
    """
    Vollständiger API Workflow
    
    Args:
        parent_order_status: Order Status Filter (0=All, 1=PENDING, 2=UN_SHIPPING, etc.)
        days_back: Wie viele Tage zurück (Standard: 7 Tage)
    """
    
    start_time = datetime.now()
    total_steps = 5
    
    print_header("TEMU ORDER PROCESSING - API Import")
    print(f"Start: {start_time.strftime('%d.%m.%Y %H:%M:%S')}\n")
    print(f"Abfrage-Zeitraum: {days_back} Tage zurück")
    print(f"  Status Filter: {parent_order_status} ({STATUS_CHOICES.get(parent_order_status, 'Unknown')})\n")
    
    results = {
        'fetch': True,
        'import': False,
        'xml': False,
        'tracking': False,
        'export': False
    }
    
    # Schritt 1: API → JSON
    print_step(1, total_steps, "API → JSON (speichern)")
    try:
        results['fetch'] = run_api_to_json(
            parent_order_status=parent_order_status,
            days_back=days_back
        )
    except Exception as e:
        print(f"✗ FEHLER: {e}")
        results['fetch'] = False
    
    # Schritt 2: JSON → Datenbank
    print_step(2, total_steps, "JSON → Datenbank")
    try:
        results['import'] = run_json_to_db()
    except Exception as e:
        print(f"✗ FEHLER: {e}")
    
    # Schritt 3: XML Generierung
    print_step(3, total_steps, "Datenbank → XML")
    try:
        results['xml'] = run_db_to_xml()
    except Exception as e:
        print(f"✗ FEHLER: {e}")
    
    # Schritt 4: Tracking Update
    print_step(4, total_steps, "JTL → Tracking")
    try:
        results['tracking'] = run_update_tracking()
    except Exception as e:
        print(f"✗ FEHLER: {e}")
    
    # Schritt 5: API Export
    print_step(5, total_steps, "Tracking Export → TEMU API")
    try:
        results['export'] = run_db_to_api()
    except Exception as e:
        print(f"✗ FEHLER: {e}")
    
    # Zusammenfassung
    end_time = datetime.now()
    duration = end_time - start_time
    
    print_header("WORKFLOW ABGESCHLOSSEN")
    print(f"Ende: {end_time.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"Dauer: {duration.total_seconds():.1f}s")
    print("\nErgebnisse:")
    print(f"  1. API → JSON:      {'✓' if results['fetch'] else '✗'}")
    print(f"  2. JSON Import:     {'✓' if results['import'] else '✗'}")
    print(f"  3. XML-Export:      {'✓' if results['xml'] else '✗'}")
    print(f"  4. Tracking Update: {'✓' if results['tracking'] else '✗'}")
    print(f"  5. API Export:      {'✓' if results['export'] else '✗'}")
    
    success_count = sum(results.values())
    print(f"\n{success_count}/{total_steps} erfolgreich")
    print("=" * 70 + "\n")
    
    return success_count == total_steps

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TEMU Order Processing Workflow - API Import",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Verfügbare Status:
  0 - All (Standard)
  1 - PENDING (Ausstehend)
  2 - UN_SHIPPING (Versand ausstehend)
  3 - CANCELED (Storniert)
  4 - SHIPPED (Versendet)
  5 - RECEIPTED (Erhalten)

Beispiele:
  python main.py                        # 7 Tage, alle Status
  python main.py --status 2             # Nur Versand ausstehend
  python main.py --days 30              # 30 Tage zurück, alle Status
  python main.py --status 4 --days 14   # Versendet, letzte 2 Wochen
        """
    )
    
    parser.add_argument(
        '--status',
        type=int,
        default=2,
        choices=[0, 1, 2, 3, 4, 5],
        help='Order Status Filter (Standard: %(default)s = Versand ausstehend)'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Wie viele Tage zurück abfragen (Standard: %(default)s)'
    )
    
    args = parser.parse_args()
    
    try:
        success = run_full_workflow(
            parent_order_status=args.status,
            days_back=args.days
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
