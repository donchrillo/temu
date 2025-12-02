import pyodbc
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- EINSTELLUNGEN ---
SQL_SERVER = os.getenv('SQL_SERVER')
SQL_DATABASE = os.getenv('SQL_DATABASE')
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')

TABLE_ORDERS = os.getenv('TABLE_ORDERS', 'temu_orders')
TABLE_ORDER_ITEMS = os.getenv('TABLE_ORDER_ITEMS', 'temu_order_items')

EXPORT_PATH = os.getenv('TRACKING_EXPORT_PATH', 'temu_tracking_export.csv')

def get_db_connection():
    """Erstellt SQL Server Verbindung."""
    conn_str = (
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={SQL_SERVER};'
        f'DATABASE={SQL_DATABASE};'
        f'UID={SQL_USERNAME};'
        f'PWD={SQL_PASSWORD}'
    )
    return pyodbc.connect(conn_str)

def export_tracking_to_csv():
    """Exportiert Bestellungen mit Trackingnummern für TEMU."""
    
    print("=" * 60)
    print("Tracking-Export für TEMU erstellen")
    print("=" * 60)
    
    conn = get_db_connection()
    
    # Bestellungen mit Trackingnummer holen
    query = f"""
        SELECT 
            o.bestell_id,
            i.bestellartikel_id,
            o.trackingnummer,
            o.versanddienstleister,
            o.versanddatum,
            o.temu_gemeldet
        FROM {TABLE_ORDERS} o
        INNER JOIN {TABLE_ORDER_ITEMS} i ON o.id = i.order_id
        WHERE o.trackingnummer IS NOT NULL 
          AND o.trackingnummer != ''
          AND o.temu_gemeldet = 0
        ORDER BY o.versanddatum DESC
    """
    
    df = pd.read_sql(query, conn)
    
    if df.empty:
        print("✓ Keine neuen Trackings zum Exportieren")
        conn.close()
        return True
    
    print(f"✓ {len(df)} Positionen zum Exportieren gefunden")
    
    # CSV exportieren
    df.to_csv(EXPORT_PATH, index=False, encoding='utf-8-sig')
    
    print(f"✓ Export erstellt: {EXPORT_PATH}")
    
    # Optional: Status aktualisieren (nach manuellem TEMU-Upload)
    # cursor = conn.cursor()
    # cursor.execute(f"""
    #     UPDATE {TABLE_ORDERS}
    #     SET temu_gemeldet = 1
    #     WHERE trackingnummer IS NOT NULL AND temu_gemeldet = 0
    # """)
    # conn.commit()
    # cursor.close()
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✓ Export erfolgreich!")
    print(f"  Datei: {EXPORT_PATH}")
    print(f"{'='*60}\n")
    
    return True

if __name__ == "__main__":
    export_tracking_to_csv()
