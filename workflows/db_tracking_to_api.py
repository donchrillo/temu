"""Workflow: Tracking Export → TEMU API"""

from src.db.repositories.order_repository import OrderRepository
from src.marketplace_connectors.temu.service import TemuMarketplaceService
from src.modules.tracking.service import TrackingService
from src.database.connection import get_db_connection
from config.settings import (
    TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT
)

def run_db_to_api() -> bool:
    """
    Workflow: Tracking Export → TEMU API
    
    🎯 Orchestriert: Services aufrufen in richtiger Reihenfolge
    🎯 NICHT: Business Logic, Carrier Mapping, etc.
    
    Returns:
        bool: True wenn erfolgreich
    """
    
    print("=" * 70)
    print("Tracking Export → TEMU API")
    print("=" * 70 + "\n")
    
    # ===== Validiere Credentials =====
    if not all([TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN]):
        print("✗ TEMU Credentials nicht in .env gesetzt!")
        return False
    
    # ===== Gepoolte Connection =====
    try:
        toci_conn = get_db_connection(database='toci', use_pool=True)
    except Exception as e:
        print(f"✗ DB Verbindungsfehler: {e}")
        return False
    
    # ===== Repositories =====
    order_repo = OrderRepository(connection=toci_conn)
    
    # ===== Services =====
    # ✅ TrackingService braucht jetzt nur order_repo (jtl_repo ist optional)
    tracking_service = TrackingService(order_repo)
    
    temu_service = TemuMarketplaceService(
        app_key=TEMU_APP_KEY,
        app_secret=TEMU_APP_SECRET,
        access_token=TEMU_ACCESS_TOKEN,
        endpoint=TEMU_API_ENDPOINT
    )
    
    # ===== Step 1: Hole Orders mit Tracking =====
    print("→ Hole Orders mit Tracking...")
    
    orders_data = order_repo.get_orders_for_tracking_export()
    
    if not orders_data:
        print("✓ Keine Bestellungen zum Exportieren\n")
        return True
    
    print(f"✓ {len(orders_data)} Bestellungen mit Tracking\n")
    
    # ===== Step 2: Prepare für API (Service macht Business Logic!) =====
    print("→ Konvertiere zu API Format...\n")
    
    tracking_data_for_api = tracking_service.prepare_tracking_for_api(orders_data)
    
    if not tracking_data_for_api:
        print("✓ Keine Tracking-Daten zum Upload\n")
        return True
    
    print(f"✓ {len(tracking_data_for_api)} Positionen zum Upload\n")
    
    # ===== Step 3: Upload zu TEMU API =====
    print("→ Lade zu TEMU API hoch...\n")
    
    success, error_code, error_msg = temu_service.upload_tracking(tracking_data_for_api)
    
    if success:
        # ===== Step 4: Update Status in DB =====
        print("\n→ Markiere Orders als gemeldet...\n")
        
        for order_data in orders_data:
            order_repo.update_temu_tracking_status(order_data['order_id'])
        
        print(f"\n{'='*70}")
        print(f"✓ Tracking Export erfolgreich!")
        print(f"{'='*70}")
        print(f"  Hochgeladen: {len(tracking_data_for_api)} Positionen")
        print(f"  Orders: {len(orders_data)}")
        print(f"{'='*70}\n")
        
        return True
    else:
        print(f"\n{'='*70}")
        print(f"✗ Tracking Export fehlgeschlagen!")
        print(f"  Error Code: {error_code}")
        print(f"  Error Message: {error_msg}")
        print(f"{'='*70}\n")
        
        return False

if __name__ == "__main__":
    run_db_to_api()
