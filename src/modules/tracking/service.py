"""Tracking Service - Business Logic (SIMPLIFIZIERT)"""

from typing import Dict
from db.connection import get_db_connection
from src.db.repositories.order_repository import OrderRepository
from config.settings import DB_JTL

class TrackingService:
    """Business Logic für Tracking"""
    
    def __init__(self, order_repo: OrderRepository = None):
        self.order_repo = order_repo or OrderRepository()
    
    def update_from_jtl(self) -> Dict:
        """
        Hole Trackingnummern aus JTL und update Orders
        SIMPLIFIZIERT: Nur Basis-Funktionalität
        """
        updated_count = 0
        not_found_count = 0
        
        # Hole Orders ohne Tracking
        orders = self.order_repo.find_by_status('importiert')
        
        for order in orders:
            if not order.bestell_id:
                continue
            
            # Hole Tracking aus JTL
            tracking_data = self._fetch_from_jtl(order.bestell_id)
            
            if tracking_data:
                self.order_repo.update_tracking(
                    order.id,
                    tracking_data['trackingnummer'],
                    tracking_data['versanddienstleister']
                )
                updated_count += 1
            else:
                not_found_count += 1
        
        return {'updated': updated_count, 'not_found': not_found_count}
    
    def _fetch_from_jtl(self, bestell_id: str) -> Dict:
        """Hole Tracking aus JTL"""
        try:
            conn = get_db_connection(DB_JTL)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT [cVersandartName], CAST([cTrackingId] AS VARCHAR(50))
                FROM [Versand].[lvLieferschein]
                JOIN [Versand].[lvLieferscheinpaket]
                    ON [Versand].[lvLieferscheinpaket].kLieferschein = 
                       [Versand].[lvLieferschein].kLieferschein
                WHERE cBestellungInetBestellNr = ?
            """, bestell_id)
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                return {
                    'versanddienstleister': result[0],
                    'trackingnummer': result[1]
                }
            return None
        except:
            return None
