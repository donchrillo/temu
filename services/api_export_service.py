"""API Export Service - sendet Daten an TEMU API"""

import time
from db.connection import get_db_connection
from services.temu_client import TemuApiClient
from services.temu_orders_api import TemuOrdersApi
from config.settings import TABLE_ORDERS, TABLE_ORDER_ITEMS, DB_TOCI

def export_to_temu_api(app_key, app_secret, access_token, api_endpoint):
    """Exportiert Bestellungen mit Tracking zur TEMU API (1 Order pro Request)"""
    
    print("=" * 60)
    print("Datenbank → TEMU API")
    print("=" * 60)
    
    conn_toci = get_db_connection(DB_TOCI)
    cursor_toci = conn_toci.cursor()
    print(f"✓ {DB_TOCI} Verbindung hergestellt")
    
    # Bestellungen mit Tracking zum Export holen
    cursor_toci.execute(f"""
        SELECT 
            o.id,
            o.bestell_id,
            i.bestellartikel_id,
            CAST(i.menge AS INTEGER),
            o.versanddienstleister,
            o.trackingnummer
        FROM {TABLE_ORDERS} o
        INNER JOIN {TABLE_ORDER_ITEMS} i ON o.id = i.order_id
        WHERE o.trackingnummer IS NOT NULL 
          AND o.trackingnummer != ''
          AND o.temu_gemeldet = 0
          AND o.status = 'versendet'
        ORDER BY o.versanddatum DESC
    """)
    
    orders = cursor_toci.fetchall()
    
    if not orders:
        print("✓ Keine Bestellungen zum Exportieren")
        cursor_toci.close()
        conn_toci.close()
        return True
    
    print(f"✓ {len(orders)} Bestellungen zum Exportieren gefunden\n")

    # Mapping von Versanddienstleister zu Carrier ID
    CARRIER_MAPPING = {
        'DHL': 141252268,
        'DPD': 998264853,
        'default': 141252268
    }
    
    # Statistik
    exported_count = 0
    skipped_count = 0
    error_count = 0
    
    # Erstelle API Client einmalig
    try:
        client = TemuApiClient(app_key, app_secret, access_token, api_endpoint)
        orders_api = TemuOrdersApi(client)
    except Exception as e:
        print(f"✗ API Client Fehler: {e}")
        cursor_toci.close()
        conn_toci.close()
        return False
    
    # Loop: Jede Order einzeln exportieren
    for idx, order in enumerate(orders, 1):
        order_id, bestell_id, bestellartikel_id, menge, versanddienstleister, trackingnummer = order
        
        print(f"[{idx}/{len(orders)}] Order {bestell_id} (Tracking: {trackingnummer})")
        
        try:
            # Bestimme Carrier ID
            carrier_id = CARRIER_MAPPING.get(versanddienstleister, CARRIER_MAPPING['default'])
            
            # Baue Payload für EINEN Order
            export_data = [{
                'bestell_id': bestell_id,
                'order_sn': bestellartikel_id,
                'quantity': menge,
                'carrier_id': carrier_id,
                'tracking_number': trackingnummer
            }]
            
            # API Aufruf (1 Order) - gibt Tuple zurück
            success, error_code, error_msg = orders_api.upload_tracking_data(export_data)
            
            if success:
                # Order als gemeldet markieren
                cursor_toci.execute(f"""
                    UPDATE {TABLE_ORDERS}
                    SET temu_gemeldet = 1,
                        updated_at = GETDATE()
                    WHERE id = ?
                """, order_id)
                conn_toci.commit()
                
                print(f"  ✓ Erfolgreich exportiert")
                exported_count += 1
            
            else:
                # Fehlerbehandlung basierend auf Error-Code
                IGNORABLE_ERRORS = {
                    20004: "Order already shipped",
                    20005: "Tracking already exists",
                }
                
                if error_code in IGNORABLE_ERRORS:
                    print(f"  ⚠ {IGNORABLE_ERRORS[error_code]} (Code {error_code})")
                    
                    # Trotzdem als gemeldet markieren (verhindert Endlosschleife)
                    cursor_toci.execute(f"""
                        UPDATE {TABLE_ORDERS}
                        SET temu_gemeldet = 1,
                            updated_at = GETDATE()
                        WHERE id = ?
                    """, order_id)
                    conn_toci.commit()
                    skipped_count += 1
                else:
                    # Echter Fehler - nicht als gemeldet markieren
                    print(f"  ✗ Fehler Code {error_code}: {error_msg}")
                    error_count += 1
        
        except Exception as e:
            print(f"  ✗ Exception: {e}")
            error_count += 1
        
        # Rate Limiting: 0,5 Sekunden Pause zwischen Requests
        if idx < len(orders):
            time.sleep(0.5)
    
    cursor_toci.close()
    conn_toci.close()
    
    # Zusammenfassung
    print(f"\n{'='*60}")
    print("EXPORT ABGESCHLOSSEN")
    print(f"{'='*60}")
    print(f"  ✓ Erfolgreich:   {exported_count}")
    print(f"  ⚠ Übersprungen:  {skipped_count}")
    print(f"  ✗ Fehler:        {error_count}")
    print(f"  Total bearbeitet: {exported_count + skipped_count + error_count}/{len(orders)}")
    print(f"{'='*60}\n")
    
    # Erfolg = mindestens ein Order verarbeitet
    success = (exported_count + skipped_count) > 0
    return success