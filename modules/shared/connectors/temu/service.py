"""TEMU Marketplace Service - API Integration Layer"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from modules.temu.services.config import TEMU_API_RESPONSES_DIR
from .api_client import TemuApiClient
from .orders_api import TemuOrdersApi
from .inventory_api import TemuInventoryApi
from ..base_connector import BaseMarketplaceConnector
from ...logging.log_service import log_service


API_RESPONSE_DIR = TEMU_API_RESPONSES_DIR
API_RESPONSE_DIR.mkdir(exist_ok=True)


def _save_json(filepath: Path, data: dict) -> None:
    """Speichere Daten als JSON-Datei."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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
        Hole Orders von TEMU API und speichere lokal als JSON.
        
        Args:
            parent_order_status: Order Status Filter
            days_back: Wie viele Tage zurück
            job_id: Optional - für strukturiertes Logging
        
        Returns:
            bool: True wenn erfolgreich
        """
        try:
            log_service.log(job_id, "temu_service", "INFO", "→ Hole Orders von TEMU API")
            
            # Guard Clause: Credentials prüfen
            if not self.validate_credentials():
                log_service.log(job_id, "temu_service", "ERROR", "✗ TEMU Credentials fehlen")
                return False
            
            # 1. Orders abrufen
            orders_response = self._fetch_orders_from_api(parent_order_status, days_back, job_id)
            if orders_response is None:
                return False
            
            # 2. Orders JSON speichern
            _save_json(API_RESPONSE_DIR / 'api_response_orders.json', orders_response)
            log_service.log(job_id, "temu_service", "INFO", "  ✓ Orders gespeichert")
            
            # 3. Orders extrahieren
            orders = orders_response.get("result", {}).get("pageItems", [])
            if not orders:
                log_service.log(job_id, "temu_service", "INFO", "  ✓ Keine Orders gefunden")
                return True
            
            log_service.log(job_id, "temu_service", "INFO", f"  ✓ {len(orders)} Orders gefunden")
            
            # 4. Zusätzliche Informationen abrufen und speichern
            self._fetch_and_save_order_details(orders, job_id)
            
            log_service.log(job_id, "temu_service", "INFO", 
                          "✓ API Orders erfolgreich heruntergeladen und gespeichert")
            return True
        
        except Exception as e:
            log_service.log(job_id, "temu_service", "ERROR", f"✗ Fehler: {str(e)}")
            return False
    
    def _fetch_orders_from_api(self, parent_order_status: int, days_back: int, 
                                job_id: Optional[str]) -> Optional[dict]:
        """Rufe Orders von TEMU API ab."""
        log_service.log(job_id, "temu_service", "INFO", "  → Rufe Orders ab...")
        
        now = datetime.now()
        create_before = int(now.timestamp())
        create_after = int((now - timedelta(days=days_back)).timestamp())
        
        response = self.orders_api.get_orders(
            parent_order_status=parent_order_status,
            page_number=1,
            page_size=100,
            create_after=create_after,
            create_before=create_before,
            job_id=job_id
        )
        
        if response is None:
            log_service.log(job_id, "temu_service", "ERROR", "✗ API Fehler beim Order-Abruf")
        
        return response
    
    def _fetch_and_save_order_details(self, orders: list, job_id: Optional[str]) -> None:
        """Rufe Versand- und Preisinformationen pro Order ab und speichere als JSON."""
        log_service.log(job_id, "temu_service", "INFO", 
                      "  → Rufe Versand- und Preisinformationen ab...")
        
        shipping_responses = {}
        amount_responses = {}
        
        for order_item in orders:
            parent_order_sn = order_item.get("parentOrderMap", {}).get("parentOrderSn")
            if not parent_order_sn:
                continue
            
            shipping_response = self.orders_api.get_shipping_info(parent_order_sn, job_id=job_id)
            if shipping_response:
                shipping_responses[parent_order_sn] = shipping_response
            
            amount_response = self.orders_api.get_order_amount(parent_order_sn, job_id=job_id)
            if amount_response:
                amount_responses[parent_order_sn] = amount_response
        
        _save_json(API_RESPONSE_DIR / 'api_response_shipping_all.json', shipping_responses)
        _save_json(API_RESPONSE_DIR / 'api_response_amount_all.json', amount_responses)
        
        log_service.log(job_id, "temu_service", "INFO", 
                      f"  ✓ Versand: {len(shipping_responses)}, Preise: {len(amount_responses)}")
    
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
