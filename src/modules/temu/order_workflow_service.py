"""TEMU Order Workflow Service - 5-Schritt Orchestrierung"""

from datetime import datetime
from typing import Dict

from config.settings import (
    TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT
)
from src.marketplace_connectors.temu.service import TemuMarketplaceService
from src.db.connection import get_db_connection
from src.db.repositories.temu.order_repository import OrderRepository
from src.db.repositories.temu.order_item_repository import OrderItemRepository
from src.db.repositories.jtl_common.jtl_repository import JtlRepository
from src.modules.temu.order_service import OrderService
from src.modules.xml_export.xml_export_service import XmlExportService
from src.modules.temu.tracking_service import TrackingService
from src.services.log_service import log_service


class OrderWorkflowService:
    """
    Orchestriert den kompletten TEMU Order Sync Workflow (5 Steps)
    Mit Dependency Injection und Shared Connections für bessere Performance
    """
    
    def __init__(
        self,
        temu_service: TemuMarketplaceService = None,
        order_service: OrderService = None,
        xml_service: XmlExportService = None,
        tracking_service: TrackingService = None
    ):
        """
        Initialisiere Service mit optionalen Dependencies
        Falls nicht injected, werden sie lazy erstellt bei Bedarf
        """
        self._temu_service = temu_service
        self._order_service = order_service
        self._xml_service = xml_service
        self._tracking_service = tracking_service
        
        # Shared DB Connections (lazy loaded)
        self._toci_conn = None
        self._jtl_conn = None
        self._order_repo = None
        self._item_repo = None
        self._jtl_repo = None
    
    def run_complete_workflow(
        self, 
        parent_order_status: int = 2, 
        days_back: int = 7, 
        verbose: bool = False
    ) -> bool:
        """
        Führe kompletten TEMU Order Sync aus (5 Schritte)
        
        Args:
            parent_order_status: TEMU Order Status (2=processing, 3=cancelled, 4=shipped, 5=delivered)
            days_back: Wie viele Tage zurück abrufen
            verbose: Detailliertes Logging
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        start_time = datetime.now()
        job_id = f"temu_orders_{int(start_time.timestamp())}"
        
        # Validierung
        valid_status = [2, 3, 4, 5]
        if parent_order_status not in valid_status:
            log_service.log(job_id, "order_workflow", "ERROR", 
                          f"Ungültiger Status: {parent_order_status}")
            return False
        
        if days_back < 1:
            log_service.log(job_id, "order_workflow", "ERROR", "Days muss >= 1 sein")
            return False
        
        log_service.start_job_capture(job_id, "order_workflow")
        
        try:
            # Step 1: API → JSON
            log_service.log(job_id, "order_workflow", "INFO", "[1/5] TEMU API → JSON")
            if not self._step_1_api_to_json(parent_order_status, days_back, verbose, job_id):
                raise Exception("API Fetch fehlgeschlagen")
            log_service.log(job_id, "order_workflow", "INFO", "✓ [1/5] API → JSON erfolgreich")
            
            # Step 2: JSON → Database
            log_service.log(job_id, "order_workflow", "INFO", "[2/5] JSON → Datenbank")
            result = self._step_2_json_to_db(job_id)
            log_service.log(job_id, "order_workflow", "INFO", 
                          f"✓ [2/5] JSON → DB: {result.get('imported', 0)} neu, {result.get('updated', 0)} aktualisiert")
            
            # Step 3: Database → XML Export
            log_service.log(job_id, "order_workflow", "INFO", "[3/5] Datenbank → XML Export")
            xml_result = self._step_3_db_to_xml(job_id)
            if xml_result.get('success'):
                log_service.log(job_id, "order_workflow", "INFO", 
                              f"✓ [3/5] DB → XML: {xml_result.get('exported', 0)} exportiert")
            else:
                log_service.log(job_id, "order_workflow", "INFO", 
                              f"✓ [3/5] DB → XML: {xml_result.get('message', 'Keine Orders')}")
            
            # Step 4: JTL → Tracking Update
            log_service.log(job_id, "order_workflow", "INFO", "[4/5] JTL → Tracking Update")
            tracking_result = self._step_4_tracking_to_db(job_id)
            log_service.log(job_id, "order_workflow", "INFO", 
                          f"✓ [4/5] JTL → Tracking: {tracking_result.get('updated', 0)} aktualisiert")
            
            # Step 5: Tracking → TEMU API
            log_service.log(job_id, "order_workflow", "INFO", "[5/5] Tracking → TEMU API")
            if not self._step_5_db_to_api(job_id):
                log_service.log(job_id, "order_workflow", "WARNING", 
                              "⚠ [5/5] Tracking Export fehlgeschlagen")
            else:
                log_service.log(job_id, "order_workflow", "INFO", 
                              "✓ [5/5] Tracking → API erfolgreich")
            
            # Erfolg
            duration = (datetime.now() - start_time).total_seconds()
            log_service.log(job_id, "order_workflow", "INFO", 
                          f"✓ TEMU Order Sync erfolgreich ({duration:.1f}s)")
            log_service.end_job_capture(success=True, duration=duration)
            return True
            
        except Exception as e:
            import traceback
            duration = (datetime.now() - start_time).total_seconds()
            error_trace = traceback.format_exc()
            log_service.log(job_id, "order_workflow", "ERROR", 
                          f"✗ TEMU Order Sync fehlgeschlagen: {str(e)}\n{error_trace}")
            log_service.end_job_capture(success=False, duration=duration, error=str(e))
            return False
    
    def _get_toci_connection(self):
        """Lazy-load TOCI connection (singleton für Workflow)"""
        if self._toci_conn is None:
            self._toci_conn = get_db_connection(database='toci', use_pool=True)
        return self._toci_conn
    
    def _get_jtl_connection(self):
        """Lazy-load JTL connection (singleton für Workflow)"""
        if self._jtl_conn is None:
            self._jtl_conn = get_db_connection(database='eazybusiness', use_pool=True)
        return self._jtl_conn
    
    def _get_order_repo(self):
        """Lazy-load OrderRepository (singleton für Workflow)"""
        if self._order_repo is None:
            self._order_repo = OrderRepository(connection=self._get_toci_connection())
        return self._order_repo
    
    def _get_item_repo(self):
        """Lazy-load OrderItemRepository (singleton für Workflow)"""
        if self._item_repo is None:
            self._item_repo = OrderItemRepository(connection=self._get_toci_connection())
        return self._item_repo
    
    def _get_jtl_repo(self):
        """Lazy-load JtlRepository (singleton für Workflow)"""
        if self._jtl_repo is None:
            try:
                self._jtl_repo = JtlRepository(connection=self._get_jtl_connection())
            except Exception:
                self._jtl_repo = None
        return self._jtl_repo
    
    def _get_temu_service(self, verbose: bool = False):
        """Lazy-load TemuMarketplaceService"""
        if self._temu_service is None:
            self._temu_service = TemuMarketplaceService(
                app_key=TEMU_APP_KEY,
                app_secret=TEMU_APP_SECRET,
                access_token=TEMU_ACCESS_TOKEN,
                endpoint=TEMU_API_ENDPOINT,
                verbose=verbose
            )
        return self._temu_service
    
    def _get_order_service(self):
        """Lazy-load OrderService"""
        if self._order_service is None:
            self._order_service = OrderService(
                order_repo=self._get_order_repo(),
                item_repo=self._get_item_repo()
            )
        return self._order_service
    
    def _get_xml_service(self):
        """Lazy-load XmlExportService"""
        if self._xml_service is None:
            self._xml_service = XmlExportService(
                order_repo=self._get_order_repo(),
                item_repo=self._get_item_repo(),
                jtl_repo=self._get_jtl_repo()
            )
        return self._xml_service
    
    def _get_tracking_service(self):
        """Lazy-load TrackingService"""
        if self._tracking_service is None:
            self._tracking_service = TrackingService(
                order_repo=self._get_order_repo(),
                jtl_repo=self._get_jtl_repo()
            )
        return self._tracking_service
    
    def _step_1_api_to_json(
        self, 
        parent_order_status: int, 
        days_back: int, 
        verbose: bool, 
        job_id: str
    ) -> bool:
        """Step 1: Hole Orders von TEMU API und speichere als JSON"""
        try:
            temu_service = self._get_temu_service(verbose)
            
            result = temu_service.fetch_orders(
                parent_order_status=parent_order_status, 
                days_back=days_back, 
                job_id=job_id
            )
            
            return bool(result)
            
        except Exception as e:
            import traceback
            log_service.log(job_id, "api_to_json", "ERROR", 
                          f"✗ API Abruf Fehler: {str(e)}\n{traceback.format_exc()}")
            return False
    
    def _step_2_json_to_db(self, job_id: str) -> Dict:
        """Step 2: Importiere JSON Orders in Datenbank"""
        try:
            order_service = self._get_order_service()
            result = order_service.import_from_json_files(job_id=job_id)
            return result
            
        except Exception as e:
            import traceback
            log_service.log(job_id, "json_to_db", "ERROR", 
                          f"✗ JSON Import Fehler: {str(e)}\n{traceback.format_exc()}")
            return {'imported': 0, 'updated': 0}
    
    def _step_3_db_to_xml(self, job_id: str) -> Dict:
        """Step 3: Exportiere Orders als XML für JTL"""
        try:
            xml_service = self._get_xml_service()
            jtl_repo = self._get_jtl_repo()
            
            result = xml_service.export_to_xml(
                save_to_disk=True, 
                import_to_jtl=jtl_repo is not None, 
                job_id=job_id
            )
            return result
            
        except Exception as e:
            import traceback
            log_service.log(job_id, "db_to_xml", "ERROR", 
                          f"✗ XML Export Fehler: {str(e)}\n{traceback.format_exc()}")
            return {'success': False, 'message': str(e)}
    
    def _step_4_tracking_to_db(self, job_id: str) -> Dict:
        """Step 4: Hole Tracking-Daten aus JTL und aktualisiere DB"""
        try:
            tracking_service = self._get_tracking_service()
            result = tracking_service.update_tracking_from_jtl(job_id)
            return result
            
        except Exception as e:
            import traceback
            log_service.log(job_id, "tracking_to_db", "ERROR", 
                          f"✗ Tracking Update Fehler: {str(e)}\n{traceback.format_exc()}")
            return {'updated': 0, 'errors': 0}
    
    def _step_5_db_to_api(self, job_id: str) -> bool:
        """Step 5: Exportiere Tracking-Daten zu TEMU API"""
        try:
            if not all([TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN]):
                log_service.log(job_id, "tracking_to_api", "ERROR", 
                              "✗ TEMU Credentials nicht gesetzt!")
                return False
            
            order_repo = self._get_order_repo()
            tracking_service = self._get_tracking_service()
            temu_service = self._get_temu_service()
            
            orders_data = order_repo.get_orders_for_tracking_export()
            
            if not orders_data:
                log_service.log(job_id, "tracking_to_api", "INFO", 
                              "✓ Keine Bestellungen zum Exportieren")
                return True
            
            tracking_data_for_api = tracking_service.prepare_tracking_for_api(orders_data, job_id)
            
            if not tracking_data_for_api:
                log_service.log(job_id, "tracking_to_api", "INFO", 
                              "✓ Keine Tracking-Daten zum Upload")
                return True
            
            success, error_code, error_msg = temu_service.upload_tracking(
                tracking_data_for_api, 
                job_id
            )
            
            if success:
                for order_data in orders_data:
                    order_repo.update_temu_tracking_status(order_data['order_id'])
                log_service.log(job_id, "tracking_to_api", "INFO",
                              f"✓ Tracking Export erfolgreich: {len(tracking_data_for_api)} Positionen")
                return True
            
            log_service.log(job_id, "tracking_to_api", "ERROR",
                          f"✗ Tracking Export fehlgeschlagen: Code {error_code}, Message: {error_msg}")
            return False
            
        except Exception as e:
            import traceback
            log_service.log(job_id, "tracking_to_api", "ERROR", 
                          f"✗ Tracking Export Fehler: {str(e)}\n{traceback.format_exc()}")
            return False
