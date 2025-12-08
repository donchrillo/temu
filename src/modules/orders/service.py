"""Order Service - Business Logic (SIMPLIFIZIERT)"""

from typing import List, Dict, Optional
from datetime import datetime
from src.db.repositories.order_repository import OrderRepository, Order
from src.db.repositories.order_item_repository import OrderItemRepository, OrderItem

class OrderService:
    """Business Logic für Orders"""
    
    def __init__(self, order_repo: OrderRepository = None,
                 item_repo: OrderItemRepository = None):
        self.order_repo = order_repo or OrderRepository()
        self.item_repo = item_repo or OrderItemRepository()
    
    def import_from_api_response(self, api_responses: List[Dict]) -> Dict:
        """
        Importiere Orders + Items aus API Responses
        
        SIMPLIFIZIERT: Nur was wirklich nötig ist
        """
        imported_count = 0
        updated_count = 0
        
        for response in api_responses:
            if not response.get('success'):
                continue
            
            result = response.get('result', {})
            parent_order_map = result.get('parentOrderMap', {})
            parent_order_sn = parent_order_map.get('parentOrderSn')
            
            if not parent_order_sn:
                continue
            
            # Prüfe ob Order existiert
            existing_order = self.order_repo.find_by_bestell_id(parent_order_sn)
            
            # Parse zu Order
            order = Order(
                id=existing_order.id if existing_order else None,
                bestell_id=parent_order_sn,
                bestellstatus=self._map_status(parent_order_map.get('parentOrderStatus', 2)),
                kaufdatum=datetime.fromtimestamp(parent_order_map.get('parentOrderTime', 0)),
                status='importiert'
            )
            
            order_id = self.order_repo.save(order)
            
            if existing_order:
                updated_count += 1
            else:
                imported_count += 1
        
        return {
            'imported': imported_count,
            'updated': updated_count,
            'total': imported_count + updated_count
        }
    
    def _map_status(self, status_code: int) -> str:
        """Mapping Status Code zu String"""
        mapping = {1: 'pending', 2: 'processing', 3: 'cancelled', 4: 'shipped', 5: 'delivered'}
        return mapping.get(status_code, 'unknown')
