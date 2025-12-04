"""Workflow: CSV/API → Datenbank"""

from src.services.csv_import_service import import_csv_to_database

def run_api_to_db():
    """Importiert Bestellungen in Datenbank"""
    return import_csv_to_database()

if __name__ == "__main__":
    run_api_to_db()
