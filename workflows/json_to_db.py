"""Workflow: JSON → Datenbank (mit neuer Architektur)"""

import json
from pathlib import Path
from config.settings import DATA_DIR
from src.db.repositories.order_repository import OrderRepository
from src.db.repositories.order_item_repository import OrderItemRepository
from src.modules.orders.service import OrderService
from src.db.connection import get_db_connection

def run_json_to_db():
    """
    Importiere Orders + Items aus JSON Files in Datenbank
    Mit kompletter Merge-Logik von Shipping + Amount Daten
    
    🎯 Orchestriert: Services aufrufen in richtiger Reihenfolge
    🎯 NICHT: Business Logic, DB Operations
    """
    
    print("=" * 70)
    print("JSON → Datenbank importieren (mit Merge-Logik)")
    print("=" * 70 + "\n")
    
    # ===== Hole Connections (ZENTRAL!) =====
    try:
        toci_conn = get_db_connection(database='toci', use_pool=True)
    except Exception as e:
        print(f"✗ DB Verbindungsfehler: {e}")
        return False
    
    # ===== Repositories mit gepoolter Connection =====
    order_repo = OrderRepository(connection=toci_conn)
    item_repo = OrderItemRepository(connection=toci_conn)
    
    # ===== SERVICE (Business Logic) =====
    order_service = OrderService(order_repo, item_repo)
    
    # ===== Import aus JSON Files =====
    result = order_service.import_from_json_files()
    
    # ===== Ausgabe =====
    print(f"\n{'='*70}")
    print(f"✓ Import abgeschlossen!")
    print(f"{'='*70}")
    print(f"  Neue Orders: {result['imported']}")
    print(f"  Aktualisiert: {result['updated']}")
    print(f"  Total: {result['total']}")
    print(f"{'='*70}\n")
    
    return result['total'] > 0

if __name__ == "__main__":
    run_json_to_db()