"""Workflow: CSV → Datenbank"""

from src.services.csv_import_service import import_csv_to_database

def run_csv_to_db():
    """Importiert CSV in Datenbank"""
    return import_csv_to_database()

if __name__ == "__main__":
    run_csv_to_db()
