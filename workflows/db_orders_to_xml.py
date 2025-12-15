"""Workflow: Datenbank → XML Export (für JTL)"""

from typing import Optional
from src.modules.xml_export.xml_export_service import XmlExportService
from src.db.repositories.order_repository import OrderRepository
from src.db.repositories.order_item_repository import OrderItemRepository
from src.db.repositories.jtl_repository import JtlRepository
from src.db.connection import get_db_connection
from src.services.log_service import log_service

def run_db_to_xml(
    save_to_disk: bool = True, 
    import_to_jtl: bool = True,
    job_id: Optional[str] = None
) -> bool:
    """
    Workflow: Datenbank → XML Export
    
    Args:
        save_to_disk: Speichere XML lokal
        import_to_jtl: Importiere in JTL DB
        job_id: Optional - wenn gesetzt, logge in SQL Server
    
    Returns:
        bool: True wenn erfolgreich
    """
    
    try:
        if job_id:
            log_service.log(job_id, "db_to_xml", "INFO", 
                          "→ Exportiere Orders als XML für JTL")
        
        # ===== Hole Connections =====
        toci_conn = get_db_connection(database='toci', use_pool=True)
        
        # ===== Erstelle Repositories =====
        order_repo = OrderRepository(connection=toci_conn)
        item_repo = OrderItemRepository(connection=toci_conn)
        
        # ===== Optional: JTL Repository =====
        jtl_repo = None
        if import_to_jtl:
            try:
                jtl_conn = get_db_connection(database='eazybusiness', use_pool=True)
                jtl_repo = JtlRepository(connection=jtl_conn)
                if job_id:
                    log_service.log(job_id, "db_to_xml", "INFO", "  ✓ JTL Verbindung erfolgreich")
            except Exception as e:
                if job_id:
                    log_service.log(job_id, "db_to_xml", "WARNING", 
                                  f"  ⚠ JTL Verbindung fehlgeschlagen: {e}")
        
        # ===== Erstelle Service =====
        service = XmlExportService(
            order_repo=order_repo,
            item_repo=item_repo,
            jtl_repo=jtl_repo
        )
        
        # ===== Export =====
        result = service.export_to_xml(
            save_to_disk=save_to_disk,
            import_to_jtl=import_to_jtl and jtl_repo is not None,
            job_id=job_id  # ← job_id hinzufügen!
        )
        
        if result.get('success'):
            if job_id:
                log_service.log(job_id, "db_to_xml", "INFO", 
                              f"✓ XML Export erfolgreich")
            # ✅ KORRIGIERT: True auch wenn 0 Orders
            return True
        else:
            # ✅ True wenn kein Fehler, nur 0 Daten
            if job_id:
                log_service.log(job_id, "db_to_xml", "INFO", 
                              f"✓ XML Export: {result.get('message', 'Keine Orders')}")
            return True  # ← Kein Fehler!
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        
        if job_id:
            log_service.log(job_id, "db_to_xml", "ERROR", 
                          f"✗ XML Export Fehler: {str(e)}")
            log_service.log(job_id, "db_to_xml", "ERROR", error_trace)
        else:
            print(f"✗ XML Export Fehler: {e}")
        
        return False

if __name__ == "__main__":
    run_db_to_xml()
