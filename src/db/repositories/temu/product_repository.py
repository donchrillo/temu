import pyodbc
from typing import List, Dict, Any


class ProductRepository:
    def __init__(self, connection: pyodbc.Connection):
        self.conn = connection

    def upsert_products(self, products: List[Dict[str, Any]]) -> Dict[str, int]:
        inserted, updated = 0, 0
        cursor = self.conn.cursor()
        for p in products:
            cursor.execute(
                """
MERGE temu_products AS target
USING (SELECT ? AS sku, ? AS goods_id, ? AS sku_id, ? AS goods_name, ? AS jtl_article_id, ? AS is_active) AS src
ON target.sku = src.sku
WHEN MATCHED THEN UPDATE SET goods_id = src.goods_id, sku_id = src.sku_id, goods_name = src.goods_name,
    jtl_article_id = src.jtl_article_id, is_active = src.is_active, updated_at = GETDATE()
WHEN NOT MATCHED THEN INSERT (sku, goods_id, sku_id, goods_name, jtl_article_id, is_active)
    VALUES (src.sku, src.goods_id, src.sku_id, src.goods_name, src.jtl_article_id, src.is_active);
""",
                p.get("sku"), p.get("goods_id"), p.get("sku_id"), p.get("goods_name"), p.get("jtl_article_id"), p.get("is_active", 1)
            )
            if cursor.rowcount == 1:
                inserted += 1
            else:
                updated += 1
        self.conn.commit()
        return {"inserted": inserted, "updated": updated}

    def deactivate_missing(self, active_skus: List[str]) -> int:
        if not active_skus:
            return 0
        cursor = self.conn.cursor()
        cursor.execute(
            f"UPDATE temu_products SET is_active = 0, updated_at = GETDATE() WHERE sku NOT IN ({','.join(['?']*len(active_skus))})",
            active_skus
        )
        self.conn.commit()
        return cursor.rowcount

    def fetch_all(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, sku, goods_id, sku_id, goods_name, jtl_article_id, is_active FROM temu_products")
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]
