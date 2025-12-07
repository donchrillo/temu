"""Workflow: Datenbank → Excel"""

from src.services.excel_export_service import export_tracking_to_excel

def run_db_to_excel():
    """Exportiert Tracking als Excel"""
    return export_tracking_to_excel()

if __name__ == "__main__":
    run_db_to_excel()
