"""OrderItem Repository - Data Access Layer"""

from typing import List, Optional
from db.connection import get_db_connection
from config.settings import TABLE_ORDER_ITEMS, DB_TOCI

class OrderItem:
    """OrderItem Domain Model"""
    def __init__(self, id=None, order_id=None, bestell_id=None, bestellartikel_id=None,
                 produktname=None, sku=None, sku_id=None, variation=None,
                 menge=None, netto_einzelpreis=None, brutto_einzelpreis=None,
                 gesamtpreis_netto=None, gesamtpreis_brutto=None, mwst_satz=None):
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
    """Repository für OrderItem-Operationen"""
    
    def __init__(self, db_name=DB_TOCI):
        self.db_name = db_name
    
    def find_by_order_id(self, order_id: int) -> List[OrderItem]:
        """Hole alle Items für eine Order"""
        conn = get_db_connection(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT id, order_id, bestell_id, bestellartikel_id,
                   produktname, sku, sku_id, variation,
                   menge, netto_einzelpreis, brutto_einzelpreis,
                   gesamtpreis_netto, gesamtpreis_brutto, mwst_satz
            FROM {TABLE_ORDER_ITEMS}
            WHERE order_id = ?
        """, order_id)
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [self._map_to_item(row) for row in rows]
    
    def save(self, item: OrderItem) -> int:
        """INSERT oder UPDATE OrderItem"""
        conn = get_db_connection(self.db_name)
        cursor = conn.cursor()
        
        if item.id:
            # UPDATE
            cursor.execute(f"""
                UPDATE {TABLE_ORDER_ITEMS}
                SET produktname = ?, sku = ?, sku_id = ?, variation = ?,
                    menge = ?, netto_einzelpreis = ?, brutto_einzelpreis = ?,
                    gesamtpreis_netto = ?, gesamtpreis_brutto = ?, mwst_satz = ?
                WHERE id = ?
            """, item.produktname, item.sku, item.sku_id, item.variation,
                item.menge, item.netto_einzelpreis, item.brutto_einzelpreis,
                item.gesamtpreis_netto, item.gesamtpreis_brutto, item.mwst_satz,
                item.id)
            result = item.id
        else:
            # INSERT
            cursor.execute(f"""
                INSERT INTO {TABLE_ORDER_ITEMS} (
                    order_id, bestell_id, bestellartikel_id, produktname,
                    sku, sku_id, variation, menge,
                    netto_einzelpreis, brutto_einzelpreis,
                    gesamtpreis_netto, gesamtpreis_brutto, mwst_satz
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, item.order_id, item.bestell_id, item.bestellartikel_id,
                item.produktname, item.sku, item.sku_id, item.variation,
                item.menge, item.netto_einzelpreis, item.brutto_einzelpreis,
                item.gesamtpreis_netto, item.gesamtpreis_brutto, item.mwst_satz)
            
            cursor.execute("SELECT @@IDENTITY")
            result = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return result
    
    def _map_to_item(self, row) -> OrderItem:
        """Konvertiere DB-Row zu OrderItem"""
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
