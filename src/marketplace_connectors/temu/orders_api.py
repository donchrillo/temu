"""TEMU Orders API - Get Orders"""

from src.marketplace_connectors.temu.api_client import TemuApiClient

class TemuOrdersApi:
    """Orders API Endpoint"""
    
    def __init__(self, client):
        """
        Initialisiert Orders API.
        
        Args:
            client: TemuApiClient Instanz
        """
        self.client = client
    
    def get_orders(self, parent_order_status=2, days_back=7):
        """
        Hole Aufträge von TEMU API
        
        Args:
            parent_order_status: Order Status Filter (0=All, 1=PENDING, 2=UN_SHIPPING, etc.)
            days_back: Wie viele Tage zurück (Standard: 7 Tage)
        
        Returns:
            dict: API Response
        """
        # Beispielhafte Implementierung - anpassen je nach API Spezifikation
        endpoint = "/orders"
        params = {
            "status": parent_order_status,
            "days": days_back
        }
        
        response = self.client.get(endpoint, params=params)
        return response.json() if response and response.status_code == 200 else {}