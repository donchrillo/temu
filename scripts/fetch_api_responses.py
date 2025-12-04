"""
Fetcht TEMU API Responses und speichert sie lokal zum Testen.
"""

import json
import os
from pathlib import Path
from config.settings import (
    TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT,
    DATA_DIR
)
from src.api_import.temu_client import TemuApiClient
from src.api_import.temu_orders_api import TemuOrdersApi

# Output-Verzeichnis
API_RESPONSE_DIR = DATA_DIR / 'api_responses'
API_RESPONSE_DIR.mkdir(exist_ok=True)

def save_json_pretty(data, filepath):
    """Speichert JSON schön formatiert."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Gespeichert: {filepath}")

def fetch_and_save_orders():
    """Holt Orders aus API und speichert sie."""
    
    print("=" * 70)
    print("TEMU API - Orders abrufen")
    print("=" * 70)
    
    # Validiere Credentials
    if not all([TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN]):
        print("✗ FEHLER: TEMU API Credentials in .env nicht gesetzt!")
        return False
    
    print("✓ API Credentials vorhanden\n")
    
    # Erstelle API Client
    client = TemuApiClient(
        TEMU_APP_KEY,
        TEMU_APP_SECRET,
        TEMU_ACCESS_TOKEN,
        TEMU_API_ENDPOINT
    )
    
    orders_api = TemuOrdersApi(client)
    
    # Schritt 1: Orders abrufen
    print("[Schritt 1/1] Orders abrufen (bg.order.list.v2.get)")
    print("-" * 70)
    
    orders_response = orders_api.get_orders(page_number=1, page_size=100,parent_order_status=0)
    
    if orders_response is None:
        print("✗ Fehler beim Abrufen der Orders")
        return False
    
    # Speichere Orders
    orders_file = API_RESPONSE_DIR / 'api_response_orders.json'
    save_json_pretty(orders_response, orders_file)
    
    # Extrahiere Orders
    orders = orders_response.get("result", {}).get("pageItems", [])
    print(f"✓ {len(orders)} Orders erhalten\n")
    
    if not orders:
        print("⚠ Keine Orders gefunden")
        return True
    
    # Schritt 2: Versand- & Preisinformationen
    print("[Schritt 2/1] Versand- & Preisinformationen abrufen")
    print("-" * 70)
    
    shipping_responses = {}
    amount_responses = {}
    
    for i, order_item in enumerate(orders, 1):
        parent_order_map = order_item.get("parentOrderMap", {})
        parent_order_sn = parent_order_map.get("parentOrderSn")
        
        if not parent_order_sn:
            print(f"  ⚠ Order {i}: Keine parentOrderSn gefunden")
            continue
        
        print(f"  [{i}/{len(orders)}] {parent_order_sn}")
        
        # Versandinfo
        shipping_response = orders_api.get_shipping_info(parent_order_sn)
        if shipping_response:
            shipping_responses[parent_order_sn] = shipping_response
            shipping_file = API_RESPONSE_DIR / f"shipping_{parent_order_sn}.json"
            save_json_pretty(shipping_response, shipping_file)
        
        # Preisinformation
        amount_response = orders_api.get_order_amount(parent_order_sn)
        if amount_response:
            amount_responses[parent_order_sn] = amount_response
            amount_file = API_RESPONSE_DIR / f"amount_{parent_order_sn}.json"
            save_json_pretty(amount_response, amount_file)
    
    # Speichere Zusammenfassungen
    all_shipping_file = API_RESPONSE_DIR / 'api_response_shipping_all.json'
    save_json_pretty(shipping_responses, all_shipping_file)
    
    all_amount_file = API_RESPONSE_DIR / 'api_response_amount_all.json'
    save_json_pretty(amount_responses, all_amount_file)
    
    # Zusammenfassung
    print("\n" + "=" * 70)
    print("ERFOLGREICH ABGESCHLOSSEN")
    print("=" * 70)
    print(f"\nGespeicherte Dateien:")
    print(f"  • {orders_file}")
    print(f"  • {all_shipping_file}")
    print(f"  • {all_amount_file}")
    print(f"  • Einzelne Dateien in {API_RESPONSE_DIR}/")
    print("\nNächste Schritte:")
    print("  1. Kontrolliere die JSON-Struktur in data/api_responses/")
    print("  2. Wenn alles passt: src/services/api_sync_service.py erstellen")
    print("=" * 70 + "\n")
    
    return True

if __name__ == "__main__":
    import sys
    try:
        success = fetch_and_save_orders()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠ Abgebrochen")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
