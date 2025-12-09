"""TEMU Orders API - Get Orders"""

from src.marketplace_connectors.temu.api_client import TemuApiClient

class TemuOrdersApi:
    """Orders API Endpoint"""
    
    def __init__(self, client: TemuApiClient):
        """
        Initialisiert Orders API.
        
        Args:
            client: TemuApiClient Instanz
        """
        self.client = client
    
    def get_orders(self, page_number=1, page_size=100, parent_order_status=2, 
                   create_after=None, create_before=None):
        """
        Holt Bestellungsliste von TEMU API.
        
        Args:
            page_number: Seite (Standard: 1)
            page_size: Bestellungen pro Seite (Standard: 100, Max: 100)
            parent_order_status: Order Status Filter (0=All, 1=PENDING, 2=UN_SHIPPING, etc.)
            create_after: Unix timestamp - Start time für Order-Abfrage (optional)
            create_before: Unix timestamp - End time für Order-Abfrage (optional)
        
        Returns:
            API-Response oder None bei Fehler
        """
        
        request_params = {
            "pageSize": page_size,
            "pageNumber": page_number,
            "parentOrderStatus": parent_order_status
        }
        
        # Optionale Parameter hinzufügen
        if create_after is not None:
            request_params["createAfter"] = create_after
        
        if create_before is not None:
            request_params["createBefore"] = create_before
        
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
            Tuple: (success: bool, error_code: str, error_msg: str)
        """
        
        if not tracking_data_list:
            print("Keine Tracking-Daten zum Upload")
            return True, None, None
        
        # Gruppiere nach Carrier ID
        by_carrier = {}
        for item in tracking_data_list:
            carrier_id = item.get('carrier_id', 960246690)
            if carrier_id not in by_carrier:
                by_carrier[carrier_id] = []
            by_carrier[carrier_id].append(item)
        
        success_count = 0
        error_count = 0
        last_error_code = None
        last_error_msg = None
        
        for carrier_id, items in by_carrier.items():
            send_request_list = []
            
            for item in items:
                send_request_list.append({
                    "carrierId": carrier_id,
                    "orderSendInfoList": [
                        {
                            "orderSn": item['order_sn'],
                            "parentOrderSn": item['bestell_id'],
                            "quantity": item['quantity'],
                        }
                    ],
                    "trackingNumber": item['tracking_number']
                })
            
            # API Request
            request_params = {
                "sendRequestList": send_request_list,
                "sendType": 0
            }
            
            try:
                response = self.client.call("bg.logistics.shipment.v2.confirm", request_params)
                
                if response and response.get('success'):
                    success_count += len(items)
                    for item in items:
                        print(f"  ✓ {item['order_sn']}: {item['tracking_number']} hochgeladen")
                else:
                    error_count += len(items)
                    last_error_code = response.get('errorCode', '?') if response else 'HTTP_ERROR'
                    last_error_msg = response.get('errorMsg', 'Unbekannter Fehler') if response else 'HTTP Error'
                    print(f"  ✗ API Fehler ({last_error_code}): {last_error_msg}")
                    
            except Exception as e:
                error_count += len(items)
                last_error_msg = str(e)
                print(f"  ✗ Fehler beim Upload: {e}")
        
        print(f"\nTracking-Upload: {success_count} erfolgreich, {error_count} Fehler")
        
        # WICHTIG: Return Tuple (nicht bool!)
        success = error_count == 0
        return success, last_error_code, last_error_msg