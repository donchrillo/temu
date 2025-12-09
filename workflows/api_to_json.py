"""Workflow: API → JSON (speichert API Responses lokal)"""

from config.settings import TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT
from src.marketplace_connectors.temu.service import TemuMarketplaceService

def run_api_to_json(parent_order_status=2, days_back=7, verbose: bool = False) -> bool:
    """
    Workflow: TEMU API → JSON
    
    Args:
        parent_order_status: Order Status Filter
        days_back: Tage zurück
        verbose: Debug Output (Payload + Response)
    
    Returns:
        bool: True wenn erfolgreich
    """
    # ===== Marketplace Service =====
    # ✅ Propagiere verbose Flag!
    temu_service = TemuMarketplaceService(
        app_key=TEMU_APP_KEY,
        app_secret=TEMU_APP_SECRET,
        access_token=TEMU_ACCESS_TOKEN,
        endpoint=TEMU_API_ENDPOINT,
        verbose=verbose  # ← WICHTIG!
    )
    
    return temu_service.fetch_orders(
        parent_order_status=parent_order_status,
        days_back=days_back
    )

if __name__ == "__main__":
    run_api_to_json()
