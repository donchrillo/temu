"""TEMU Orders API - Get Orders"""

from src.api_import.temu_client import TemuApiClient

class TemuOrdersApi:
    """Orders API Endpoint"""
    
    def __init__(self, client):
        """
        Initialisiert Orders API.
        
        Args:
            client: TemuApiClient Instanz
        """
        self.client = client
    
    def get_orders(self, page_number=1, page_size=100, parent_order_status=2):
        """
        Holt Bestellungsliste von TEMU API.
        
        Args:
            page_number: Seite (Standard: 1)
            page_size: Bestellungen pro Seite (Standard: 100, Max: 100)
            parent_order_status: 2 = alle Bestellungen
        
        Returns:
            API-Response oder None bei Fehler
        """
        
        request_params = {
            "pageSize": page_size,
            "pageNumber": page_number,
            "parentOrderStatus": parent_order_status
        }
        
        return self.client.call("bg.order.list.v2.get", request_params)
    
    def get_shipping_info(self, parent_order_sn):
        """
        Holt Versandinformationen für eine Bestellung.
        
        Args:
            parent_order_sn: Parent Bestellnummer (z.B. 'PO-076-...')
        
        Returns:
            API-Response oder None bei Fehler
        """
        
        request_params = {
            "parentOrderSn": parent_order_sn
        }
        
        return self.client.call("bg.order.shippinginfo.v2.get", request_params)
    
    def get_order_amount(self, parent_order_sn):
        """
        Holt Preisinformationen für eine Bestellung.
        
        Args:
            parent_order_sn: Parent Bestellnummer
        
        Returns:
            API-Response oder None bei Fehler
        """
        
        request_params = {
            "parentOrderSn": parent_order_sn
        }
        
        return self.client.call("bg.order.amount.query", request_params)
