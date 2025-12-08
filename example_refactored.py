"""
BEISPIEL: Wie die refaktorierte Architektur funktioniert
Zeigt: Repository → Service → API Pattern
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.db.repositories.order_repository import OrderRepository
from src.db.repositories.order_item_repository import OrderItemRepository
from src.modules.orders.service import OrderService
from src.modules.tracking.service import TrackingService
from src.modules.xml_export.service import XmlExportService

def example_workflow():
    """Zeigt wie Services zusammenarbeiten"""
    
    print("\n" + "="*70)
    print("REFACTORED ARCHITECTURE - BEISPIEL")
    print("="*70)
    
    # ===== 1. Repositories erstellen =====
    print("\n[1] Create Repositories (Data Access Layer)")
    print("-"*70)
    order_repo = OrderRepository()
    item_repo = OrderItemRepository()
    print("✓ OrderRepository erstellt")
    print("✓ OrderItemRepository erstellt")
    
    # ===== 2. Services mit Repositories =====
    print("\n[2] Create Services (Business Logic Layer)")
    print("-"*70)
    order_service = OrderService(order_repo, item_repo)
    tracking_service = TrackingService(order_repo)
    xml_service = XmlExportService(order_repo, item_repo)
    print("✓ OrderService erstellt")
    print("✓ TrackingService erstellt")
    print("✓ XmlExportService erstellt")
    
    # ===== 3. Services nutzen =====
    print("\n[3] Use Services")
    print("-"*70)
    
    # Beispiel API Response (vereinfacht)
    api_responses = [
        {
            'success': True,
            'result': {
                'parentOrderMap': {
                    'parentOrderSn': 'PO-076-07254990055033717',
                    'parentOrderStatus': 2,
                    'parentOrderTime': 1702000000
                },
                'orderList': [
                    {
                        'orderSn': 'ORD-001',
                        'originalGoodsName': 'Test Product',
                        'originalOrderQuantity': 1
                    }
                ]
            }
        }
    ]
    
    # Import Orders
    import_result = order_service.import_from_api_response(api_responses)
    print(f"✓ Orders importiert: {import_result['imported']}")
    print(f"  Updated: {import_result['updated']}")
    
    # Update Tracking
    tracking_result = tracking_service.update_from_jtl()
    print(f"✓ Tracking aktualisiert: {tracking_result['updated']}")
    
    # XML Export
    xml_result = xml_service.export_to_xml()
    print(f"✓ XML exportiert: {xml_result['exported']}")
    
    print("\n" + "="*70)
    print("✓ WORKFLOW ERFOLGREICH")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        example_workflow()
    except Exception as e:
        print(f"\n✗ FEHLER: {e}")
        import traceback
        traceback.print_exc()
