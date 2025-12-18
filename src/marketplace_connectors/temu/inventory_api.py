"""TEMU Inventory API - Get SKU List & Update Stock"""

from typing import Optional, List, Dict
from src.marketplace_connectors.temu.api_client import TemuApiClient
from src.services.log_service import log_service


class TemuInventoryApi:
    """Inventory API Endpoints"""
    
    def __init__(self, client: TemuApiClient):
        """
        Initialisiert Inventory API.
        
        Args:
            client: TemuApiClient Instanz
        """
        self.client = client
    
    def get_sku_list(self, status: int, page_no: int = 1, page_size: int = 100, job_id: Optional[str] = None):
        """
        Holt SKU-Liste von TEMU API (Status 2 oder 3).
        
        Args:
            status: 2=Available, 3=Not available
            page_no: Seite (Standard: 1)
            page_size: Items pro Seite (Standard: 100, Max: 100)
            job_id: Optional - für strukturiertes Logging
        
        Returns:
            API-Response oder None bei Fehler
        """
        request_params = {
            "skuStatusFilterType": status,
            "pageNo": page_no,
            "pageSize": page_size
        }
        return self.client.call("bg.local.goods.sku.list.query", request_params, job_id=job_id)
    
    def update_stock_target(self, items: List[Dict[str, int]], stock_type: int = 0, job_id: Optional[str] = None):
        """
        Aktualisiert Bestand bei TEMU (full update via skuStockTargetList).
        
        Args:
            items: List mit {"skuId": <id>, "stockTarget": <qty>}
            stock_type: 0=ordinary, 1=pre-sale (Standard: 0)
            job_id: Optional - für strukturiertes Logging
        
        Returns:
            API-Response oder None bei Fehler
        """
        if not items:
            log_service.log(job_id, "inventory_api", "INFO", "Keine Items zum Update")
            return {"success": True}
        
        request_params = {
            "goodsId": items[0].get("goodsId") if items else None,
            "skuStockTargetList": [
                {
                    "skuId": it["skuId"],
                    "stockTarget": it["stockTarget"]
                } for it in items
            ],
            "stockType": stock_type
        }
        return self.client.call("bg.local.goods.stock.edit", request_params, job_id=job_id)
