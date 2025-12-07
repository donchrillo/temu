"""Workflow: API → Datenbank"""

from src.services.api_sync_service import import_api_responses_to_db

def run_json_to_db():
    """Importiert API-Responses in Datenbank"""
    return import_api_responses_to_db()

if __name__ == "__main__":
    run_json_to_db()