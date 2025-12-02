import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

# --- EINSTELLUNGEN ---
SQL_SERVER = os.getenv('SQL_SERVER')
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')

TABLE_ORDERS = os.getenv('TABLE_ORDERS', 'temu_orders')

# Datenbanknamen (fest im Code)
DB_TOCI = 'toci'
DB_JTL = 'eazybusiness'

def get_db_connection(database):
    """Erstellt SQL Server Verbindung zu einer bestimmten Datenbank."""
    # Verfügbare Treiber in Priorität
    drivers = [
        'ODBC Driver 18 for SQL Server',
        'ODBC Driver 17 for SQL Server',
        'ODBC Driver 13 for SQL Server',
        'SQL Server Native Client 11.0',
        'SQL Server'
    ]
    
    # Installierten Treiber finden
    available_drivers = [d for d in pyodbc.drivers() if 'SQL Server' in d]
    
    driver = None
    for d in drivers:
        if d in available_drivers:
            driver = d
            break
    
    if not driver and available_drivers:
        driver = available_drivers[0]
    
    if not driver:
        raise Exception("Kein SQL Server ODBC-Treiber gefunden!")
    
    conn_str = (
        f'DRIVER={{{driver}}};'
        f'SERVER={SQL_SERVER};'
        f'DATABASE={database};'
        f'UID={SQL_USERNAME};'
        f'PWD={SQL_PASSWORD};'
        f'TrustServerCertificate=yes;'
    )
    return pyodbc.connect(conn_str)

def update_tracking_from_jtl():
    """Holt Trackingnummern aus JTL und aktualisiert temu_orders."""
    
    print("=" * 60)
    print("Trackingnummern aus JTL aktualisieren")
    print("=" * 60)
    
    # Verbindung zu TOCI Datenbank (TEMU Orders)
    conn_toci = get_db_connection(DB_TOCI)
    cursor_toci = conn_toci.cursor()
    print(f"✓ {DB_TOCI} Datenbankverbindung hergestellt")
    
    # Verbindung zu JTL Datenbank
    try:
        conn_jtl = get_db_connection(DB_JTL)
        cursor_jtl = conn_jtl.cursor()
        print(f"✓ {DB_JTL} Datenbankverbindung hergestellt")
    except Exception as e:
        print(f"✗ FEHLER bei JTL-Verbindung: {e}")
        cursor_toci.close()
        conn_toci.close()
        return False
    
    # Bestellungen aus TOCI holen die noch keine Trackingnummer haben
    cursor_toci.execute(f"""
        SELECT id, bestell_id 
        FROM {TABLE_ORDERS}
        WHERE (trackingnummer IS NULL OR trackingnummer = '')
          AND status = 'xml_erstellt'
    """)
    
    orders = cursor_toci.fetchall()
    
    if not orders:
        print("✓ Keine Bestellungen ohne Trackingnummer gefunden")
        cursor_toci.close()
        cursor_jtl.close()
        conn_toci.close()
        conn_jtl.close()
        return True
    
    print(f"✓ {len(orders)} Bestellungen ohne Tracking gefunden")
    
    updated_count = 0
    
    for order in orders:
        order_db_id, bestell_id = order
        
        # Tracking aus JTL holen mit dem neuen SQL Query
        cursor_jtl.execute("""
            SELECT 
                [cBestellungInetBestellNr],
                [cVersandartName],
                CAST([cTrackingId] AS VARCHAR(50))
            FROM [eazybusiness].[Versand].[lvLieferschein]
            JOIN [eazybusiness].[Versand].[lvLieferscheinpaket]
                ON [eazybusiness].[Versand].[lvLieferscheinpaket].kLieferschein = 
                   [eazybusiness].[Versand].[lvLieferschein].kLieferschein
            WHERE cBestellungInetBestellNr = ?
        """, bestell_id)
        
        result = cursor_jtl.fetchone()
        
        if result:
            bestellnr, versanddienstleister, trackingnummer = result
            
            # In TOCI Datenbank aktualisieren
            cursor_toci.execute(f"""
                UPDATE {TABLE_ORDERS}
                SET trackingnummer = ?,
                    versanddienstleister = ?,
                    versanddatum = GETDATE(),
                    status = 'versendet',
                    updated_at = GETDATE()
                WHERE id = ?
            """, trackingnummer, versanddienstleister, order_db_id)
            
            updated_count += 1
            print(f"  ✓ {bestell_id}: {trackingnummer} ({versanddienstleister})")
        else:
            print(f"  ⚠ {bestell_id}: Noch kein Tracking in JTL")
    
    conn_toci.commit()
    cursor_toci.close()
    cursor_jtl.close()
    conn_toci.close()
    conn_jtl.close()
    
    print(f"\n{'='*60}")
    print(f"✓ Tracking-Update erfolgreich!")
    print(f"  Aktualisierte Bestellungen: {updated_count}")
    print(f"{'='*60}\n")
    
    return True

if __name__ == "__main__":
    update_tracking_from_jtl()
