"""TEMU Marketplace Service - API Integration Layer"""

import json
from datetime import datetime, timedelta
from typing import Dict, Optional
from modules.temu.services.config import TEMU_API_RESPONSES_DIR
from .api_client import TemuApiClient
from .orders_api import TemuOrdersApi
from .inventory_api import TemuInventoryApi
from ..base_connector import BaseMarketplaceConnector
from ...logging.log_service import log_service


API_RESPONSE_DIR = TEMU_API_RESPONSES_DIR
API_RESPONSE_DIR.mkdir(exist_ok=True)

class TemuMarketplaceService(BaseMarketplaceConnector):
    """
    TEMU Marketplace Connector
    
    Implementiert BaseMarketplaceConnector für TEMU spezifische Integration.
    Verantwortlich für: API Kommunikation, JSON Speicherung, Authentifizierung
    """
    
    def __init__(self, app_key: str, app_secret: str, access_token: str, endpoint: str, verbose: bool = False):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = access_token
        self.endpoint = endpoint
        
        self.client = TemuApiClient(app_key, app_secret, access_token, endpoint, verbose=verbose)
        self.orders_api = TemuOrdersApi(self.client)
        self.inventory_api = TemuInventoryApi(self.client)
    
    def validate_credentials(self) -> bool:
        """Validiere TEMU Credentials"""
        return all([self.app_key, self.app_secret, self.access_token])
    
    def fetch_orders(self, parent_order_status=0, days_back=7, job_id: Optional[str] = None) -> bool:
        """
        Hole Orders von TEMU API und speichere lokal als JSON
        
        Args:
            parent_order_status: Order Status Filter
            days_back: Wie viele Tage zurück
            job_id: Optional - für strukturiertes Logging
        
        Returns:
            bool: True wenn erfolgreich
        """
        
        try:
            
            log_service.log(job_id, "temu_service", "INFO", 
                              "→ Hole Orders von TEMU API")
            
            # Validiere Credentials
            if not self.validate_credentials():
                error_msg = "TEMU Credentials fehlen"
                log_service.log(job_id, "temu_service", "ERROR", f"✗ {error_msg}")

            
            # Berechne Timestamps
            now = datetime.now()
            create_before = int(now.timestamp())
            create_after = int((now - timedelta(days=days_back)).timestamp())

            
            # Abrufe Orders
            log_service.log(job_id, "temu_service", "INFO", "  → Rufe Orders ab...")
            
            orders_response = self.orders_api.get_orders(
                parent_order_status=parent_order_status,            
                page_number=1, 
                page_size=100, 
                create_after=create_after,
                create_before=create_before,
                job_id=job_id
            )
            
            if orders_response is None:
                error_msg = "API Fehler beim Order-Abruf"
                log_service.log(job_id, "temu_service", "ERROR", f"✗ {error_msg}")
                return False
            
            # Speichere Orders JSON
            orders_file = API_RESPONSE_DIR / 'api_response_orders.json'
            with open(orders_file, 'w', encoding='utf-8') as f:
                json.dump(orders_response, f, ensure_ascii=False, indent=2)
            
            log_service.log(job_id, "temu_service", "INFO", "  ✓ Orders gespeichert")  

            
            # Extrahiere Orders
            orders = orders_response.get("result", {}).get("pageItems", [])
            
            if not orders:
                log_service.log(job_id, "temu_service", "INFO", "  ✓ Keine Orders gefunden")
                return True
            
            log_service.log(job_id, "temu_service", "INFO", f"  ✓ {len(orders)} Orders gefunden")
            
            # Abrufe Versand- & Preisinformationen
            log_service.log(job_id, "temu_service", "INFO", 
                          "  → Rufe Versand- und Preisinformationen ab...")
            
            shipping_responses = {}
            amount_responses = {}
            
            for order_item in orders:
                parent_order_map = order_item.get("parentOrderMap", {})
                parent_order_sn = parent_order_map.get("parentOrderSn")
                
                if not parent_order_sn:
                    continue
                
                shipping_response = self.orders_api.get_shipping_info(parent_order_sn, job_id=job_id)
                if shipping_response:
                    shipping_responses[parent_order_sn] = shipping_response
                
                amount_response = self.orders_api.get_order_amount(parent_order_sn, job_id=job_id)
                if amount_response:
                    amount_responses[parent_order_sn] = amount_response
            
            # Speichere Zusammenfassungen
            shipping_file = API_RESPONSE_DIR / 'api_response_shipping_all.json'
            with open(shipping_file, 'w', encoding='utf-8') as f:
                json.dump(shipping_responses, f, ensure_ascii=False, indent=2)
            
            amount_file = API_RESPONSE_DIR / 'api_response_amount_all.json'
            with open(amount_file, 'w', encoding='utf-8') as f:
                json.dump(amount_responses, f, ensure_ascii=False, indent=2)
            

            log_service.log(job_id, "temu_service", "INFO", 
                              f"  ✓ Versand: {len(shipping_responses)}, Preise: {len(amount_responses)}")
            log_service.log(job_id, "temu_service", "INFO", 
                              "✓ API Orders erfolgreich heruntergeladen und gespeichert")
            
            return True
        
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            log_service.log(job_id, "temu_service", "ERROR", f"✗ Fehler: {str(e)}")

    
    def fetch_shipping_info(self, order_id: str, job_id: Optional[str] = None) -> Dict:
        """Hole Versandinformationen"""
        return self.orders_api.get_shipping_info(order_id, job_id=job_id)
    
    def upload_tracking(self, tracking_data, job_id: Optional[str] = None):
        """Upload Tracking-Daten zu TEMU API
        
        Args:
            tracking_data: Liste mit Tracking-Dicts
            job_id: Optional - für strukturiertes Logging
        
        Returns:
            Tuple: (success: bool, error_code: str, error_msg: str)
        """
        return self.orders_api.upload_tracking_data(tracking_data, job_id=job_id)
    
    # def fetch_inventory_skus(self, job_id: Optional[str] = None, page_size: int = 100) -> bool:
    #     """
    #     (Deaktiviert) SKU-Download ist jetzt im InventoryService.fetch_and_store_raw_skus.
    #     Diese Methode bleibt auskommentiert, um doppelten Code zu vermeiden.
    #     """
    #     pass
