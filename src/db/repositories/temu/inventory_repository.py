"""Inventory Repository - SQLAlchemy + Raw SQL (FIXED)"""

from typing import List, Dict, Any
from sqlalchemy import text
from src.services.logger import app_logger
from src.db.connection import get_engine
from config.settings import DB_TOCI


class InventoryRepository:
    def __init__(self, connection: Any = None):
        """Optional injektierte Connection"""
        self._conn = connection

    def upsert_inventory(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Upsert inventory items via MERGE"""
        inserted, updated = 0, 0
        try:
            for it in items:
                if self._conn:
                    result = self._conn.execute(text("""
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
                else:
                    with get_engine(DB_TOCI).connect() as conn:
                        result = conn.execute(text("""
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
                        conn.commit()
                
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
            if self._conn:
                result = self._conn.execute(text("""
                    SELECT inv.id, inv.product_id, inv.jtl_stock, inv.temu_stock,
                           p.goods_id, p.sku_id, p.sku
                    FROM temu_inventory inv
                    JOIN temu_products p ON inv.product_id = p.id
                    WHERE inv.needs_sync = 1 AND p.is_active = 1
                """))
            else:
                with get_engine(DB_TOCI).connect() as conn:
                    result = conn.execute(text("""
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

    def mark_synced(self, inventory_ids: List[int]) -> int:
        """Mark inventory items as synced"""
        if not inventory_ids:
            return 0
        
        try:
            sql = """
                UPDATE temu_inventory SET needs_sync = 0, updated_at = GETDATE()
                WHERE id IN (:ids)
            """
            
            if self._conn:
                result = self._conn.execute(text(sql), {"ids": tuple(inventory_ids)})
            else:
                with get_engine(DB_TOCI).connect() as conn:
                    result = conn.execute(text(sql), {"ids": tuple(inventory_ids)})
                    conn.commit()
            
            return result.rowcount
        except Exception as e:
            app_logger.error(f"InventoryRepository mark_synced: {e}", exc_info=True)
            return 0
