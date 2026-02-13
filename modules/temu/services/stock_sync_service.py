"""TEMU Stock Sync Service - Logic for API Upload"""

from typing import List, Dict
from modules.shared import log_service


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
        
        # Validierung: Filtere ungültige Einträge
        valid_deltas = []
        skipped = 0
        for d in deltas:
            if d.get("goods_id") and d.get("sku_id"):
                valid_deltas.append(d)
            else:
                skipped += 1
                
        if skipped:
            log_service.log(job_id, "inventory_to_api", "WARNING", 
                          f"Überspringe {skipped} Einträge ohne goods_id/sku_id")
            
        # Gruppiere nach goodsId (nötig für API-Endpunkt bg.local.goods.stock.edit)
        by_goods_id: Dict[int, List] = {}
        for d in valid_deltas:
            gid = d["goods_id"]
            if gid not in by_goods_id: 
                by_goods_id[gid] = []
            by_goods_id[gid].append(d)
            
        total_synced = 0
        
        # Sende Updates gruppiert
        for goods_id, items in by_goods_id.items():
            payload_items = [
                {
                    "skuId": it["sku_id"],
                    "stockTarget": it["jtl_stock"]
                } for it in items
            ]
            
            # API Call (Single Goods Format: goodsId im Header, Liste nur mit skuId)
            # Wir bauen hier eine Struktur, die update_stock_target versteht
            # update_stock_target erwartet eine Liste von Dicts, die intern geprüft wird.
            # Da wir jetzt gruppiert haben, können wir "goodsId" auch weglassen und der API
            # sagen "Nimm goodsId X für alle". Aber update_stock_target erwartet momentan
            # eine Liste von Items. Ich übergebe goodsId einfach im ersten Item oder separat?
            # Ich passe update_stock_target gleich an, dass es goodsId explizit nimmt?
            # NEIN, ich nutze die bestehende Signatur. Ich packe goodsId in jedes Item, 
            # damit die API-Methode (die ich gleich reverten werde) es einfach hat 
            # ODER ich übergebe es so, wie es vorher war.
            
            # Um API Änderungen minimal zu halten: Ich übergebe Items MIT goodsId.
            # Meine API-Methode (die ich gleich reverten werde) schaut aufs erste Item.
            # Die reverted API Methode schaut auch aufs erste Item. Passt.
            
            api_items = [
                {
                    "goodsId": goods_id,
                    "skuId": it["sku_id"],
                    "stockTarget": it["jtl_stock"]
                } for it in items
            ]
            
            resp = temu_inventory_api.update_stock_target(api_items, stock_type=0, job_id=job_id)
            
            if resp and resp.get("success"):
                # Sofort markieren
                batch_updates = [
                    {
                        "id": it["id"], 
                        "temu_stock": it["jtl_stock"]
                    } for it in items
                ]
                inventory_repo.mark_synced(batch_updates)
                
                total_synced += len(items)
                log_service.log(job_id, "inventory_to_api", "INFO", 
                              f"✓ goodsId {goods_id}: {len(items)} SKUs aktualisiert & markiert")
            else:
                error_info = resp.get("errorMsg") if resp else "Unbekannter Fehler"
                log_service.log(job_id, "inventory_to_api", "ERROR", 
                              f"✗ goodsId {goods_id} fehlgeschlagen: {error_info}")
        
        if total_synced > 0:
            log_service.log(job_id, "inventory_to_api", "INFO", 
                          f"Gesamt: {total_synced} / {len(valid_deltas)} SKUs erfolgreich synchronisiert")

