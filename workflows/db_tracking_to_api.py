"""Workflow: Tracking Export → TEMU API"""

from typing import Optional
from src.db.repositories.order_repository import OrderRepository
from src.marketplace_connectors.temu.service import TemuMarketplaceService
from src.modules.tracking.service import TrackingService
from src.db.connection import get_db_connection
from config.settings import (
    TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT
)
from src.services.log_service import log_service

def run_db_to_api(job_id: Optional[str] = None) -> bool:
    """
    Workflow: Tracking Export → TEMU API
    
    Args:
        job_id: Optional - wenn gesetzt, logge in SQL Server
    
    Returns:
        bool: True wenn erfolgreich
    """
    
    try:
        if job_id:
            log_service.log(job_id, "tracking_to_api", "INFO", 
                          "→ Exportiere Tracking zu TEMU API")
        
        # ===== Validiere Credentials =====
        if not all([TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN]):
            error_msg = "TEMU Credentials nicht in .env gesetzt!"
            if job_id:
                log_service.log(job_id, "tracking_to_api", "ERROR", f"✗ {error_msg}")
            else:
                print(f"✗ {error_msg}")
            return False
        
        # ===== Gepoolte Connection =====
        toci_conn = get_db_connection(database='toci', use_pool=True)
        
        # ===== Repositories =====
        order_repo = OrderRepository(connection=toci_conn)
        
        # ===== Services =====
        tracking_service = TrackingService(order_repo)
        
        temu_service = TemuMarketplaceService(
            app_key=TEMU_APP_KEY,
            app_secret=TEMU_APP_SECRET,
            access_token=TEMU_ACCESS_TOKEN,
            endpoint=TEMU_API_ENDPOINT
        )
        
        # ===== Step 1: Hole Orders mit Tracking =====
        if job_id:
            log_service.log(job_id, "tracking_to_api", "INFO", 
                          "  → Hole Orders mit Tracking...")
        
        orders_data = order_repo.get_orders_for_tracking_export()
        
        if not orders_data:
            if job_id:
                log_service.log(job_id, "tracking_to_api", "INFO", 
                              "  ✓ Keine Bestellungen zum Exportieren")
            return True  # ← Kein Fehler!
        
        if job_id:
            log_service.log(job_id, "tracking_to_api", "INFO", 
                          f"  ✓ {len(orders_data)} Bestellungen mit Tracking")
        
        # ===== Step 2: Prepare für API =====
        if job_id:
            log_service.log(job_id, "tracking_to_api", "INFO", 
                          "  → Konvertiere zu API Format...")
        
        tracking_data_for_api = tracking_service.prepare_tracking_for_api(orders_data)
        
        if not tracking_data_for_api:
            if job_id:
                log_service.log(job_id, "tracking_to_api", "INFO", 
                              "  ✓ Keine Tracking-Daten zum Upload")
            return True  # ← Kein Fehler!
        
        if job_id:
            log_service.log(job_id, "tracking_to_api", "INFO", 
                          f"  ✓ {len(tracking_data_for_api)} Positionen zum Upload")
        
        # ===== Step 3: Upload zu TEMU API =====
        if job_id:
            log_service.log(job_id, "tracking_to_api", "INFO", 
                          "  → Lade zu TEMU API hoch...")
        
        success, error_code, error_msg = temu_service.upload_tracking(tracking_data_for_api)
        
        if success:
            # ===== Step 4: Update Status in DB =====
            if job_id:
                log_service.log(job_id, "tracking_to_api", "INFO", 
                              "  → Markiere Orders als gemeldet...")
            
            for order_data in orders_data:
                order_repo.update_temu_tracking_status(order_data['order_id'])
            
            if job_id:
                log_service.log(job_id, "tracking_to_api", "INFO", 
                              f"✓ Tracking Export erfolgreich: {len(tracking_data_for_api)} Positionen")
            
            return True
        else:
            error_detail = f"Code: {error_code}, Message: {error_msg}"
            if job_id:
                log_service.log(job_id, "tracking_to_api", "ERROR", 
                              f"✗ Tracking Export fehlgeschlagen: {error_detail}")
            else:
                print(f"✗ Tracking Export fehlgeschlagen: {error_detail}")
            
            return False
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        
        if job_id:
            log_service.log(job_id, "tracking_to_api", "ERROR", 
                          f"✗ Tracking Export Fehler: {str(e)}")
            log_service.log(job_id, "tracking_to_api", "ERROR", error_trace)
        else:
            print(f"✗ Tracking Export Fehler: {e}")
        
        return False

if __name__ == "__main__":
    run_db_to_api()
