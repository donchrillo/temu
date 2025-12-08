"""TEMU Marketplace Service - API Integration Layer"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict
from config.settings import DATA_DIR
from src.marketplace_connectors.temu.api_client import TemuApiClient
from src.marketplace_connectors.temu.orders_api import TemuOrdersApi
from src.marketplace_connectors.base_connector import BaseMarketplaceConnector

API_RESPONSE_DIR = DATA_DIR / 'api_responses'
API_RESPONSE_DIR.mkdir(exist_ok=True)

class TemuMarketplaceService(BaseMarketplaceConnector):
    """
    TEMU Marketplace Connector
    
    Implementiert BaseMarketplaceConnector für TEMU spezifische Integration.
    Verantwortlich für: API Kommunikation, JSON Speicherung, Authentifizierung
    """
    
    def __init__(self, app_key: str, app_secret: str, access_token: str, endpoint: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = access_token
        self.endpoint = endpoint
        
        self.client = TemuApiClient(app_key, app_secret, access_token, endpoint)
        self.orders_api = TemuOrdersApi(self.client)
    
    def validate_credentials(self) -> bool:
        """Validiere TEMU Credentials"""
        return all([self.app_key, self.app_secret, self.access_token])
    
    def fetch_orders(self, parent_order_status=0, days_back=7) -> bool:
        """
        Hole Orders von TEMU API und speichere lokal als JSON
        
        Args:
            parent_order_status: Order Status Filter
            days_back: Wie viele Tage zurück
        
        Returns:
            bool: True wenn erfolgreich
        """
        
        print("=" * 70)
        print("TEMU API → JSON (speichern)")
        print("=" * 70)
        
        # Validiere Credentials
        if not self.validate_credentials():
            print("✗ TEMU Credentials fehlen")
            return False
        
        # Berechne Timestamps
        now = datetime.now()
        create_before = int(now.timestamp())
        create_after = int((now - timedelta(days=days_back)).timestamp())
        
        print(f"✓ API Client erstellt")
        print(f"  Zeitraum: {days_back} Tage")
        print(f"  Status: {parent_order_status}\n")
        
        # Abrufe Orders
        print("→ Rufe Orders ab...")
        orders_response = self.orders_api.get_orders(
            page_number=1, 
            page_size=100, 
            parent_order_status=parent_order_status,
            createAfter=create_after,
            createBefore=create_before
        )
        
        if orders_response is None:
            print("✗ API Fehler")
            return False
        
        # Speichere Orders JSON
        orders_file = API_RESPONSE_DIR / 'api_response_orders.json'
        with open(orders_file, 'w', encoding='utf-8') as f:
            json.dump(orders_response, f, ensure_ascii=False, indent=2)
        print(f"✓ Orders gespeichert")
        
        # Extrahiere Orders
        orders = orders_response.get("result", {}).get("pageItems", [])
        
        if not orders:
            print("✓ Keine Orders gefunden\n")
            return True
        
        print(f"✓ {len(orders)} Orders gefunden")
        
        # Abrufe Versand- & Preisinformationen
        print("\n→ Rufe Versandinformationen ab...")
        shipping_responses = {}
        amount_responses = {}
        
        for order_item in orders:
            parent_order_map = order_item.get("parentOrderMap", {})
            parent_order_sn = parent_order_map.get("parentOrderSn")
            
            if not parent_order_sn:
                continue
            
            shipping_response = self.orders_api.get_shipping_info(parent_order_sn)
            if shipping_response:
                shipping_responses[parent_order_sn] = shipping_response
            
            amount_response = self.orders_api.get_order_amount(parent_order_sn)
            if amount_response:
                amount_responses[parent_order_sn] = amount_response
        
        # Speichere Zusammenfassungen
        shipping_file = API_RESPONSE_DIR / 'api_response_shipping_all.json'
        with open(shipping_file, 'w', encoding='utf-8') as f:
            json.dump(shipping_responses, f, ensure_ascii=False, indent=2)
        
        amount_file = API_RESPONSE_DIR / 'api_response_amount_all.json'
        with open(amount_file, 'w', encoding='utf-8') as f:
            json.dump(amount_responses, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Versandinformationen: {len(shipping_responses)}")
        print(f"✓ Preisinformationen: {len(amount_responses)}")
        print(f"\n{'='*70}\n")
        
        return True
    
    def fetch_shipping_info(self, order_id: str) -> Dict:
        """Hole Versandinformationen"""
        return self.orders_api.get_shipping_info(order_id)
    
    def upload_tracking(self, tracking_data) -> bool:
        """Upload Tracking-Daten"""
        success, error_code, error_msg = self.orders_api.upload_tracking_data(tracking_data)
        return success
