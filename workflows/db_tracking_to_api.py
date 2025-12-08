"""Workflow: Tracking Export zur TEMU API"""

from config.settings import TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT
from services.api_export_service import export_to_temu_api

def run_db_to_api():
    """Exportiert Bestellungen mit Tracking zur TEMU API"""
    return export_to_temu_api(
        TEMU_APP_KEY,
        TEMU_APP_SECRET,
        TEMU_ACCESS_TOKEN,
        TEMU_API_ENDPOINT
    )

if __name__ == "__main__":
    run_db_to_api()
