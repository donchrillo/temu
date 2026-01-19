"""TEMU API Client - Base Class"""

import requests
import json
import time
from typing import Optional
from src.marketplace_connectors.temu.signature import calculate_signature
from src.services.log_service import log_service

class TemuApiClient:
    """Base Client für TEMU Open API"""
    
    def __init__(self, app_key, app_secret, access_token, endpoint, verbose: bool = False):
        """
        Initialisiert den API Client.
        
        Args:
            app_key: TEMU_APP_KEY
            app_secret: TEMU_APP_SECRET
            access_token: TEMU_ACCESS_TOKEN
            endpoint: TEMU_API_ENDPOINT
            verbose: Debug Output (Payload + Response)
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = access_token
        self.endpoint = endpoint
        self.data_type = "JSON"
        self.verbose = verbose
    
    def call(self, api_type, request_params=None, job_id: Optional[str] = None):
        """
        Ruft TEMU API auf.
        
        Args:
            api_type: API-Typ (z.B. 'bg.order.list.v2.get')
            request_params: Dict mit zusätzlichen Parametern
            job_id: Optional - für strukturiertes Logging
        
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
            if job_id:
                log_service.log(job_id, "temu_api", "INFO", f"→ API Call: {api_type}")
            
            # ===== DEBUG: Nur wenn --verbose! =====
            if self.verbose and job_id:
                log_service.log(job_id, "temu_api", "DEBUG", 
                              f"Payload: {json.dumps(payload, indent=2, default=str)}")
            
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            response_json = response.json()
            
            # ===== DEBUG: Nur wenn --verbose! =====
            if self.verbose and job_id:
                log_service.log(job_id, "temu_api", "DEBUG", 
                              f"Response: {json.dumps(response_json, indent=2, default=str)}")
            
            # Prüfe auf API-Fehler
            if not response_json.get("success", False):
                error_code = response_json.get("errorCode", "?")
                error_msg = response_json.get("errorMsg", "Unbekannter Fehler")
                if job_id:
                    log_service.log(job_id, "temu_api", "ERROR", 
                                  f"API Fehler ({error_code}): {error_msg}")
                else:
                    print(f"✗ API Fehler ({error_code}): {error_msg}")
                return None
            
            if job_id:
                log_service.log(job_id, "temu_api", "INFO", "✓ Response erfolgreich")
            
            return response_json
        
        except requests.exceptions.RequestException as e:
            error_msg = f"Request Fehler: {str(e)}"
            if job_id:
                log_service.log(job_id, "temu_api", "ERROR", error_msg)
                if self.verbose:
                    import traceback
                    log_service.log(job_id, "temu_api", "ERROR", traceback.format_exc())
            else:
                print(f"✗ {error_msg}")
            return None
        
        except json.JSONDecodeError as e:
            error_msg = f"JSON Decode Fehler: {str(e)}"
            if job_id:
                log_service.log(job_id, "temu_api", "ERROR", error_msg)
            else:
                print(f"✗ {error_msg}")
            return None