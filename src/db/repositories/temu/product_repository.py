"""Product Repository - SQLAlchemy + Raw SQL (FIXED)"""

from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.engine import Connection
from src.services.logger import app_logger
from src.db.connection import get_engine
from config.settings import DB_TOCI


class ProductRepository:
    def __init__(self, connection: Any = None):
        """Optional injektierte Connection"""
        self._conn = connection

    def upsert_products(self, products: List[Dict[str, Any]]) -> Dict[str, int]:
        """Upsert products via MERGE"""
        inserted, updated = 0, 0
        try:
            for p in products:
                if self._conn:
                    result = self._conn.execute(text("""
                        MERGE temu_products AS target
                        USING (SELECT :sku AS sku, :goods_id AS goods_id, :sku_id AS sku_id, 
                                      :goods_name AS goods_name, :jtl_article_id AS jtl_article_id, 
                                      :is_active AS is_active) AS src
                        ON target.sku = src.sku
                        WHEN MATCHED THEN UPDATE SET 
                            goods_id = src.goods_id, sku_id = src.sku_id, 
                            goods_name = src.goods_name,
                            jtl_article_id = src.jtl_article_id, is_active = src.is_active, 
                            updated_at = GETDATE()
                        WHEN NOT MATCHED THEN INSERT (sku, goods_id, sku_id, goods_name, jtl_article_id, is_active)
                            VALUES (src.sku, src.goods_id, src.sku_id, src.goods_name, src.jtl_article_id, src.is_active);
                    """), {
                        "sku": p.get("sku"),
                        "goods_id": p.get("goods_id"),
                        "sku_id": p.get("sku_id"),
                        "goods_name": p.get("goods_name"),
                        "jtl_article_id": p.get("jtl_article_id"),
                        "is_active": p.get("is_active", 1)
                    })
                else:
                    with get_engine(DB_TOCI).connect() as conn:
                        result = conn.execute(text("""
                            MERGE temu_products AS target
                            USING (SELECT :sku AS sku, :goods_id AS goods_id, :sku_id AS sku_id, 
                                          :goods_name AS goods_name, :jtl_article_id AS jtl_article_id, 
                                          :is_active AS is_active) AS src
                            ON target.sku = src.sku
                            WHEN MATCHED THEN UPDATE SET 
                                goods_id = src.goods_id, sku_id = src.sku_id, 
                                goods_name = src.goods_name,
                                jtl_article_id = src.jtl_article_id, is_active = src.is_active, 
                                updated_at = GETDATE()
                            WHEN NOT MATCHED THEN INSERT (sku, goods_id, sku_id, goods_name, jtl_article_id, is_active)
                                VALUES (src.sku, src.goods_id, src.sku_id, src.goods_name, src.jtl_article_id, src.is_active);
                        """), {
                            "sku": p.get("sku"),
                            "goods_id": p.get("goods_id"),
                            "sku_id": p.get("sku_id"),
                            "goods_name": p.get("goods_name"),
                            "jtl_article_id": p.get("jtl_article_id"),
                            "is_active": p.get("is_active", 1)
                        })
                        conn.commit()
                
                if result.rowcount == 1:
                    inserted += 1
                else:
                    updated += 1
            return {"inserted": inserted, "updated": updated}
        except Exception as e:
            app_logger.error(f"ProductRepository upsert_products: {e}", exc_info=True)
            return {"inserted": 0, "updated": 0}

    def deactivate_missing(self, active_skus: List[str]) -> int:
        """Deactivate products not in active_skus"""
        if not active_skus:
            return 0
        
        try:
            sql = """
                UPDATE temu_products SET is_active = 0, updated_at = GETDATE()
                WHERE sku NOT IN (:skus)
            """
            
            if self._conn:
                result = self._conn.execute(text(sql), {"skus": tuple(active_skus)})
            else:
                with get_engine(DB_TOCI).connect() as conn:
                    result = conn.execute(text(sql), {"skus": tuple(active_skus)})
                    conn.commit()
            
            return result.rowcount
        except Exception as e:
            app_logger.error(f"ProductRepository deactivate_missing: {e}", exc_info=True)
            return 0

    def fetch_all(self) -> List[Dict]:
        """Fetch all products"""
        try:
            if self._conn:
                result = self._conn.execute(text("SELECT id, sku, goods_id, sku_id, goods_name, jtl_article_id, is_active FROM temu_products"))
            else:
                with get_engine(DB_TOCI).connect() as conn:
                    result = conn.execute(text("SELECT id, sku, goods_id, sku_id, goods_name, jtl_article_id, is_active FROM temu_products"))
            
            return [dict(row) for row in result.mappings().all()] if hasattr(result, 'mappings') else result.all()
        except Exception as e:
            app_logger.error(f"ProductRepository fetch_all: {e}", exc_info=True)
            return []

    def update_jtl_article_id(self, sku: str, jtl_article_id: int) -> bool:
        """Update JTL article ID for a product"""
        try:
            sql = "UPDATE temu_products SET jtl_article_id = :jtl_id, updated_at = GETDATE() WHERE sku = :sku"
            
            if self._conn:
                self._conn.execute(text(sql), {"jtl_id": jtl_article_id, "sku": sku})
            else:
                with get_engine(DB_TOCI).connect() as conn:
                    conn.execute(text(sql), {"jtl_id": jtl_article_id, "sku": sku})
                    conn.commit()
            
            return True
        except Exception as e:
            app_logger.error(f"ProductRepository update_jtl_article_id: {e}", exc_info=True)
            return False
