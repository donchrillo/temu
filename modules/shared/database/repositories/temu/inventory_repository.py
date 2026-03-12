"""Inventory Repository - SQLAlchemy + Raw SQL (Final & Optimized)"""

from typing import List, Dict, Any
from sqlalchemy import text
from .._log_helper import get_log_service as _get_log_service
from ...connection import get_engine
from ....config.settings import DB_TOCI
from ..base import BaseRepository

class InventoryRepository(BaseRepository):
    def upsert_inventory(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Upsert inventory items via MERGE.
        Optimiert: Nutzt EINE Transaktion für alle Items (Batch).
        """
        inserted, updated = 0, 0
        sql = text("""
            MERGE temu_inventory AS t
            USING (SELECT :product_id AS product_id, :jtl_article_id AS jtl_article_id, 
                          :jtl_stock AS jtl_stock) AS s
            ON t.product_id = s.product_id
            WHEN MATCHED THEN UPDATE SET 
                jtl_article_id = s.jtl_article_id, 
                jtl_stock = s.jtl_stock,
                needs_sync = CASE WHEN s.jtl_stock <> t.temu_stock THEN 1 ELSE 0 END, 
                updated_at = GETDATE()
            WHEN NOT MATCHED THEN INSERT (product_id, jtl_article_id, jtl_stock, temu_stock, needs_sync)
                VALUES (s.product_id, s.jtl_article_id, s.jtl_stock, 0, 1);
        """)

        try:
            # Helper Funktion für die innere Logik (damit wir den Loop nicht doppelt schreiben müssen)
            def process_items(conn):
                processed = 0
                for it in items:
                    params = {
                        "product_id": it["product_id"],
                        "jtl_article_id": it.get("jtl_article_id"),
                        "jtl_stock": it.get("jtl_stock", 0)
                    }
                    result = conn.execute(sql, params)
                    
                    # MERGE liefert rowcount=1 sowohl bei INSERT als auch UPDATE
                    if result.rowcount > 0:
                        processed += 1
                return processed

            if self._conn:
                # Wir sind bereits in einer Transaktion
                processed = process_items(self._conn)
            else:
                # EIGENE Transaktion öffnen, aber NUR EINMAL für alle Items!
                engine = get_engine(DB_TOCI)
                with engine.connect() as conn:
                    with conn.begin(): # Explizite Transaktion starten
                        processed = process_items(conn)
                        # Commit passiert automatisch am Ende von conn.begin() wenn kein Fehler
            
            return {"processed": processed}

        except Exception as e:
            _get_log_service().log("SYSTEM_ERROR", "inventoryrepository" , "ERROR", f"InventoryRepository upsert_inventory: {e}")
            return {"processed": 0}

    def get_needs_sync(self) -> List[Dict[str, Any]]:
        """Get inventory items that need sync"""
        try:
            sql = text("""
                SELECT inv.id, inv.product_id, inv.jtl_stock, inv.temu_stock,
                       p.goods_id, p.sku_id, p.sku
                FROM temu_inventory inv
                JOIN temu_products p ON inv.product_id = p.id
                WHERE inv.needs_sync = 1 AND p.is_active = 1
            """)
            rows = self._fetch_all(sql)
            return [dict(row._mapping) for row in rows]
        except Exception as e:
            _get_log_service().log("SYSTEM_ERROR", "inventoryrepository" , "ERROR", f"InventoryRepository get_needs_sync: {e}")
            return []

    def mark_synced(self, items: List[Dict[str, Any]]) -> int:
        """
        Mark inventory items as synced and UPDATE temu_stock.
        Nutzt Batch-Update (executemany) für maximale Performance.
        
        Args:
            items: Liste von Dicts [{'id': 1, 'temu_stock': 5}, ...]
        """
        if not items:
            return 0
        
        try:
            # WICHTIG: Wir setzen temu_stock = :temu_stock (der neue Wert aus JTL),
            # damit needs_sync beim nächsten Check 0 bleibt.
            sql = """
                UPDATE temu_inventory 
                SET needs_sync = 0, 
                    temu_stock = :temu_stock,
                    last_synced_to_temu = GETDATE(),
                    updated_at = GETDATE()
                WHERE id = :id
            """
            
            # Explizites Loop statt implizites executemany
            # (executemany über _execute_stmt ist undokumentierter Seiteneffekt)
            for item in items:
                self._execute_stmt(sql, {"id": item["id"], "temu_stock": item["temu_stock"]})
            
            return len(items)
            
        except Exception as e:
            _get_log_service().log("SYSTEM_ERROR", "inventoryrepository" , "ERROR", f"InventoryRepository mark_synced: {e}")
            return 0