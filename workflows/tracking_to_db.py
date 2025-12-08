"""Workflow: JTL → Tracking Update (mit neuer Architektur)"""

from src.db.repositories.order_repository import OrderRepository
from src.modules.tracking.service import TrackingService

def run_update_tracking():
    """
    Update Tracking-Daten aus JTL
    Nutzt neue Repository + Service Architektur
    """
    
    print("=" * 70)
    print("JTL → Tracking aktualisieren")
    print("=" * 70)
    
    # ===== REPOSITORY (Data Access Layer) =====
    order_repo = OrderRepository()
    
    # ===== SERVICE (Business Logic Layer) =====
    tracking_service = TrackingService(order_repo)
    
    # ===== EXECUTE SERVICE =====
    result = tracking_service.update_from_jtl()
    
    print(f"\n{'='*70}")
    print(f"✓ Tracking-Update abgeschlossen!")
    print(f"{'='*70}")
    print(f"  Aktualisiert: {result['updated']}")
    print(f"  Nicht gefunden: {result['not_found']}")
    print(f"{'='*70}\n")
    
    return result['updated'] > 0

if __name__ == "__main__":
    run_update_tracking()
