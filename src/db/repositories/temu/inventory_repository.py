"""Inventory Repository - SQLAlchemy + Raw SQL (Final & Optimized)"""

from typing import List, Dict, Any
from sqlalchemy import text, bindparam
from sqlalchemy.engine import Connection
from src.services.logger import app_logger
from src.db.connection import get_engine
from config.settings import DB_TOCI

class InventoryRepository:
    def __init__(self, connection: Any = None):
        """Optional injektierte Connection"""
        self._conn = connection

    def _execute_sql(self, sql, params=None):
        """Standard Helper für einfache Queries"""
        if params is None:
            params = {}
        
        if self._conn:
            return self._conn.execute(sql, params)
        else:
            engine = get_engine(DB_TOCI)
            with engine.connect() as conn:
                result = conn.execute(sql, params)
                conn.commit()
                return result

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
                jtl_article_id = s.jtl_article_id, jtl_stock = s.jtl_stock,
                needs_sync = CASE WHEN s.jtl_stock <> t.temu_stock THEN 1 ELSE 0 END, 
                updated_at = GETDATE()
            WHEN NOT MATCHED THEN INSERT (product_id, jtl_article_id, jtl_stock, temu_stock, needs_sync)
                VALUES (s.product_id, s.jtl_article_id, s.jtl_stock, s.jtl_stock, 0);
        """)

        try:
            # Helper Funktion für die innere Logik (damit wir den Loop nicht doppelt schreiben müssen)
            def process_items(conn):
                ins, upd = 0, 0
                for it in items:
                    params = {
                        "product_id": it["product_id"],
                        "jtl_article_id": it.get("jtl_article_id"),
                        "jtl_stock": it.get("jtl_stock", 0)
                    }
                    result = conn.execute(sql, params)
                    
                    # Hinweis: MERGE liefert rowcount=1 sowohl bei INSERT als auch UPDATE.
                    # Eine genaue Unterscheidung ist ohne OUTPUT Clause im SQL schwierig.
                    # Wir zählen hier einfach als "processed".
                    if result.rowcount > 0:
                        upd += 1 # Wir zählen es pauschal als Update/Upsert
                return ins, upd

            if self._conn:
                # Wir sind bereits in einer Transaktion
                inserted, updated = process_items(self._conn)
            else:
                # EIGENE Transaktion öffnen, aber NUR EINMAL für alle Items!
                engine = get_engine(DB_TOCI)
                with engine.connect() as conn:
                    with conn.begin(): # Explizite Transaktion starten
                        inserted, updated = process_items(conn)
                        # Commit passiert automatisch am Ende von conn.begin() wenn kein Fehler
            
            return {"inserted": inserted, "updated": updated}

        except Exception as e:
            app_logger.error(f"InventoryRepository upsert_inventory: {e}", exc_info=True)
            return {"inserted": 0, "updated": 0}

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

            if self._conn:
                result = self._conn.execute(sql)
                return [dict(row) for row in result.mappings().all()]
            else:
                engine = get_engine(DB_TOCI)
                with engine.connect() as conn:
                    result = conn.execute(sql)
                    return [dict(row) for row in result.mappings().all()]

        except Exception as e:
            app_logger.error(f"InventoryRepository get_needs_sync: {e}", exc_info=True)
            return []

    def mark_synced(self, inventory_ids: List[int]) -> int:
        """Mark inventory items as synced"""
        if not inventory_ids:
            return 0
        
        try:
            # WICHTIG: 'expanding=True' erlaubt es, Listen an IN-Clauses zu übergeben
            # Extrahiere nur die IDs aus den Dict-Objekten (die kommen vom upsert_inventory)
            if isinstance(inventory_ids, list) and len(inventory_ids) > 0:
                if isinstance(inventory_ids[0], dict):
                    inventory_ids_only = [item.get('id') for item in inventory_ids]
                else:
                    inventory_ids_only = list(inventory_ids)
            else:
                inventory_ids_only = list(inventory_ids)
            
            sql = text("""
                UPDATE temu_inventory SET needs_sync = 0, updated_at = GETDATE()
                WHERE id IN :ids
            """).bindparams(bindparam('ids', expanding=True))
            
            # Hier reicht unser einfacher _execute_sql Helper
            result = self._execute_sql(sql, {"ids": inventory_ids_only})
            return result.rowcount
            
        except Exception as e:
            app_logger.error(f"InventoryRepository mark_synced: {e}", exc_info=True)
            return 0