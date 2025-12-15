"""Workflow: API → JSON (speichert API Responses lokal)"""

from typing import Optional
from config.settings import TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT
from src.marketplace_connectors.temu.service import TemuMarketplaceService
from src.services.log_service import log_service
from src.services.logger import app_logger

def run_api_to_json(
    parent_order_status: int = 2, 
    days_back: int = 7, 
    verbose: bool = False,
    job_id: Optional[str] = None  # ✅ NEU: Optional job_id für Logging
) -> bool:
    """
    Workflow: TEMU API → JSON
    
    Args:
        parent_order_status: Order Status Filter (2, 3, 4, 5)
        days_back: Tage zurück
        verbose: Debug Output (Payload + Response)
        job_id: Optional - wenn gesetzt, logge in SQL Server
    
    Returns:
        bool: True wenn erfolgreich
    """
    
    try:
        # ===== Log Start =====
        if job_id:
            log_service.log(job_id, "api_to_json", "INFO", 
                          f"→ Hole TEMU Orders (Status: {parent_order_status}, Tage: {days_back})")
        
        # ===== Marketplace Service =====
        temu_service = TemuMarketplaceService(
            app_key=TEMU_APP_KEY,
            app_secret=TEMU_APP_SECRET,
            access_token=TEMU_ACCESS_TOKEN,
            endpoint=TEMU_API_ENDPOINT,
            verbose=verbose
        )
        
        # ===== Fetch Orders (NEU: mit job_id!) =====
        result = temu_service.fetch_orders(
            parent_order_status=parent_order_status,
            days_back=days_back,
            job_id=job_id  # ← PASS job_id!
        )
        
        # ===== Log Result =====
        if result:
            if job_id:
                log_service.log(job_id, "api_to_json", "INFO", 
                              "✓ API Orders erfolgreich heruntergeladen und gespeichert")
            return True
        else:
            if job_id:
                log_service.log(job_id, "api_to_json", "WARNING", 
                              "⚠ API Abruf fehlgeschlagen oder keine neuen Orders")
            return False
    
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        
        if job_id:
            log_service.log(job_id, "api_to_json", "ERROR", 
                          f"✗ API Abruf Fehler: {error_msg}")
            log_service.log(job_id, "api_to_json", "ERROR", error_trace)
        else:
            app_logger.error(f"API Abruf Fehler: {error_msg}", exc_info=True)
        
        return False

if __name__ == "__main__":
    # Standalone-Modus: ohne job_id (Konsolen-Output)
    run_api_to_json()
