"""API Export Service - sendet Daten an TEMU API"""

from src.database.connection import get_db_connection
from src.api_import.temu_client import TemuApiClient
from src.api_import.temu_orders_api import TemuOrdersApi
from config.settings import TABLE_ORDERS, TABLE_ORDER_ITEMS, DB_TOCI

def export_to_temu_api(app_key, app_secret, access_token, api_endpoint):
    """Exportiert Bestellungen mit Tracking zur TEMU API"""
    
    print("=" * 60)
    print("Datenbank → TEMU API")
    print("=" * 60)
    
    conn_toci = get_db_connection(DB_TOCI)
    cursor_toci = conn_toci.cursor()
    print(f"✓ {DB_TOCI} Verbindung hergestellt")
    
    # Bestellungen mit Tracking zum Export holen
    cursor_toci.execute(f"""
        SELECT 
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
    
    print(f"✓ {len(orders)} Bestellungen zum Exportieren gefunden")

        # Mapping von Versanddienstleister zu Carrier ID
    CARRIER_MAPPING = {
        'DHL': 141252268,
        'DPD': 998264853,
        'default': 141252268  # Externe Carrier ID als Fallback
    }
    
    # Prepare data for API
    export_data = []
    order_ids = []

    for order in orders:
        bestell_id, bestellartikel_id, menge, versanddienstleister, trackingnummer = order

        # Bestimme Carrier ID basierend auf Versanddienstleister
        carrier_id = CARRIER_MAPPING.get(versanddienstleister, CARRIER_MAPPING['default'])
        
        export_data.append({
            'bestell_id': bestell_id,
            'order_sn': bestellartikel_id,
            'quantity': menge,
            'carrier_id': carrier_id,  # Externe Carrier ID
            'tracking_number': trackingnummer
        })
        order_ids.append(bestell_id)
    
    # Send to TEMU API
    try:
        # Erstelle API Client
        client = TemuApiClient(app_key, app_secret, access_token, api_endpoint)
        orders_api = TemuOrdersApi(client)
        success = orders_api.upload_tracking_data(export_data)
        
        #success = False  # Mock success for this example
        if success:
            for order_id in order_ids:
                cursor_toci.execute(f"""
                    UPDATE {TABLE_ORDERS}
                    SET temu_gemeldet = 1,
                        bestellstatus = 'shipped',
                        updated_at = GETDATE()
                    WHERE id = ?
                """, order_id)
            conn_toci.commit()
            exported_count = len(order_ids)
        else:
            exported_count = 0
            
    except Exception as e:
        print(f"✗ API-Fehler: {e}")
        exported_count = 0
        success = False
    finally:
        cursor_toci.close()
        conn_toci.close()
    
    print(f"\n{'='*60}")
    print(f"{'✓ API-Export erfolgreich!' if success else '✗ API-Export fehlgeschlagen'}")
    print(f"  Exportiert: {exported_count}")
    print(f"{'='*60}\n")
    
    return success
