"""Inventory Repository - SQLAlchemy + Raw SQL"""

from typing import List, Dict, Any
from sqlalchemy import text
from src.services.logger import app_logger


class InventoryRepository:
    def __init__(self, connection):
        self.conn = connection

    def upsert_inventory(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Upsert inventory items via MERGE"""
        inserted, updated = 0, 0
        try:
            for it in items:
                result = self.conn.execute(text("""
                    MERGE temu_inventory AS t
                    USING (SELECT :product_id AS product_id, :jtl_article_id AS jtl_article_id, 
                                  :jtl_stock AS jtl_stock) AS s
                    ON t.product_id = s.product_id
                    WHEN MATCHED THEN UPDATE SET 
                        jtl_article_id = s.jtl_article_id, jtl_stock = s.jtl_stock,
                        needs_sync = CASE WHEN s.jtl_stock <> t.temu_stock THEN 1 ELSE 0 END, 
                        updated_at = GETDATE()
                    WHEN NOT MATCHED THEN INSERT (product_id, jtl_article_id, jtl_stock, temu_stock, needs_sync)
                        VALUES (s.product_id, s.jtl_article_id, s.jtl_stock, s.jtl_stock, 0);
                """), {
                    "product_id": it["product_id"],
                    "jtl_article_id": it.get("jtl_article_id"),
                    "jtl_stock": it.get("jtl_stock", 0)
                })
                if result.rowcount == 1:
                    inserted += 1
                else:
                    updated += 1
            return {"inserted": inserted, "updated": updated}
        except Exception as e:
            app_logger.error(f"InventoryRepository upsert_inventory: {e}", exc_info=True)
            return {"inserted": 0, "updated": 0}

    def get_needs_sync(self) -> List[Dict[str, Any]]:
        """Get inventory items that need sync"""
        try:
            result = self.conn.execute(text("""
                SELECT inv.id, inv.product_id, inv.jtl_stock, inv.temu_stock,
                       p.goods_id, p.sku_id, p.sku
                FROM temu_inventory inv
                JOIN temu_products p ON inv.product_id = p.id
                WHERE inv.needs_sync = 1 AND p.is_active = 1
            """))
            return [dict(row) for row in result.mappings().all()]
        except Exception as e:
            app_logger.error(f"InventoryRepository get_needs_sync: {e}", exc_info=True)
            return []

    def mark_synced(self, updates: List[Dict[str, int]]) -> None:
        """Mark items as synced"""
        try:
            for upd in updates:
                self.conn.execute(text("""
                    UPDATE temu_inventory 
                    SET temu_stock = :temu_stock, needs_sync = 0, 
                        last_synced_to_temu = GETDATE(), updated_at = GETDATE() 
                    WHERE id = :id
                """), {"temu_stock": upd["temu_stock"], "id": upd["id"]})
        except Exception as e:
            app_logger.error(f"InventoryRepository mark_synced: {e}", exc_info=True)
