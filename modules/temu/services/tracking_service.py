"""Tracking Service - Hole Tracking aus JTL, Update DB, Upload zu TEMU"""

from typing import Dict, List, Optional
from src.db.repositories.temu.order_repository import OrderRepository
from src.db.repositories.jtl_common.jtl_repository import JtlRepository
from modules.shared import log_service

class TrackingService:
    """
    Tracking Workflow:
    1. Hole Tracking aus JTL (Lieferscheindaten)
    2. Update Orders in TOCI mit Tracking
    3. Prepare für API Upload
    """
    
    def __init__(self, order_repo: OrderRepository, jtl_repo: JtlRepository = None):
        self.order_repo = order_repo
        self.jtl_repo = jtl_repo
    
    def update_tracking_from_jtl(self, job_id: Optional[str] = None) -> Dict:
        """
        Hauptmethod: Hole Tracking aus JTL und update TOCI
        
        Args:
            job_id: Optional - für strukturiertes Logging
        
        Returns:
            dict mit updated/errors/success/tracking_data
        """
        
        try:

            if not self.jtl_repo:
                log_service.log(job_id, "tracking_service", "ERROR", "✗ Kein JTL-Repo verfügbar")
                return {
                    'updated': 0,
                    'errors': 1,
                    'success': False,
                    'tracking_data': []
                }

            log_service.log(job_id, "tracking_service", "INFO", 
                              "→ Hole Orders ohne Tracking...")
            
            orders_without_tracking = self.order_repo.find_orders_for_tracking()
            
            if not orders_without_tracking:
                log_service.log(job_id, "tracking_service", "INFO", 
                                  "✓ Keine Bestellungen ohne Tracking")
                
                return {
                    'updated': 0,
                    'errors': 0,
                    'success': True,
                    'tracking_data': []
                }
            
            log_service.log(job_id, "tracking_service", "INFO", 
                              f"✓ {len(orders_without_tracking)} Bestellungen ohne Tracking gefunden")
            
            updated_count = 0
            error_count = 0
            tracking_data_for_api = []  # wird aktuell nicht genutzt, behalten für Rückgabekompatibilität
            
            # Step 2 & 3: Für jede Order - suche Tracking in JTL & update TOCI
            for order in orders_without_tracking:
                try:
                    # Hole Tracking aus JTL!
                    tracking_info = self.jtl_repo.get_tracking_from_lieferschein(
                        order.bestell_id
                    )
                    
                    if not tracking_info:
                        log_service.log(job_id, "tracking_service", "WARNING", 
                                      f"⚠ {order.bestell_id}: Kein Tracking in JTL gefunden")
                        # ← Kein else-Print!
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

                        log_service.log(job_id, "tracking_service", "INFO", 
                                      f"✓ {order.bestell_id}: {tracking_info['tracking_number']}")
                        updated_count += 1
                    else:

                        log_service.log(job_id, "tracking_service", "ERROR", 
                                          f"✗ {order.bestell_id}: DB Update fehlgeschlagen")
                        error_count += 1
                
                except Exception as e:

                    log_service.log(job_id, "tracking_service", "ERROR", 
                                      f"✗ {order.bestell_id}: {str(e)}")

                    error_count += 1
            

            log_service.log(job_id, "tracking_service", "INFO", 
                              f"✓ Tracking-Sync: {updated_count} aktualisiert")
            log_service.log(job_id, "tracking_service", "INFO", 
                              f"✓ {len(tracking_data_for_api)} bereit für API Upload")
            # ← Kein else-Print!
            
            return {
                'updated': updated_count,
                'errors': error_count,
                'success': error_count == 0,
                'tracking_data': tracking_data_for_api
            }
        
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            

            log_service.log(job_id, "tracking_service", "ERROR", 
                              f"✗ Tracking Update Fehler: {str(e)}")
            log_service.log(job_id, "tracking_service", "ERROR", error_trace)
            
            return {
                'updated': 0,
                'errors': 1,
                'success': False,
                'tracking_data': []
            }
    
    def prepare_tracking_for_api(self, orders_data: List[Dict], job_id: Optional[str] = None) -> List[Dict]:
        """
        Konvertiere Tracking-Daten für TEMU API Format
        MIT Carrier ID Mapping!
        
        Args:
            orders_data: List mit Tracking-Daten aus DB
            job_id: Optional - für strukturiertes Logging
        
        Returns:
            List mit TEMU API Format
        """
        
        try:
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
            

            log_service.log(job_id, "tracking_service", "INFO", 
                              f"✓ {len(tracking_data_for_api)} Tracking-Daten für API vorbereitet")
            
            return tracking_data_for_api
        
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            

            log_service.log(job_id, "tracking_service", "ERROR", 
                              f"✗ Prepare Tracking Fehler: {str(e)}")
            log_service.log(job_id, "tracking_service", "ERROR", error_trace)

            
            return []
