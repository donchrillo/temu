"""Workflow: API → JSON (speichert API Responses lokal)"""

from config.settings import TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT, DATA_DIR
from services.api_fetch_service import fetch_and_save_orders

API_RESPONSE_DIR = DATA_DIR / 'api_responses'

def run_api_to_json(parent_order_status=2, days_back=7):
    """
    Ruft TEMU API auf und speichert Responses lokal
    
    Args:
        parent_order_status: Order Status Filter (0=All, 1=PENDING, 2=UN_SHIPPING, etc.)
        days_back: Wie viele Tage zurück (Standard: 7 Tage)
    """
    return fetch_and_save_orders(
        TEMU_APP_KEY,
        TEMU_APP_SECRET,
        TEMU_ACCESS_TOKEN,
        TEMU_API_ENDPOINT,
        parent_order_status=parent_order_status,
        days_back=days_back
    )

if __name__ == "__main__":
    run_api_to_json()
