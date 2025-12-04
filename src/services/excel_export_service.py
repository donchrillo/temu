"""Excel Export Service - exportiert Tracking als Excel"""

import pandas as pd
from src.database.connection import get_db_connection
from config.settings import TABLE_ORDERS, TABLE_ORDER_ITEMS, DB_TOCI, TRACKING_EXPORT_PATH

def export_tracking_to_excel():
    """Exportiert versendete Bestellungen als Excel"""
    
    print("=" * 60)
    print("Excel-Export für TEMU")
    print("=" * 60)
    
    conn = get_db_connection(DB_TOCI)
    
    # Bestellungen mit Tracking holen
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
        print("✓ Keine neuen Trackings")
        conn.close()
        return True
    
    print(f"✓ {len(df)} Positionen gefunden")
    
    # DataFrame in TEMU-Format umwandeln
    export_df = pd.DataFrame({
        'Bestell-ID': df['bestell_id'],
        'Bestellartikel-ID': df['bestellartikel_id'],
        'Menge': df['menge'].astype(int),
        'Versand von': '',
        'Transportdienstleister': df['versanddienstleister'],
        'Versandnummer': df['trackingnummer']
    })
    
    # Excel-Datei erstellen
    with pd.ExcelWriter(str(TRACKING_EXPORT_PATH), engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Tracking')
        
        # Spaltenbreite anpassen
        worksheet = writer.sheets['Tracking']
        worksheet.column_dimensions['A'].width = 30
        worksheet.column_dimensions['B'].width = 30
        worksheet.column_dimensions['C'].width = 10
        worksheet.column_dimensions['D'].width = 20
        worksheet.column_dimensions['E'].width = 25
        worksheet.column_dimensions['F'].width = 30
    
    print(f"✓ Excel erstellt: {TRACKING_EXPORT_PATH}")
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✓ Excel-Export erfolgreich!")
    print(f"  Zeilen: {len(export_df)}")
    print(f"{'='*60}\n")
    
    return True
