"""Workflow: Datenbank → XML Export (für JTL)"""

from src.modules.xml_export.service import XmlExportService
from src.db.repositories.order_repository import OrderRepository
from src.db.repositories.order_item_repository import OrderItemRepository
from src.db.repositories.jtl_repository import JtlRepository
from src.db.connection import get_db_connection

def run_db_to_xml(save_to_disk: bool = True, import_to_jtl: bool = True) -> bool:
    """
    Workflow: Datenbank → XML Export
    
    🎯 Orchestriert: Services aufrufen in richtiger Reihenfolge
    🎯 NICHT: Business Logic, DB Operations, Connection Management
    
    Args:
        save_to_disk: Speichere XML lokal
        import_to_jtl: Importiere in JTL DB
    
    Returns:
        bool: True wenn erfolgreich
    """
    
    # ✅ Hole Connections (ZENTRAL, nicht in Service!)
    toci_conn = get_db_connection(database='toci', use_pool=True)
    
    # ✅ Erstelle Repositories (ZENTRAL, nicht in Service!)
    order_repo = OrderRepository(connection=toci_conn)
    item_repo = OrderItemRepository(connection=toci_conn)
    
    # ✅ Optional: JTL Repository
    jtl_repo = None
    if import_to_jtl:
        try:
            jtl_conn = get_db_connection(database='eazybusiness', use_pool=True)
            jtl_repo = JtlRepository(connection=jtl_conn)
        except Exception as e:
            print(f"⚠ JTL Verbindung fehlgeschlagen: {e}")
    
    # ✅ Erstelle Service (mit Dependencies!)
    service = XmlExportService(
        order_repo=order_repo,
        item_repo=item_repo,
        jtl_repo=jtl_repo
    )
    
    # ✅ Rufe Service auf (ORCHESTRIERUNG!)
    result = service.export_to_xml(
        save_to_disk=save_to_disk,
        import_to_jtl=import_to_jtl and jtl_repo is not None
    )
    
    return result.get('success', False)

if __name__ == "__main__":
    run_db_to_xml()
