"""Workflow: JTL → Tracking Update in Datenbank"""

from src.db.repositories.order_repository import OrderRepository
from src.db.repositories.jtl_repository import JtlRepository
from src.modules.tracking.service import TrackingService
from src.database.connection import get_db_connection

def run_update_tracking() -> bool:
    """
    Aktualisiere Tracking-Daten aus JTL in TOCI Datenbank
    
    Prozess:
    1. Hole Orders ohne Tracking aus TOCI
    2. Finde Tracking in JTL Datenbank
    3. Update TOCI mit Tracking + Status
    4. Markiere als 'versendet'
    
    Returns:
        bool: True wenn erfolgreich
    """
    
    print("=" * 70)
    print("JTL → Tracking Update")
    print("=" * 70 + "\n")
    
    # ===== Gepoolte Connections =====
    try:
        toci_conn = get_db_connection(database='toci', use_pool=True)
        jtl_conn = get_db_connection(database='eazybusiness', use_pool=True)
    except Exception as e:
        print(f"✗ DB Verbindungsfehler: {e}")
        return False
    
    # ===== Repositories mit gepoolten Connections =====
    order_repo = OrderRepository(connection=toci_conn)
    jtl_repo = JtlRepository(connection=jtl_conn)
    
    # ===== Service =====
    tracking_service = TrackingService(
        order_repo=order_repo,
        jtl_repo=jtl_repo
    )
    
    # ===== Update (KORRIGIERTER Method Name!) =====
    result = tracking_service.update_tracking_from_jtl()  # ← NICHT sync_!
    
    print(f"\n{'='*70}")
    print(f"✓ Tracking-Update abgeschlossen!")
    print(f"{'='*70}")
    print(f"  Aktualisiert: {result.get('updated', 0)}")
    print(f"  Fehler: {result.get('errors', 0)}")
    print(f"{'='*70}\n")
    
    return result.get('success', False)

if __name__ == "__main__":
    run_update_tracking()
