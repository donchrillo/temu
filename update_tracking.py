import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

# --- EINSTELLUNGEN ---
SQL_SERVER = os.getenv('SQL_SERVER')
SQL_DATABASE = os.getenv('SQL_DATABASE')
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')

TABLE_ORDERS = os.getenv('TABLE_ORDERS', 'temu_orders')

# JTL Datenbank (anpassen!)
JTL_SQL_SERVER = os.getenv('JTL_SQL_SERVER', SQL_SERVER)
JTL_SQL_DATABASE = os.getenv('JTL_SQL_DATABASE', 'eazybusiness')
JTL_SQL_USERNAME = os.getenv('JTL_SQL_USERNAME', SQL_USERNAME)
JTL_SQL_PASSWORD = os.getenv('JTL_SQL_PASSWORD', SQL_PASSWORD)

def get_db_connection(server, database, username, password):
    """Erstellt SQL Server Verbindung."""
    conn_str = (
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password}'
    )
    return pyodbc.connect(conn_str)

def update_tracking_from_jtl():
    """Holt Trackingnummern aus JTL und aktualisiert temu_orders."""
    
    print("=" * 60)
    print("Trackingnummern aus JTL aktualisieren")
    print("=" * 60)
    
    # Verbindung zu unserer Datenbank
    conn_temu = get_db_connection(SQL_SERVER, SQL_DATABASE, SQL_USERNAME, SQL_PASSWORD)
    cursor_temu = conn_temu.cursor()
    
    # Verbindung zu JTL Datenbank
    try:
        conn_jtl = get_db_connection(JTL_SQL_SERVER, JTL_SQL_DATABASE, JTL_SQL_USERNAME, JTL_SQL_PASSWORD)
        cursor_jtl = conn_jtl.cursor()
        print("✓ JTL Datenbankverbindung hergestellt")
    except Exception as e:
        print(f"✗ FEHLER bei JTL-Verbindung: {e}")
        return False
    
    # Bestellungen holen die noch keine Trackingnummer haben
    cursor_temu.execute(f"""
        SELECT id, bestell_id 
        FROM {TABLE_ORDERS}
        WHERE trackingnummer IS NULL OR trackingnummer = ''
    """)
    
    orders = cursor_temu.fetchall()
    
    if not orders:
        print("✓ Keine Bestellungen ohne Trackingnummer gefunden")
        return True
    
    print(f"✓ {len(orders)} Bestellungen ohne Tracking gefunden")
    
    updated_count = 0
    
    for order in orders:
        order_db_id, bestell_id = order
        
        # Tracking aus JTL holen (ANPASSEN an JTL-Struktur!)
        cursor_jtl.execute("""
            SELECT TOP 1 v.cIdentCode, l.cName, v.dErstellt
            FROM tVersand v
            INNER JOIN tAuftrag a ON v.kLieferschein = a.kLieferschein
            LEFT JOIN tVersandart l ON v.kVersandart = l.kVersandart
            WHERE a.cBestellNr = ?
            ORDER BY v.dErstellt DESC
        """, bestell_id)
        
        result = cursor_jtl.fetchone()
        
        if result:
            trackingnummer, versanddienstleister, versanddatum = result
            
            cursor_temu.execute(f"""
                UPDATE {TABLE_ORDERS}
                SET trackingnummer = ?,
                    versanddienstleister = ?,
                    versanddatum = ?,
                    status = 'versendet',
                    updated_at = GETDATE()
                WHERE id = ?
            """, trackingnummer, versanddienstleister, versanddatum, order_db_id)
            
            updated_count += 1
            print(f"  ✓ {bestell_id}: {trackingnummer}")
    
    conn_temu.commit()
    cursor_temu.close()
    cursor_jtl.close()
    conn_temu.close()
    conn_jtl.close()
    
    print(f"\n{'='*60}")
    print(f"✓ Tracking-Update erfolgreich!")
    print(f"  Aktualisierte Bestellungen: {updated_count}")
    print(f"{'='*60}\n")
    
    return True

if __name__ == "__main__":
    update_tracking_from_jtl()
