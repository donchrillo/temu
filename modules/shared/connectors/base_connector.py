"""Base Connector - Abstract Base Class für alle Marketplace Connectors"""

from abc import ABC, abstractmethod
from typing import Dict, List

class BaseMarketplaceConnector(ABC):
    """
    Abstract Base Class für Marketplace Connectors
    
    Jeder Marketplace (TEMU, Amazon, eBay, etc.) muss diese Schnittstelle implementieren.
    Das macht es einfach, neue Marktplätze hinzuzufügen!
    """
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validiere API Credentials"""
        pass
    
    @abstractmethod
    def fetch_orders(self, **kwargs) -> bool:
        """Hole Orders vom Marketplace und speichere lokal"""
        pass
    
    @abstractmethod
    def fetch_shipping_info(self, order_id: str) -> Dict:
        """Hole Versandinformationen für eine Order"""
        pass
    
    @abstractmethod
    def upload_tracking(self, tracking_data: List[Dict]) -> bool:
        """Upload Tracking-Daten zurück zum Marketplace"""
        pass
