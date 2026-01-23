"""OrderItem Repository - Data Access Layer für Order Items"""

from typing import List, Optional
from src.db.connection import get_db_connection
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
        """Hole Connection (gepooled oder neu)"""
        if self._conn:
            return self._conn
        return get_db_connection(DB_TOCI)
    
    def save(self, item: OrderItem) -> int:
        """INSERT oder UPDATE OrderItem"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            if item.id:
                # UPDATE
                cursor.execute(f"""
                    UPDATE {TABLE_ORDER_ITEMS} SET
                        produktname = ?,
                        sku = ?,
                        sku_id = ?,
                        variation = ?,
                        menge = ?,
                        netto_einzelpreis = ?,
                        brutto_einzelpreis = ?,
                        gesamtpreis_netto = ?,
                        gesamtpreis_brutto = ?,
                        mwst_satz = ?
                    WHERE id = ?
                """, item.produktname, item.sku, item.sku_id, item.variation,
                    item.menge, item.netto_einzelpreis, item.brutto_einzelpreis,
                    item.gesamtpreis_netto, item.gesamtpreis_brutto,
                    item.mwst_satz, item.id)
                
                # ❌ NICHT conn.commit()!
                # ✅ AutoCommit ist aktiv
                return item.id
            else:
                # INSERT
                cursor.execute(f"""
                    INSERT INTO {TABLE_ORDER_ITEMS} (
                        order_id, bestell_id, bestellartikel_id,
                        produktname, sku, sku_id, variation,
                        menge, netto_einzelpreis, brutto_einzelpreis,
                        gesamtpreis_netto, gesamtpreis_brutto, mwst_satz,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, item.order_id, item.bestell_id, item.bestellartikel_id,
                    item.produktname, item.sku, item.sku_id, item.variation,
                    item.menge, item.netto_einzelpreis, item.brutto_einzelpreis,
                    item.gesamtpreis_netto, item.gesamtpreis_brutto, item.mwst_satz)
                
                cursor.execute("SELECT @@IDENTITY")
                new_id = cursor.fetchone()[0]
                
                # ❌ NICHT conn.commit()!
                # ✅ AutoCommit ist aktiv
                return int(new_id)
        
        except Exception as e:
            app_logger.error(f"DB Fehler bei save: {e}", exc_info=True)
            return 0
    
    def find_by_order_id(self, order_id: int) -> List[OrderItem]:
        """Hole alle Items für Order"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT id, order_id, bestell_id, bestellartikel_id,
                       produktname, sku, sku_id, variation, menge,
                       netto_einzelpreis, brutto_einzelpreis,
                       gesamtpreis_netto, gesamtpreis_brutto, mwst_satz
                FROM {TABLE_ORDER_ITEMS}
                WHERE order_id = ?
            """, order_id)
            rows = cursor.fetchall()
            
            # ❌ NICHT conn.close()!
            
            return [self._map_to_item(row) for row in rows]
        except Exception as e:
            app_logger.error(f"DB Fehler bei find_by_order_id: {e}", exc_info=True)
            return []
    
    def find_by_bestellartikel_id(self, bestellartikel_id: str) -> Optional[OrderItem]:
        """Hole Item by bestellartikel_id"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT id, order_id, bestell_id, bestellartikel_id,
                       produktname, sku, sku_id, variation, menge,
                       netto_einzelpreis, brutto_einzelpreis,
                       gesamtpreis_netto, gesamtpreis_brutto, mwst_satz
                FROM {TABLE_ORDER_ITEMS}
                WHERE bestellartikel_id = ?
            """, bestellartikel_id)
            row = cursor.fetchone()
            
            # ❌ NICHT conn.close()!
            
            return self._map_to_item(row) if row else None
        except Exception as e:
            app_logger.error(f"DB Fehler bei find_by_bestellartikel_id: {e}", exc_info=True)
            return None
    
    def _map_to_item(self, row) -> OrderItem:
        """Konvertiere DB Row zu OrderItem Object"""
        if not row:
            return None
        
        return OrderItem(
            id=row[0],
            order_id=row[1],
            bestell_id=row[2],
            bestellartikel_id=row[3],
            produktname=row[4],
            sku=row[5],
            sku_id=row[6],
            variation=row[7],
            menge=row[8],
            netto_einzelpreis=row[9],
            brutto_einzelpreis=row[10],
            gesamtpreis_netto=row[11],
            gesamtpreis_brutto=row[12],
            mwst_satz=row[13]
        )
