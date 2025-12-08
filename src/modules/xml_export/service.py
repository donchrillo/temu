"""XML Export Service - Business Logic (SIMPLIFIZIERT)"""

from typing import Dict
from src.db.repositories.order_repository import OrderRepository
from src.db.repositories.order_item_repository import OrderItemRepository
from config.settings import XML_OUTPUT_PATH

class XmlExportService:
    """Business Logic für XML-Export"""
    
    def __init__(self, order_repo: OrderRepository = None,
                 item_repo: OrderItemRepository = None):
        self.order_repo = order_repo or OrderRepository()
        self.item_repo = item_repo or OrderItemRepository()
    
    def export_to_xml(self) -> Dict:
        """
        Exportiere Orders zu XML
        SIMPLIFIZIERT: Nur Basis-Struktur
        """
        orders = self.order_repo.find_by_status('importiert')
        exported_count = 0
        
        for order in orders:
            items = self.item_repo.find_by_order_id(order.id)
            
            # Sehr simplifiziert: Nur als Placeholder
            xml_content = f"""<?xml version="1.0" encoding="ISO-8859-1"?>
<tBestellungen>
  <tBestellung>
    <cExterneBestellNr>{order.bestell_id}</cExterneBestellNr>
    <dErstellt>{order.kaufdatum.strftime('%d.%m.%Y') if order.kaufdatum else ''}</dErstellt>
    <cKunde>{order.nachname_empfaenger}</cKunde>
  </tBestellung>
</tBestellungen>"""
            
            # Speichere Datei
            with open(str(XML_OUTPUT_PATH), 'w', encoding='ISO-8859-1') as f:
                f.write(xml_content)
            
            exported_count += 1
        
        return {'exported': exported_count, 'jtl_imported': 0}