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
    
    def get_orders(self, page_number=1, page_size=100, parent_order_status=2, 
                   createAfter=None, createBefore=None):
        """
        Holt Bestellungsliste von TEMU API.
        
        Args:
            page_number: Seite (Standard: 1)
            page_size: Bestellungen pro Seite (Standard: 100, Max: 100)
            parent_order_status: Order Status Filter (0=All, 1=PENDING, 2=UN_SHIPPING, etc.)
            createAfter: Unix timestamp - Start time für Order-Abfrage (optional)
            createBefore: Unix timestamp - End time für Order-Abfrage (optional)
        
        Returns:
            API-Response oder None bei Fehler
        """
        
        request_params = {
            "pageSize": page_size,
            "pageNumber": page_number,
            "parentOrderStatus": parent_order_status
        }
        
        # Optionale Parameter hinzufügen
        if createAfter is not None:
            request_params["createAfter"] = createAfter
        
        if createBefore is not None:
            request_params["createBefore"] = createBefore
        
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
    
    def upload_tracking_data(self, tracking_data_list):
        """
        Lädt Tracking-Daten zu TEMU API hoch
        
        Args:
            tracking_data_list: Liste mit Dicts containing:
                - bestell_id (parentOrderSn)
                - order_sn
                - quantity
                - tracking_number
                - carrier_id (Standard: 960246690 für externe Carrier)
        
        Returns:
            tuple: (success: bool, error_code: int or None, error_msg: str or None)
        """
        
        if not tracking_data_list:
            print("Keine Tracking-Daten zum Upload")
            return (True, None, None)
        
        # Für einzelne Orders ist tracking_data_list normalerweise nur 1 Element
        item = tracking_data_list[0]
        carrier_id = item.get('carrier_id', 960246690)
        
        send_request = {
            "carrierId": carrier_id,
            "orderSendInfoList": [
                {
                    "orderSn": item['order_sn'],
                    "parentOrderSn": item['bestell_id'],
                    "quantity": item['quantity'],
                }
            ],
            "trackingNumber": item['tracking_number']
        }
        
        # API Request
        payload = {
            "type": "bg.logistics.shipment.v2.confirm",
            "sendRequestList": [send_request],
            "sendType": 0
        }
        
        try:
            response = self.client.call("bg.logistics.shipment.v2.confirm", payload)
            
            if response is None:
                return (False, -1, "API gab keine Response (Fehler bereits geloggt)")
            
            if response.get('success'):
                print(f"  ✓ {item['order_sn']}: {item['tracking_number']} hochgeladen")
                return (True, None, None)
            
            # Fehlerfall - Error wurde bereits von temu_client.py geloggt
            error_code = response.get('errorCode')
            error_msg = response.get('errorMsg', 'Unbekannter Fehler')
            
            return (False, error_code, error_msg)
                    
        except Exception as e:
            print(f"  ✗ Exception beim Upload: {e}")
            return (False, -1, str(e))
