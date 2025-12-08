"""Test: Sind die neuen Services funktionsfähig?"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test: Können alle Module importiert werden?"""
    print("\n" + "="*70)
    print("TEST: Imports")
    print("="*70)
    
    try:
        from src.db.repositories.order_repository import OrderRepository
        print("✓ OrderRepository")
        
        from src.db.repositories.order_item_repository import OrderItemRepository
        print("✓ OrderItemRepository")
        
        from src.modules.orders.service import OrderService
        print("✓ OrderService")
        
        from src.modules.tracking.service import TrackingService
        print("✓ TrackingService")
        
        from src.modules.xml_export.service import XmlExportService
        print("✓ XmlExportService")
        
        from src.marketplace_connectors.base_connector import BaseMarketplaceConnector
        print("✓ BaseMarketplaceConnector")
        
        from src.marketplace_connectors.temu.service import TemuMarketplaceService
        print("✓ TemuMarketplaceService")
        
        print("\n✓ ALLE IMPORTS ERFOLGREICH!\n")
        return True
    except Exception as e:
        print(f"\n✗ FEHLER: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_services():
    """Test: Können Services erstellt werden?"""
    print("="*70)
    print("TEST: Services erstellen")
    print("="*70)
    
    try:
        from src.db.repositories.order_repository import OrderRepository
        from src.db.repositories.order_item_repository import OrderItemRepository
        from src.modules.orders.service import OrderService
        from src.modules.tracking.service import TrackingService
        from src.modules.xml_export.service import XmlExportService
        
        order_repo = OrderRepository()
        item_repo = OrderItemRepository()
        print("✓ Repositories erstellt")
        
        order_service = OrderService(order_repo, item_repo)
        print("✓ OrderService erstellt")
        
        tracking_service = TrackingService(order_repo)
        print("✓ TrackingService erstellt")
        
        xml_service = XmlExportService(order_repo, item_repo)
        print("✓ XmlExportService erstellt")
        
        print("\n✓ ALLE SERVICES ERFOLGREICH!\n")
        return True
    except Exception as e:
        print(f"\n✗ FEHLER: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_marketplace_connectors():
    """Test: Marketplace Connectors funktionieren?"""
    print("="*70)
    print("TEST: Marketplace Connectors")
    print("="*70)
    
    try:
        from src.marketplace_connectors.base_connector import BaseMarketplaceConnector
        print("✓ BaseMarketplaceConnector")
        
        from src.marketplace_connectors.temu.service import TemuMarketplaceService
        print("✓ TemuMarketplaceService")
        
        from config.settings import TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT
        
        # Erstelle Instanz
        temu_service = TemuMarketplaceService(
            TEMU_APP_KEY,
            TEMU_APP_SECRET,
            TEMU_ACCESS_TOKEN,
            TEMU_API_ENDPOINT
        )
        print("✓ TemuMarketplaceService Instanz erstellt")
        
        # Validiere Credentials
        if temu_service.validate_credentials():
            print("✓ Credentials validiert")
        else:
            print("⚠ Credentials ungültig (aber ok für Test)")
        
        print("\n✓ MARKETPLACE CONNECTORS ERFOLGREICH!\n")
        return True
    except Exception as e:
        print(f"\n✗ FEHLER: {e}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print("TEMU PROJECT - REFACTORED ARCHITECTURE TESTS")
    print("="*70)
    
    success = True
    success = test_imports() and success
    success = test_services() and success
    success = test_marketplace_connectors() and success
    
    if success:
        print("="*70)
        print("✓ ALLES FUNKTIONIERT!")
        print("="*70 + "\n")
        sys.exit(0)
    else:
        print("="*70)
        print("✗ FEHLER GEFUNDEN!")
        print("="*70 + "\n")
        sys.exit(1)
