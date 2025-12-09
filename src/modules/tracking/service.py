"""Tracking Service - Hole Tracking aus JTL, Update DB, Upload zu TEMU"""

from typing import Dict, List
from src.db.repositories.order_repository import OrderRepository
from src.db.repositories.jtl_repository import JtlRepository

class TrackingService:
    """
    Tracking Workflow:
    1. Hole Tracking aus JTL (Lieferscheindaten)
    2. Update Orders in TOCI mit Tracking
    3. Prepare für API Upload
    """
    
    def __init__(self, order_repo: OrderRepository, jtl_repo: JtlRepository = None):
        # ✅ jtl_repo optional mit Default None
        self.order_repo = order_repo
        self.jtl_repo = jtl_repo
    
    def update_tracking_from_jtl(self) -> Dict:
        """
        Hauptmethod: Hole Tracking aus JTL und update TOCI
        
        Sucht nach Orders mit:
        - xml_erstellt = 1 (XML wurde exportiert)
        - trackingnummer IS NULL oder ''  (Kein Tracking vorhanden)
        
        Returns:
            dict mit updated/errors/success/tracking_data
        """
        
        print("→ Hole Orders ohne Tracking...")
        
        # Step 1: Hole Orders die XML haben, aber kein Tracking
        orders_without_tracking = self.order_repo.find_orders_for_tracking()
        
        if not orders_without_tracking:
            print("✓ Keine Bestellungen ohne Tracking\n")
            return {
                'updated': 0,
                'errors': 0,
                'success': True,
                'tracking_data': []
            }
        
        print(f"✓ {len(orders_without_tracking)} Bestellungen ohne Tracking\n")
        
        updated_count = 0
        error_count = 0
        tracking_data_for_api = []
        
        # Step 2 & 3: Für jede Order - suche Tracking in JTL & update TOCI
        for order in orders_without_tracking:
            try:
                # Hole Tracking aus JTL!
                tracking_info = self.jtl_repo.get_tracking_from_lieferschein(
                    order.bestell_id
                )
                
                if not tracking_info:
                    print(f"  ⚠ {order.bestell_id}: Kein Tracking in JTL gefunden")
                    error_count += 1
                    continue
                
                # Step 3: Update Order in TOCI mit Tracking
                success = self.order_repo.update_order_tracking(
                    order_id=order.id,
                    tracking_number=tracking_info['tracking_number'],
                    versanddienstleister=tracking_info['carrier'],
                    status='versendet'
                )
                
                if success:
                    print(f"  ✓ {order.bestell_id}: {tracking_info['tracking_number']}")
                    updated_count += 1
                    
                    # Step 4: Sammle Daten für API Upload (Step 5)
                    tracking_data_for_api.append({
                        'bestell_id': order.bestell_id,
                        'tracking_number': tracking_info['tracking_number'],
                        'carrier': tracking_info['carrier']
                    })
                else:
                    print(f"  ✗ {order.bestell_id}: DB Update fehlgeschlagen")
                    error_count += 1
            
            except Exception as e:
                print(f"  ✗ {order.bestell_id}: {e}")
                error_count += 1
        
        print(f"\n✓ Tracking-Sync: {updated_count} aktualisiert")
        print(f"✓ {len(tracking_data_for_api)} bereit für API Upload\n")
        
        return {
            'updated': updated_count,
            'errors': error_count,
            'success': error_count == 0,
            'tracking_data': tracking_data_for_api
        }
    
    def prepare_tracking_for_api(self, orders_data: List[Dict]) -> List[Dict]:
        """
        Konvertiere Tracking-Daten für TEMU API Format
        MIT Carrier ID Mapping!
        
        Args:
            orders_data: List mit Tracking-Daten aus DB
        
        Returns:
            List mit TEMU API Format
        """
        
        # ✅ Carrier Mapping GEHÖRT HIERHER (Service, nicht Workflow!)
        CARRIER_MAPPING = {
            'dhl': 141252268,
            'dpd': 998264853,
            'ups': 960246690,
            'hermes': 123456789,
            'default': 141252268
        }
        
        tracking_data_for_api = []
        
        for order_data in orders_data:
            bestell_id = order_data['bestell_id']
            tracking_number = order_data['trackingnummer']
            carrier_name = order_data['versanddienstleister'] or 'default'
            
            # ✅ Business Logic: Carrier ID ermitteln
            carrier_id = CARRIER_MAPPING['default']
            carrier_lower = carrier_name.lower()
            
            for key in CARRIER_MAPPING.keys():
                if key in carrier_lower:
                    carrier_id = CARRIER_MAPPING[key]
                    break
            
            # Für jeden Artikel
            for item in order_data['items']:
                tracking_data_for_api.append({
                    'bestell_id': bestell_id,
                    'order_sn': item['bestellartikel_id'],
                    'quantity': item['menge'],
                    'tracking_number': tracking_number,
                    'carrier_id': carrier_id  # ✅ Richtige ID!
                })
        
        return tracking_data_for_api
