"""Workflow: API → JSON (speichert API Responses lokal)"""

import sys
from config.settings import TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT, DATA_DIR
from src.services.api_fetch_service import fetch_and_save_orders

API_RESPONSE_DIR = DATA_DIR / 'api_responses'

def run_api_to_json(parent_order_status=0, days_back=7):
    """
    Ruft TEMU API auf und speichert Responses lokal
    
    Args:
        parent_order_status: Order Status Filter (0=All, 1=PENDING, 2=UN_SHIPPING, etc.)
        days_back: Wie viele Tage zurück (Standard: 7 Tage)
    """
    return fetch_and_save_orders(
        TEMU_APP_KEY,
        TEMU_APP_SECRET,
        TEMU_ACCESS_TOKEN,
        TEMU_API_ENDPOINT,
        parent_order_status=parent_order_status,
        days_back=days_back
    )

if __name__ == "__main__":
    # Parse CLI-Parameter
    # Beispiele:
    # python -m workflows.api_to_json
    # python -m workflows.api_to_json --status 4
    # python -m workflows.api_to_json --status 4 --days 30
    
    parent_order_status = 0
    days_back = 7
    
    if '--status' in sys.argv:
        idx = sys.argv.index('--status')
        if idx + 1 < len(sys.argv):
            parent_order_status = int(sys.argv[idx + 1])
    
    if '--days' in sys.argv:
        idx = sys.argv.index('--days')
        if idx + 1 < len(sys.argv):
            days_back = int(sys.argv[idx + 1])
    
    print("=" * 70)
    print("TEMU API - Orders abrufen und speichern")
    print("=" * 70)
    
    if not all([TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN]):
        print("✗ FEHLER: TEMU API Credentials in .env nicht gesetzt!")
        sys.exit(1)
    
    print("✓ API Credentials vorhanden\n")
    print(f"Parameter:")
    print(f"  Status Filter: {parent_order_status}")
    print(f"  Tage zurück: {days_back}\n")
    
    print("[1/1] Orders abrufen und speichern")
    print("-" * 70)
    
    try:
        success = run_api_to_json(
            parent_order_status=parent_order_status,
            days_back=days_back
        )
        
        if success:
            print("\n" + "=" * 70)
            print("✓ ERFOLGREICH ABGESCHLOSSEN")
            print("=" * 70)
            print(f"✓ Gespeichert in: {API_RESPONSE_DIR}/")
            print("\nNächste Schritte:")
            print("  1. python -m scripts.validate_api_responses")
            print("  2. python -m workflows.api_to_db")
            print("=" * 70 + "\n")
            sys.exit(0)
        else:
            print("\n✗ Fehler beim Abrufen der API")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n⚠ Abgebrochen")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
