"""Workflow: JSON → Datenbank (mit neuer Architektur)"""

import json
from pathlib import Path
from config.settings import DATA_DIR
from src.db.repositories.order_repository import OrderRepository
from src.db.repositories.order_item_repository import OrderItemRepository
from src.modules.orders.service import OrderService

def run_json_to_db():
    """
    Importiere Orders + Items aus JSON Files in Datenbank
    Nutzt die neue Repository + Service Architektur
    """
    
    print("=" * 70)
    print("JSON → Datenbank importieren")
    print("=" * 70)
    
    # ===== REPOSITORIES (Data Access Layer) =====
    order_repo = OrderRepository()
    item_repo = OrderItemRepository()
    
    # ===== SERVICE (Business Logic Layer) =====
    order_service = OrderService(order_repo, item_repo)
    
    # Lade JSON Responses
    api_response_dir = DATA_DIR / 'api_responses'
    orders_file = api_response_dir / 'api_response_orders.json'
    
    if not orders_file.exists():
        print(f"✗ Datei nicht gefunden: {orders_file}")
        return False
    
    print(f"✓ Lese {orders_file}\n")
    
    with open(orders_file, 'r', encoding='utf-8') as f:
        orders_response = json.load(f)
    
    if not orders_response.get('success'):
        print("✗ API Response war nicht erfolgreich")
        return False
    
    api_responses = orders_response.get('result', {}).get('pageItems', [])
    
    if not api_responses:
        print("✓ Keine Orders zu importieren")
        return True
    
    print(f"✓ {len(api_responses)} Orders gefunden\n")
    
    # ===== IMPORT via Service =====
    # Der Service delegiert zu Repositories - alles ist getrennt!
    result = order_service.import_from_api_response(api_responses)
    
    print(f"\n{'='*70}")
    print(f"✓ Import abgeschlossen!")
    print(f"{'='*70}")
    print(f"  Neue Orders: {result['imported']}")
    print(f"  Aktualisiert: {result['updated']}")
    print(f"  Total: {result['total']}")
    print(f"{'='*70}\n")
    
    return True

if __name__ == "__main__":
    run_json_to_db()