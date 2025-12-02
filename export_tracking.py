import pyodbc
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- EINSTELLUNGEN ---
SQL_SERVER = os.getenv('SQL_SERVER')
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')

# Datenbanknamen (fest im Code)
DB_TOCI = 'toci'

TABLE_ORDERS = os.getenv('TABLE_ORDERS', 'temu_orders')
TABLE_ORDER_ITEMS = os.getenv('TABLE_ORDER_ITEMS', 'temu_order_items')

EXPORT_PATH = os.getenv('TRACKING_EXPORT_PATH', 'temu_tracking_export.xlsx')

def get_db_connection():
    """Erstellt SQL Server Verbindung zur TOCI Datenbank."""
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
        f'DATABASE={DB_TOCI};'
        f'UID={SQL_USERNAME};'
        f'PWD={SQL_PASSWORD};'
        f'TrustServerCertificate=yes;'
    )
    return pyodbc.connect(conn_str)

def export_tracking_to_excel():
    """Exportiert Bestellungen mit Trackingnummern für TEMU im Excel-Format."""
    
    print("=" * 60)
    print("Tracking-Export für TEMU erstellen")
    print("=" * 60)
    
    conn = get_db_connection()
    
    # Bestellungen mit Trackingnummer holen
    query = f"""
        SELECT 
            o.bestell_id,
            i.bestellartikel_id,
            i.menge,
            o.versanddienstleister,
            o.trackingnummer
        FROM {TABLE_ORDERS} o
        INNER JOIN {TABLE_ORDER_ITEMS} i ON o.id = i.order_id
        WHERE o.trackingnummer IS NOT NULL 
          AND o.trackingnummer != ''
          AND o.temu_gemeldet = 0
          AND o.status = 'versendet'
        ORDER BY o.versanddatum DESC
    """
    
    df = pd.read_sql(query, conn)
    
    if df.empty:
        print("✓ Keine neuen Trackings zum Exportieren")
        conn.close()
        return True
    
    print(f"✓ {len(df)} Positionen zum Exportieren gefunden")
    
    # DataFrame in TEMU-Format umwandeln
    export_df = pd.DataFrame({
        'Bestell-ID': df['bestell_id'],
        'Bestellartikel-ID': df['bestellartikel_id'],
        'Menge': df['menge'].astype(int),
        'Versand von': '',  # Leer lassen (wird von TEMU befüllt)
        'Transportdienstleister': df['versanddienstleister'],
        'Versandnummer': df['trackingnummer']
    })
    
    # Excel-Datei erstellen
    with pd.ExcelWriter(EXPORT_PATH, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Tracking')
        
        # Spaltenbreite anpassen
        worksheet = writer.sheets['Tracking']
        worksheet.column_dimensions['A'].width = 30  # Bestell-ID
        worksheet.column_dimensions['B'].width = 30  # Bestellartikel-ID
        worksheet.column_dimensions['C'].width = 10  # Menge
        worksheet.column_dimensions['D'].width = 20  # Versand von
        worksheet.column_dimensions['E'].width = 25  # Transportdienstleister
        worksheet.column_dimensions['F'].width = 30  # Versandnummer
    
    print(f"✓ Export erstellt: {EXPORT_PATH}")
    print(f"  {len(export_df)} Zeilen exportiert")
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✓ Export erfolgreich!")
    print(f"  Datei: {EXPORT_PATH}")
    print(f"  Format: Excel (.xlsx)")
    print(f"{'='*60}\n")
    
    return True

if __name__ == "__main__":
    export_tracking_to_excel()
