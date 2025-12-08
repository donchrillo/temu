"""Workflow: Tracking Export → TEMU API (mit Marketplace Connector)"""

from config.settings import TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT
from src.db.repositories.order_repository import OrderRepository
from src.marketplace_connectors.temu.service import TemuMarketplaceService

def run_db_to_api():
    """
    Exportiere Orders mit Tracking zur TEMU API
    Nutzt neue Repository + Marketplace Connector Architektur
    """
    
    print("=" * 70)
    print("Datenbank → TEMU API (Tracking Export)")
    print("=" * 70)
    
    # ===== REPOSITORY (Data Access Layer) =====
    order_repo = OrderRepository()
    
    # ===== MARKETPLACE CONNECTOR =====
    temu_service = TemuMarketplaceService(
        TEMU_APP_KEY,
        TEMU_APP_SECRET,
        TEMU_ACCESS_TOKEN,
        TEMU_API_ENDPOINT
    )
    
    # Hole Orders mit Tracking zum Export
    orders = order_repo.find_for_tracking_export()
    
    if not orders:
        print("✓ Keine Bestellungen zum Exportieren\n")
        return True
    
    print(f"✓ {len(orders)} Bestellungen zum Exportieren gefunden\n")
    
    # Mapping von Versanddienstleister zu Carrier ID
    CARRIER_MAPPING = {
        'DHL': 141252268,
        'DPD': 998264853,
        'default': 141252268
    }
    
    exported_count = 0
    skipped_count = 0
    error_count = 0
    
    # Loop: Jede Order einzeln exportieren
    for idx, order in enumerate(orders, 1):
        print(f"[{idx}/{len(orders)}] Order {order.bestell_id} (Tracking: {order.trackingnummer})")
        
        try:
            # Bestimme Carrier ID
            carrier_id = CARRIER_MAPPING.get(order.versanddienstleister, CARRIER_MAPPING['default'])
            
            # Baue Payload
            tracking_data = [{
                'bestell_id': order.bestell_id,
                'order_sn': order.id,
                'quantity': 1,
                'carrier_id': carrier_id,
                'tracking_number': order.trackingnummer
            }]
            
            # API Aufruf via Marketplace Service
            success = temu_service.upload_tracking(tracking_data)
            
            if success:
                order_repo.mark_exported(order.id)
                print(f"  ✓ Erfolgreich exportiert")
                exported_count += 1
            else:
                print(f"  ✗ Fehler beim Export")
                error_count += 1
        
        except Exception as e:
            print(f"  ✗ Exception: {e}")
            error_count += 1
    
    print(f"\n{'='*70}")
    print("EXPORT ABGESCHLOSSEN")
    print(f"{'='*70}")
    print(f"  ✓ Erfolgreich:   {exported_count}")
    print(f"  ✗ Fehler:        {error_count}")
    print(f"{'='*70}\n")
    
    return (exported_count + skipped_count) > 0

if __name__ == "__main__":
    run_db_to_api()
