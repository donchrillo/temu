import json
from typing import Dict, Any, List
from pathlib import Path
from config.settings import TEMU_API_RESPONSES_DIR
from src.services.log_service import log_service


class InventoryService:
    """Business Logic - Verarbeitet Inventory-Daten"""
    
    def __init__(self):
        self.api_response_dir = TEMU_API_RESPONSES_DIR
    
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
                
                total = result.get("total") or len(all_items)
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
        Optimiert: Batch-Abfrage statt N+1 Queries.
        """
        products = product_repo.fetch_all()
        items_to_upsert = []
        
        # 1. Sammle alle JTL Artikel-IDs, die wir schon kennen
        known_jtl_ids = [p["jtl_article_id"] for p in products if p.get("jtl_article_id")]
        
        # 2. Batch-Abfrage der Bestände für alle bekannten IDs (nur 1-x SQL Queries statt 5000)
        stock_map = {}
        if known_jtl_ids:
            log_service.log(job_id, "jtl_to_inventory", "INFO", 
                          f"→ Lade Bestände für {len(known_jtl_ids)} Artikel im Batch...")
            stock_map = jtl_repo.get_stocks_by_article_ids(known_jtl_ids)
        
        for p in products:
            sku = p.get("sku")
            jtl_article_id = p.get("jtl_article_id")
            
            # Fall A: JTL ID fehlt -> Einzeln nachladen (passiert nur selten/initial)
            if not jtl_article_id and sku:
                jtl_article_id = jtl_repo.get_article_id_by_sku(sku)
                if jtl_article_id:
                    # Update Product Table sofort, damit wir es beim nächsten Mal haben
                    product_repo.update_jtl_article_id(p["id"], jtl_article_id)
                    # Wenn wir es gerade erst gefunden haben, müssen wir den Stock einzeln holen
                    stock = jtl_repo.get_stock_by_article_id(jtl_article_id)
                else:
                    stock = 0
            
            # Fall B: JTL ID bekannt -> Aus der Batch-Map holen (Superschnell)
            else:
                stock = stock_map.get(jtl_article_id, 0) if jtl_article_id else 0
            
            # Items für den Upsert vorbereiten
            items_to_upsert.append({
                "product_id": p["id"],
                "jtl_article_id": jtl_article_id,
                "jtl_stock": int(stock)  # Temu nimmt nur ganze Zahlen
            })
        
        if not items_to_upsert:
            return {"inserted": 0, "updated": 0}
        
        # 3. Batch-Upsert in temu_inventory
        result = inventory_repo.upsert_inventory(items_to_upsert)
        
        log_service.log(job_id, "jtl_to_inventory", "INFO", 
                      f"Bestände abgeglichen: {result['inserted']} neu, {result['updated']} aktualisiert")
        return result