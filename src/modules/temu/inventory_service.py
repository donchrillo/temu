import json
from typing import Dict, Any, List
from pathlib import Path
from config.settings import DATA_DIR
from src.services.log_service import log_service


class InventoryService:
    """Business Logic - Verarbeitet Inventory-Daten"""
    
    def __init__(self):
        self.api_response_dir = DATA_DIR / 'api_responses'
    
    def fetch_and_store_raw_skus(self, temu_inventory_api, job_id: str) -> bool:
        """
        Holt SKU-Listen von TEMU API (Status 2 & 3) und speichert lokal.
        
        Args:
            temu_inventory_api: TemuInventoryApi Instanz
            job_id: für Logging
        
        Returns:
            True wenn erfolgreich
        """
        self.api_response_dir.mkdir(parents=True, exist_ok=True)
        ok = True
        
        for status in (2, 3):
            page_no = 1
            status_file = self.api_response_dir / f"temu_sku_status{status}.json"
            all_items = []
            
            while True:
                resp = temu_inventory_api.get_sku_list(
                    status=status, page_no=page_no, page_size=100, job_id=job_id
                )
                if not resp or not resp.get("success"):
                    ok = False
                    break
                
                result = resp.get("result", {}) or {}
                sku_list = result.get("skuList", []) or []
                all_items.extend(sku_list)
                
                total = result.get("total", len(all_items))
                if len(all_items) >= total or not sku_list:
                    break
                page_no += 1
            
            status_file.write_text(
                json.dumps({"result": {"skuList": all_items, "total": len(all_items)}}, indent=2),
                encoding="utf-8"
            )
            log_service.log(job_id, "api_to_json", "INFO", 
                          f"SKU-Status {status} gespeichert ({len(all_items)} Einträge)")
        return ok
    
    def import_products_from_raw(self, product_repo, job_id: str) -> Dict[str, int]:
        """
        Importiert SKU-JSON in temu_products mit Mapping.
        
        Args:
            product_repo: ProductRepository
            job_id: für Logging
        
        Returns:
            {"inserted": n, "updated": n}
        """
        files = list(self.api_response_dir.glob("temu_sku_status*.json"))
        products: List[Dict[str, Any]] = []
        
        for fp in files:
            data = json.loads(fp.read_text(encoding="utf-8"))
            for sku in data.get("result", {}).get("skuList", []):
                products.append({
                    "sku": sku.get("skuSn"),
                    "goods_id": sku.get("goodsId"),
                    "sku_id": sku.get("skuId"),
                    "goods_name": sku.get("goodsName"),
                    "jtl_article_id": None,
                    "is_active": 1
                })
        
        if not products:
            return {"inserted": 0, "updated": 0}
        
        result = product_repo.upsert_products(products)
        log_service.log(job_id, "json_to_db", "INFO", 
                      f"Produkte: {result['inserted']} neu, {result['updated']} aktualisiert")
        return result
    
    def refresh_inventory_from_jtl(self, product_repo, inventory_repo, jtl_repo, job_id: str) -> Dict[str, int]:
        """
        Liest JTL-Bestände und aktualisiert temu_inventory.
        """
        products = product_repo.fetch_all()
        items = []
        
        for p in products:
            sku = p.get("sku")
            
            # Hole JTL Artikel-ID per SKU (falls noch nicht gemappt)
            if not p.get("jtl_article_id") and sku:
                jtl_article_id = jtl_repo.get_article_id_by_sku(sku)
                if jtl_article_id:
                    product_repo.update_jtl_article_id(p["id"], jtl_article_id)
                    p["jtl_article_id"] = jtl_article_id
            
            # Hole JTL Bestand per Artikel-ID
            jtl_stock = 0
            if p.get("jtl_article_id"):
                jtl_stock = jtl_repo.get_stock_by_article_id(p["jtl_article_id"])
            
            items.append({
                "product_id": p["id"],
                "jtl_article_id": p.get("jtl_article_id"),
                "jtl_stock": jtl_stock
            })
        
        if not items:
            return {"inserted": 0, "updated": 0}
        
        result = inventory_repo.upsert_inventory(items)
        log_service.log(job_id, "jtl_to_inventory", "INFO", 
                      f"Bestände: {result['inserted']} neu, {result['updated']} aktualisiert")
        return result