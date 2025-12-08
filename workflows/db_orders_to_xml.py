"""Workflow: Datenbank → XML"""

from services.xml_generator_service import generate_xml_for_orders

def run_db_to_xml():
    """Generiert XML aus Datenbank"""
    return generate_xml_for_orders()

if __name__ == "__main__":
    run_db_to_xml()
