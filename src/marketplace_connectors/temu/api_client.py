"""TEMU API Client - Base Class"""

import requests
import json
import time
from src.marketplace_connectors.temu.signature import calculate_signature

class TemuApiClient:
    """Base Client für TEMU Open API"""
    
    def __init__(self, app_key, app_secret, access_token, endpoint):
        """
        Initialisiert den API Client.
        
        Args:
            app_key: TEMU_APP_KEY
            app_secret: TEMU_APP_SECRET
            access_token: TEMU_ACCESS_TOKEN
            endpoint: TEMU_API_ENDPOINT (z.B. https://open.temuglobal.com)
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = access_token
        self.endpoint = endpoint
        self.data_type = "JSON"
    
    def call(self, api_type, request_params=None):
        """
        Ruft TEMU API auf.
        
        Args:
            api_type: API-Typ (z.B. 'bg.order.list.v2.get')
            request_params: Dict mit zusätzlichen Parametern
        
        Returns:
            API-Response als Dict (auch bei Fehlern!) oder None bei HTTP-Fehler
        """
        path = f"/{api_type}"
        return self._send_request("GET", path, data=request_params)
    
    def _get_headers(self):
        """Berechne und gebe die erforderlichen Header zurück"""
        timestamp = int(time.time() * 1000)
        signature = calculate_signature(self.app_key, self.app_secret, timestamp)
        
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "App-Key": self.app_key,
            "App-Signature": signature,
            "App-Timestamp": str(timestamp),
            "Authorization": f"Bearer {self.access_token}"
        }
    
    def _send_request(self, method, path, data=None):
        """Sende eine HTTP-Anfrage an die TEMU API"""
        url = f"{self.endpoint}{path}"
        headers = self._get_headers()
        
        response = requests.request(method, url, headers=headers, json=data)
        
        if response.status_code != 200:
            raise Exception(f"API Fehler: {response.status_code} - {response.text}")
        
        return response.json()
    
    def get_order(self, order_id):
        """Hole eine Bestellung"""
        path = f"/orders/{order_id}"
        return self._send_request("GET", path)
    
    def create_order(self, order_data):
        """Erstelle eine neue Bestellung"""
        path = "/orders"
        return self._send_request("POST", path, data=order_data)
    
    def update_order(self, order_id, order_data):
        """Aktualisiere eine bestehende Bestellung"""
        path = f"/orders/{order_id}"
        return self._send_request("PUT", path, data=order_data)
    
    def delete_order(self, order_id):
        """Lösche eine Bestellung"""
        path = f"/orders/{order_id}"
        return self._send_request("DELETE", path)