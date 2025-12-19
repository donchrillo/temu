import pyodbc
from typing import List, Dict, Any


class InventoryRepository:
    def __init__(self, connection: pyodbc.Connection):
        self.conn = connection

    def upsert_inventory(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        inserted, updated = 0, 0
        cursor = self.conn.cursor()
        for it in items:
            cursor.execute(
                """
MERGE temu_inventory AS t
USING (SELECT ? AS product_id, ? AS jtl_article_id, ? AS jtl_stock) AS s
ON t.product_id = s.product_id
WHEN MATCHED THEN UPDATE SET jtl_article_id = s.jtl_article_id, jtl_stock = s.jtl_stock,
    needs_sync = CASE WHEN s.jtl_stock <> t.temu_stock THEN 1 ELSE 0 END, updated_at = GETDATE()
WHEN NOT MATCHED THEN INSERT (product_id, jtl_article_id, jtl_stock, temu_stock, needs_sync)
    VALUES (s.product_id, s.jtl_article_id, s.jtl_stock, s.jtl_stock, 0);
""",
                it["product_id"], it.get("jtl_article_id"), it.get("jtl_stock", 0)
            )
            if cursor.rowcount == 1:
                inserted += 1
            else:
                updated += 1
        self.conn.commit()
        return {"inserted": inserted, "updated": updated}

    def get_needs_sync(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT inv.id, inv.product_id, inv.jtl_stock, inv.temu_stock,
                      p.goods_id, p.sku_id, p.sku
               FROM temu_inventory inv
               JOIN temu_products p ON inv.product_id = p.id
               WHERE inv.needs_sync = 1 AND p.is_active = 1"""
        )
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def mark_synced(self, updates: List[Dict[str, int]]) -> None:
        if not updates:
            return
        cursor = self.conn.cursor()
        for upd in updates:
            cursor.execute(
                "UPDATE temu_inventory SET temu_stock = ?, needs_sync = 0, last_synced_to_temu = GETDATE(), updated_at = GETDATE() WHERE id = ?",
                upd["temu_stock"], upd["id"]
            )
        self.conn.commit()
