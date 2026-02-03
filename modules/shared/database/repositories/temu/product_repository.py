"""Product Repository - SQLAlchemy + Raw SQL (Final & Optimized)"""

from typing import List, Dict, Any
from sqlalchemy import text
# Lazy import to avoid circular dependency
def _get_log_service():
    from ...logging.log_service import log_service
    return log_service
from ...connection import get_engine
from ....config.settings import DB_TOCI
from ..base import BaseRepository

class ProductRepository(BaseRepository):
    def upsert_products(self, products: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Upsert products via MERGE.
        Optimiert: Nutzt EINE Transaktion für alle Items.
        """
        inserted, updated = 0, 0
        
        # SQL Statement einmal definieren
        sql = text("""
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
        """)

        try:
            # Innere Logik zum Ausführen des Loops (vermeidet Code-Duplizierung)
            def process_batch(conn):
                ins, upd = 0, 0
                for p in products:
                    params = {
                        "sku": p.get("sku"),
                        "goods_id": p.get("goods_id"),
                        "sku_id": p.get("sku_id"),
                        "goods_name": p.get("goods_name"),
                        "jtl_article_id": p.get("jtl_article_id"),
                        "is_active": p.get("is_active", 1)
                    }
                    result = conn.execute(sql, params)
                    
                    if result.rowcount > 0:
                        upd += 1 # Merge liefert rowcount > 0 bei Insert & Update
                return ins, upd

            if self._conn:
                inserted, updated = process_batch(self._conn)
            else:
                engine = get_engine(DB_TOCI)
                with engine.connect() as conn:
                    with conn.begin(): # Transaktion starten
                        inserted, updated = process_batch(conn)
            
            return {"inserted": inserted, "updated": updated}

        except Exception as e:
            _get_log_service().log("SYSTEM_ERROR", "productrepository" , "ERROR", f"ProductRepository upsert_products: {e}")
            return {"inserted": 0, "updated": 0}

    def deactivate_missing(self, active_skus: List[str]) -> int:
        """Deactivate products not in active_skus"""
        if not active_skus:
            return 0
        
        try:
            # WICHTIG: expanding=True für Listen-Parameter
            sql = text("""
                UPDATE temu_products SET is_active = 0, updated_at = GETDATE()
                WHERE sku NOT IN :skus
            """).bindparams(bindparam('skus', expanding=True))
            
            result = self._execute_stmt(sql, {"skus": list(active_skus)})
            return result.rowcount
            
        except Exception as e:
            _get_log_service().log("SYSTEM_ERROR", "productrepository" , "ERROR", f"ProductRepository deactivate_missing: {e}")
            return 0

    def fetch_all(self) -> List[Dict]:
        """Fetch all products"""
        try:
            sql = text("SELECT id, sku, goods_id, sku_id, goods_name, jtl_article_id, is_active FROM temu_products")
            rows = self._fetch_all(sql)
            return [dict(row._mapping) for row in rows]
        except Exception as e:
            _get_log_service().log("SYSTEM_ERROR", "productrepository" , "ERROR", f"ProductRepository fetch_all: {e}")
            return []

    def update_jtl_article_id(self, product_id: int, jtl_article_id: int) -> bool:
        """Update JTL article ID for a product"""
        try:
            sql = text("UPDATE temu_products SET jtl_article_id = :jtl_id, updated_at = GETDATE() WHERE id = :product_id")
            self._execute_stmt(sql, {"jtl_id": jtl_article_id, "product_id": product_id})
            return True
        except Exception as e:
            _get_log_service().log("SYSTEM_ERROR", "productrepository" , "ERROR", f"ProductRepository update_jtl_article_id: {e}")
            return False