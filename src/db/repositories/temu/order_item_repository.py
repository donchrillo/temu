"""OrderItem Repository - SQLAlchemy + Raw SQL"""

from typing import List, Optional
from sqlalchemy import text
from src.services.logger import app_logger
from config.settings import TABLE_ORDER_ITEMS, DB_TOCI

class OrderItem:
    """Domain Model für Order Item"""
    def __init__(self, id=None, order_id=None, bestell_id=None, 
                 bestellartikel_id=None, produktname=None, sku=None,
                 sku_id=None, variation=None, menge=None,
                 netto_einzelpreis=None, brutto_einzelpreis=None,
                 gesamtpreis_netto=None, gesamtpreis_brutto=None, 
                 mwst_satz=None):
        self.id = id
        self.order_id = order_id
        self.bestell_id = bestell_id
        self.bestellartikel_id = bestellartikel_id
        self.produktname = produktname
        self.sku = sku
        self.sku_id = sku_id
        self.variation = variation
        self.menge = menge
        self.netto_einzelpreis = netto_einzelpreis
        self.brutto_einzelpreis = brutto_einzelpreis
        self.gesamtpreis_netto = gesamtpreis_netto
        self.gesamtpreis_brutto = gesamtpreis_brutto
        self.mwst_satz = mwst_satz

class OrderItemRepository:
    """Data Access Layer - ONLY DB Operations"""
    
    def __init__(self, connection=None):
        """Optionale Injektierte Connection (für Pooling)"""
        self._conn = connection
    
    def _get_conn(self):
        """Hole Connection"""
        if self._conn:
            return self._conn
        from src.db.connection import get_engine
        return get_db_connection(DB_TOCI)
    
    def save(self, item: OrderItem) -> int:
        """INSERT oder UPDATE OrderItem"""
        try:
            if item.id:
                # UPDATE
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
                    "mwst_satz": item.mwst_satz,
                    "id": item.id
                }
                
                if self._conn:
                    self._conn.execute(text(sql), params)
                else:
                    with get_engine(DB_TOCI).connect() as conn:
                        conn.execute(text(sql), params)
                        conn.commit()
                
                return item.id
            else:
                # INSERT
                sql = f"""
                    INSERT INTO {TABLE_ORDER_ITEMS} (
                        order_id, bestell_id, bestellartikel_id, produktname,
                        sku, sku_id, variation, menge,
                        netto_einzelpreis, brutto_einzelpreis,
                        gesamtpreis_netto, gesamtpreis_brutto, mwst_satz
                    ) VALUES (
                        :order_id, :bestell_id, :bestellartikel_id, :produktname,
                        :sku, :sku_id, :variation, :menge,
                        :netto_einzelpreis, :brutto_einzelpreis,
                        :gesamtpreis_netto, :gesamtpreis_brutto, :mwst_satz
                    );
                    SELECT @@IDENTITY AS new_id;
                """
                params = {
                    "order_id": item.order_id,
                    "bestell_id": item.bestell_id,
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
            app_logger.error(f"OrderItemRepository save: {e}", exc_info=True)
            return 0

    def find_by_order_id(self, order_id: int) -> List[OrderItem]:
        """Hole alle Items für Order"""
        try:
            conn = self._get_conn()
            result = conn.execute(text(f"""
                SELECT id, order_id, bestell_id, bestellartikel_id,
                       produktname, sku, sku_id, variation, menge,
                       netto_einzelpreis, brutto_einzelpreis,
                       gesamtpreis_netto, gesamtpreis_brutto, mwst_satz
                FROM {TABLE_ORDER_ITEMS}
                WHERE order_id = :order_id
            """), {"order_id": order_id})
            return [self._map_to_item(row) for row in result.all()]
        except Exception as e:
            app_logger.error(f"OrderItemRepository find_by_order_id: {e}", exc_info=True)
            return []
    
    def find_by_bestellartikel_id(self, bestellartikel_id: str) -> Optional[OrderItem]:
        """Hole Item by bestellartikel_id"""
        try:
            conn = self._get_conn()
            result = conn.execute(text(f"""
                SELECT id, order_id, bestell_id, bestellartikel_id,
                       produktname, sku, sku_id, variation, menge,
                       netto_einzelpreis, brutto_einzelpreis,
                       gesamtpreis_netto, gesamtpreis_brutto, mwst_satz
                FROM {TABLE_ORDER_ITEMS}
                WHERE bestellartikel_id = :bestellartikel_id
            """), {"bestellartikel_id": bestellartikel_id})
            row = result.first()
            return self._map_to_item(row) if row else None
        except Exception as e:
            app_logger.error(f"OrderItemRepository find_by_bestellartikel_id: {e}", exc_info=True)
            return None
    
    def _map_to_item(self, row) -> OrderItem:
        """Konvertiere DB Row zu OrderItem Object"""
        if not row:
            return None
        return OrderItem(
            id=row[0], order_id=row[1], bestell_id=row[2],
            bestellartikel_id=row[3], produktname=row[4], sku=row[5],
            sku_id=row[6], variation=row[7], menge=row[8],
            netto_einzelpreis=row[9], brutto_einzelpreis=row[10],
            gesamtpreis_netto=row[11], gesamtpreis_brutto=row[12],
            mwst_satz=row[13]
        )
