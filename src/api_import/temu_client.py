"""TEMU API Client - Base Class"""

import requests
import json
import time
from src.api_import.temu_signature import calculate_signature

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
            API-Response als Dict oder None bei Fehler
        """
        
        if request_params is None:
            request_params = {}
        
        # Common Parameters
        common_params = {
            "app_key": self.app_key,
            "data_type": self.data_type,
            "access_token": self.access_token,
            "timestamp": int(time.time()),
            "type": api_type,
            "version": "V1"
        }
        
        # Merge Parameters
        all_params = {**common_params, **request_params}
        
        # Berechne Signatur
        sign = calculate_signature(self.app_secret, all_params)
        
        # Erstelle Payload
        payload = {
            **all_params,
            "sign": sign
        }
        
        # Sende Request
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            print(f"  → API Call: {api_type}")
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            response_json = response.json()
            
            # Prüfe auf API-Fehler
            if not response_json.get("success", False):
                error_code = response_json.get("errorCode", "?")
                error_msg = response_json.get("errorMsg", "Unbekannter Fehler")
                print(f"  ✗ API Fehler (Code {error_code}): {error_msg}")
                return None
            
            print(f"  ✓ Response erhalten")
            return response_json
        
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Request Fehler: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON Decode Fehler: {e}")
            return None
