"""Workflow: JSON → Datenbank (mit neuer Architektur)"""

from typing import Optional
from config.settings import DATA_DIR
from src.db.repositories.order_repository import OrderRepository
from src.db.repositories.order_item_repository import OrderItemRepository
from src.modules.orders.service import OrderService
from src.db.connection import get_db_connection
from src.services.log_service import log_service

def run_json_to_db(job_id: Optional[str] = None) -> bool:
    """
    Importiere Orders + Items aus JSON Files in Datenbank
    Mit kompletter Merge-Logik von Shipping + Amount Daten
    
    Args:
        job_id: Optional - wenn gesetzt, logge in SQL Server
    
    Returns:
        bool: True wenn erfolgreich
    """
    
    try:
        if job_id:
            log_service.log(job_id, "json_to_db", "INFO", 
                          "→ Importiere Orders aus JSON in Datenbank")
        
        # ===== Hole Connection =====
        toci_conn = get_db_connection(database='toci', use_pool=True)
        
        # ===== Repositories =====
        order_repo = OrderRepository(connection=toci_conn)
        item_repo = OrderItemRepository(connection=toci_conn)
        
        # ===== SERVICE (Business Logic) =====
        order_service = OrderService(order_repo, item_repo)
        
        # ===== Import aus JSON Files (NEU: mit job_id!) =====
        result = order_service.import_from_json_files(job_id=job_id)  # ← job_id hinzufügen!
        
        if job_id:
            log_service.log(job_id, "json_to_db", "INFO", 
                          f"✓ Import abgeschlossen: {result.get('total', 0)} Orders")
            log_service.log(job_id, "json_to_db", "INFO", 
                          f"  Neu: {result.get('imported', 0)}, Aktualisiert: {result.get('updated', 0)}")
        
        # ✅ KORRIGIERT: True wenn erfolgreich, auch wenn 0 Orders
        return True
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        
        if job_id:
            log_service.log(job_id, "json_to_db", "ERROR", 
                          f"✗ JSON Import Fehler: {str(e)}")
            log_service.log(job_id, "json_to_db", "ERROR", error_trace)
        else:
            print(f"✗ JSON Import Fehler: {e}")
        
        return False

if __name__ == "__main__":
    run_json_to_db()