"""ORM-ähnliche Klassen für Datenbank-Operationen"""

from src.database.connection import get_db_connection
from config.settings import TABLE_ORDERS, TABLE_ORDER_ITEMS

class TemuOrder:
    """Bestellungs-Modell"""
    
    @staticmethod
    def get_by_id(order_id):
        """Holt Bestellung nach Bestell-ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {TABLE_ORDERS} WHERE bestell_id = ?", order_id)
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result
    
    @staticmethod
    def get_pending_for_xml():
        """Holt Bestellungen für XML-Export"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT * FROM {TABLE_ORDERS} 
            WHERE status = 'importiert' AND xml_erstellt = 0 AND bestellstatus != 'Storniert'
        """)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results

class TemuOrderItem:
    """Bestellpositionen-Modell"""
    
    @staticmethod
    def get_by_order_id(order_id):
        """Holt Positionen einer Bestellung"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {TABLE_ORDER_ITEMS} WHERE order_id = ?", order_id)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
