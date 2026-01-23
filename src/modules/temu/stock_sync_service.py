from typing import List, Dict
from src.services.log_service import log_service


class StockSyncService:
    """Koordiniert Stock-Sync zu TEMU API"""
    
    def __init__(self):
        pass
    
    def sync_deltas_to_temu(self, temu_inventory_api, inventory_repo, job_id: str) -> None:
        """
        Sendet Delta-Bestände an TEMU (nur needs_sync=1).
        
        Args:
            temu_inventory_api: TemuInventoryApi Instanz
            inventory_repo: InventoryRepository
            job_id: für Logging
        """
        deltas = inventory_repo.get_needs_sync()
        if not deltas:
            log_service.log(job_id, "inventory_to_api", "INFO", "Keine Deltas zu synchronisieren")
            return
        
        # Gruppiere nach goodsId (jede goodsId ein API-Call)
        by_goods_id: Dict[int, List] = {}
        skipped = 0
        for d in deltas:
            goods_id = d.get("goods_id")
            sku_id = d.get("sku_id")
            if not goods_id or not sku_id:
                skipped += 1
                continue
            if goods_id not in by_goods_id:
                by_goods_id[goods_id] = []
            by_goods_id[goods_id].append(d)

        if skipped:
            log_service.log(job_id, "inventory_to_api", "WARNING", 
                          f"Überspringe {skipped} Einträge ohne goods_id/sku_id")
        
        synced_ids: List[int] = []
        for goods_id, items in by_goods_id.items():
            payload_items = [
                {
                    "goodsId": goods_id,
                    "skuId": it["sku_id"],
                    "stockTarget": it["jtl_stock"]
                } for it in items
            ]
            resp = temu_inventory_api.update_stock_target(payload_items, stock_type=0, job_id=job_id)
            
            if resp and resp.get("success"):
                synced_ids.extend([it["id"] for it in items])
                log_service.log(job_id, "inventory_to_api", "INFO", 
                              f"✓ goodsId {goods_id}: {len(items)} SKUs aktualisiert")
            else:
                log_service.log(job_id, "inventory_to_api", "ERROR", 
                              f"✗ goodsId {goods_id}: {resp}")
        
        if synced_ids:
            updates = [{"id": d["id"], "temu_stock": d["jtl_stock"]} for d in deltas if d["id"] in synced_ids]
            inventory_repo.mark_synced(updates)
            log_service.log(job_id, "inventory_to_api", "INFO", 
                          f"✓ {len(synced_ids)} Bestände aktualisiert")
