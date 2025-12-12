"""Workflow: JTL → Tracking Update in Datenbank"""

from typing import Optional
from src.db.repositories.order_repository import OrderRepository
from src.db.repositories.jtl_repository import JtlRepository
from src.modules.tracking.service import TrackingService
from src.db.connection import get_db_connection
from src.services.log_service import log_service

def run_update_tracking(job_id: Optional[str] = None) -> bool:
    """
    Aktualisiere Tracking-Daten aus JTL in TOCI Datenbank
    
    Prozess:
    1. Hole Orders ohne Tracking aus TOCI
    2. Finde Tracking in JTL Datenbank
    3. Update TOCI mit Tracking + Status
    4. Markiere als 'versendet'
    
    Args:
        job_id: Optional - wenn gesetzt, logge in SQL Server
    
    Returns:
        bool: True wenn erfolgreich
    """
    
    try:
        if job_id:
            log_service.log(job_id, "tracking_to_db", "INFO", 
                          "→ Hole Tracking-Daten aus JTL")
        
        # ===== Gepoolte Connections =====
        toci_conn = get_db_connection(database='toci', use_pool=True)
        jtl_conn = get_db_connection(database='eazybusiness', use_pool=True)
        
        # ===== Repositories =====
        order_repo = OrderRepository(connection=toci_conn)
        jtl_repo = JtlRepository(connection=jtl_conn)
        
        # ===== Service =====
        tracking_service = TrackingService(
            order_repo=order_repo,
            jtl_repo=jtl_repo
        )
        
        # ===== Update =====
        result = tracking_service.update_tracking_from_jtl()
        
        if job_id:
            log_service.log(job_id, "tracking_to_db", "INFO", 
                          f"✓ Tracking-Update abgeschlossen")
            log_service.log(job_id, "tracking_to_db", "INFO", 
                          f"  Aktualisiert: {result.get('updated', 0)}, Fehler: {result.get('errors', 0)}")
        
        # ✅ KORRIGIERT: True wenn erfolgreich (auch wenn 0 Tracking gefunden)
        return True
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        
        if job_id:
            log_service.log(job_id, "tracking_to_db", "ERROR", 
                          f"✗ Tracking Update Fehler: {str(e)}")
            log_service.log(job_id, "tracking_to_db", "ERROR", error_trace)
        else:
            print(f"✗ Tracking Update Fehler: {e}")
        
        return False

if __name__ == "__main__":
    run_update_tracking()
