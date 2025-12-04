"""Tracking Service - holt Tracking aus JTL"""

from src.database.connection import get_db_connection
from config.settings import TABLE_ORDERS, DB_TOCI, DB_JTL

def update_tracking_from_jtl():
    """Holt Trackingnummern aus JTL und aktualisiert Datenbank"""
    
    print("=" * 60)
    print("Tracking-Update aus JTL")
    print("=" * 60)
    
    conn_toci = get_db_connection(DB_TOCI)
    cursor_toci = conn_toci.cursor()
    print(f"✓ {DB_TOCI} Verbindung hergestellt")
    
    try:
        conn_jtl = get_db_connection(DB_JTL)
        cursor_jtl = conn_jtl.cursor()
        print(f"✓ {DB_JTL} Verbindung hergestellt")
    except Exception as e:
        print(f"✗ JTL-Verbindung fehlgeschlagen: {e}")
        cursor_toci.close()
        conn_toci.close()
        return False
    
    # Bestellungen ohne Tracking holen
    cursor_toci.execute(f"""
        SELECT id, bestell_id 
        FROM {TABLE_ORDERS}
        WHERE (trackingnummer IS NULL OR trackingnummer = '')
          AND status = 'xml_erstellt'
    """)
    
    orders = cursor_toci.fetchall()
    
    if not orders:
        print("✓ Keine Bestellungen ohne Tracking")
        cursor_toci.close()
        cursor_jtl.close()
        conn_toci.close()
        conn_jtl.close()
        return True
    
    print(f"✓ {len(orders)} Bestellungen ohne Tracking gefunden")
    
    updated_count = 0
    
    for order_db_id, bestell_id in orders:
        # Tracking aus JTL holen
        cursor_jtl.execute("""
            SELECT 
                [cBestellungInetBestellNr],
                [cVersandartName],
                CAST([cTrackingId] AS VARCHAR(50))
            FROM [Versand].[lvLieferschein]
            JOIN [Versand].[lvLieferscheinpaket]
                ON [Versand].[lvLieferscheinpaket].kLieferschein = 
                   [Versand].[lvLieferschein].kLieferschein
            WHERE cBestellungInetBestellNr = ?
        """, bestell_id)
        
        result = cursor_jtl.fetchone()
        
        if result:
            bestellnr, versanddienstleister, trackingnummer = result
            
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
            print(f"  ✓ {bestell_id}: {trackingnummer}")
        else:
            print(f"  ⚠ {bestell_id}: Kein Tracking")
    
    conn_toci.commit()
    cursor_toci.close()
    cursor_jtl.close()
    conn_toci.close()
    conn_jtl.close()
    
    print(f"\n{'='*60}")
    print(f"✓ Tracking-Update erfolgreich!")
    print(f"  Aktualisiert: {updated_count}")
    print(f"{'='*60}\n")
    
    return True
