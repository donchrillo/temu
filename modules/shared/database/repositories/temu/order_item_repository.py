"""OrderItem Repository - SQLAlchemy + Raw SQL (Final)"""

from typing import List, Optional
from sqlalchemy import text
from .._log_helper import get_log_service as _get_log_service
from ...connection import get_engine
from ....config.settings import TABLE_ORDER_ITEMS, DB_TOCI
from ..base import BaseRepository

# Domain Model - importiert aus zentraler models.py (Rückwärtskompatibel)
from .models import OrderItem

class OrderItemRepository(BaseRepository):
    """Data Access Layer - ONLY DB Operations"""

    # Zentrale Spaltenliste für SELECT-Queries (DRY)
    _ITEM_COLUMNS = """id, order_id, bestell_id, bestellartikel_id,
                       produktname, sku, sku_id, variation, menge,
                       netto_einzelpreis, brutto_einzelpreis,
                       gesamtpreis_netto, gesamtpreis_brutto, mwst_satz"""

    def save(self, item: OrderItem) -> int:
        """INSERT oder UPDATE OrderItem"""
        try:
            params = {
                "bestellartikel_id": item.bestellartikel_id,
                "produktname": item.produktname,
                "sku": item.sku,
                "sku_id": item.sku_id,
                "variation": item.variation,
                "menge": item.menge,
                "netto_einzelpreis": item.netto_einzelpreis,
                "brutto_einzelpreis": item.brutto_einzelpreis,
                "gesamtpreis_netto": item.gesamtpreis_netto,
                "gesamtpreis_brutto": item.gesamtpreis_brutto,
                "mwst_satz": item.mwst_satz
            }

            if item.id:
                # UPDATE - nutze _execute_stmt
                sql = f"""
                    UPDATE {TABLE_ORDER_ITEMS} SET
                        bestellartikel_id = :bestellartikel_id,
                        produktname = :produktname,
                        sku = :sku,
                        sku_id = :sku_id,
                        variation = :variation,
                        menge = :menge,
                        netto_einzelpreis = :netto_einzelpreis,
                        brutto_einzelpreis = :brutto_einzelpreis,
                        gesamtpreis_netto = :gesamtpreis_netto,
                        gesamtpreis_brutto = :gesamtpreis_brutto,
                        mwst_satz = :mwst_satz
                    WHERE id = :id
                """
                params["id"] = item.id
                self._execute_stmt(sql, params)
                return item.id
            else:
                # INSERT - Speziallogik für @@IDENTITY + Transaktions-Commit
                params.update({
                    "order_id": item.order_id,
                    "bestell_id": item.bestell_id
                })

                # OUTPUT inserted.id vermeidet Mehrfach-Resultsets und ResourceClosed bei pyodbc
                sql = f"""
                    INSERT INTO {TABLE_ORDER_ITEMS} (
                        order_id, bestell_id, bestellartikel_id, produktname,
                        sku, sku_id, variation, menge,
                        netto_einzelpreis, brutto_einzelpreis,
                        gesamtpreis_netto, gesamtpreis_brutto, mwst_satz
                    )
                    OUTPUT inserted.id AS new_id
                    VALUES (
                        :order_id, :bestell_id, :bestellartikel_id, :produktname,
                        :sku, :sku_id, :variation, :menge,
                        :netto_einzelpreis, :brutto_einzelpreis,
                        :gesamtpreis_netto, :gesamtpreis_brutto, :mwst_satz
                    );
                """
                
                # Manuelle Logik: Fetch BEVOR Connection zugeht
                if self._conn:
                    result = self._conn.execute(text(sql), params)
                    row = result.first()
                    return int(row[0]) if row else 0
                else:
                    with get_engine(DB_TOCI).connect() as conn:
                        result = conn.execute(text(sql), params)
                        row = result.first()
                        conn.commit()
                        return int(row[0]) if row else 0
        
        except Exception as e:
            # ✅ CRITICAL: Detailliertes Logging für Debugging
            bestellartikel_id = item.bestellartikel_id if item else "unknown"
            _get_log_service().log("SYSTEM_ERROR", "orderitem_repository" , "ERROR", f"OrderItemRepository save FAILED for item {bestellartikel_id}: {e}")
            return 0

    def find_by_order_id(self, order_id: int) -> List[OrderItem]:
        """Hole alle Items für Order"""
        try:
            sql = f"""
                SELECT {self._ITEM_COLUMNS}
                FROM {TABLE_ORDER_ITEMS}
                WHERE order_id = :order_id
            """
            rows = self._fetch_all(sql, {"order_id": order_id})
            return [self._map_to_item(row) for row in rows]
        except Exception as e:
            _get_log_service().log("SYSTEM_ERROR", "orderitem_repository" , "ERROR", f"OrderItemRepository find_by_order_id: {e}")
            return []
    
    def find_by_bestell_id(self, bestell_id: str) -> List[OrderItem]:
        """Hole alle Items für eine Bestellung (via bestell_id)"""
        try:
            sql = f"""
                SELECT {self._ITEM_COLUMNS}
                FROM {TABLE_ORDER_ITEMS}
                WHERE bestell_id = :bestell_id
            """
            rows = self._fetch_all(sql, {"bestell_id": bestell_id})
            return [self._map_to_item(row) for row in rows]
        except Exception as e:
            _get_log_service().log("SYSTEM_ERROR", "orderitem_repository" , "ERROR", f"OrderItemRepository find_by_bestell_id: {e}")
            return []
    
    def find_by_bestellartikel_id(self, bestellartikel_id: str) -> Optional[OrderItem]:
        """Hole Item by bestellartikel_id"""
        try:
            sql = f"""
                SELECT {self._ITEM_COLUMNS}
                FROM {TABLE_ORDER_ITEMS}
                WHERE bestellartikel_id = :bestellartikel_id
            """
            row = self._fetch_one(sql, {"bestellartikel_id": bestellartikel_id})
            return self._map_to_item(row) if row else None
        except Exception as e:
            _get_log_service().log("SYSTEM_ERROR", "orderitem_repository" , "ERROR", f"OrderItemRepository find_by_bestellartikel_id: {e}")
            return None
    
    def _map_to_item(self, row) -> Optional[OrderItem]:
        """Konvertiere DB Row zu OrderItem Object (Key-Based mit row._mapping)"""
        if not row:
            return None
        
        try:
            r = row._mapping
            return OrderItem(
                id=r['id'],
                order_id=r['order_id'],
                bestell_id=r['bestell_id'],
                bestellartikel_id=r['bestellartikel_id'],
                produktname=r['produktname'],
                sku=r['sku'],
                sku_id=r['sku_id'],
                variation=r['variation'],
                menge=r['menge'],
                netto_einzelpreis=r['netto_einzelpreis'],
                brutto_einzelpreis=r['brutto_einzelpreis'],
                gesamtpreis_netto=r['gesamtpreis_netto'],
                gesamtpreis_brutto=r['gesamtpreis_brutto'],
                mwst_satz=r['mwst_satz']
            )
        except Exception as e:
            _get_log_service().log("SYSTEM_ERROR", "orderitem_repository" , "ERROR", f"OrderItemRepository _map_to_item: {e}")
            return None