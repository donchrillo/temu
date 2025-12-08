"""Workflow: Datenbank → XML Export (mit neuer Architektur)"""

from src.db.repositories.order_repository import OrderRepository
from src.db.repositories.order_item_repository import OrderItemRepository
from src.modules.xml_export.service import XmlExportService

def run_db_to_xml():
    """
    Exportiere Orders zu JTL XML
    Nutzt neue Repository + Service Architektur
    """
    
    print("=" * 70)
    print("Datenbank → XML Export")
    print("=" * 70)
    
    # ===== REPOSITORIES (Data Access Layer) =====
    order_repo = OrderRepository()
    item_repo = OrderItemRepository()
    
    # ===== SERVICE (Business Logic Layer) =====
    xml_service = XmlExportService(order_repo, item_repo)
    
    # ===== EXECUTE SERVICE =====
    result = xml_service.export_to_xml()
    
    print(f"\n{'='*70}")
    print(f"✓ XML-Export abgeschlossen!")
    print(f"{'='*70}")
    print(f"  Exportiert: {result['exported']}")
    print(f"  JTL-Import: {result['jtl_imported']}")
    print(f"{'='*70}\n")
    
    return result['exported'] > 0

if __name__ == "__main__":
    run_db_to_xml()
