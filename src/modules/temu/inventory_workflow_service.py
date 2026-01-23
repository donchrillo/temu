"""TEMU Inventory Workflow Service - 4-Schritt Orchestrierung"""

from datetime import datetime
from typing import Dict

from config.settings import TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT
from src.services.log_service import log_service
from src.db.connection import get_db_connection
from src.db.repositories.temu.product_repository import ProductRepository
from src.db.repositories.temu.inventory_repository import InventoryRepository
from src.db.repositories.jtl_common.jtl_repository import JtlRepository
from src.marketplace_connectors.temu.service import TemuMarketplaceService
from src.modules.temu.inventory_service import InventoryService
from src.modules.temu.stock_sync_service import StockSyncService


class InventoryWorkflowService:
    """
    Orchestriert den kompletten TEMU Inventory Sync Workflow (4 Steps)
    Separiert von CLI-Wrapper für bessere Testbarkeit und Wiederverwendbarkeit
    """
    
    def __init__(self):
        """Initialisiere Service ohne externe Dependencies"""
        pass
    
    def run_complete_workflow(self, mode: str = "quick", verbose: bool = False) -> bool:
        """
        Führe kompletten TEMU Inventory Sync aus (4 Schritte)
        
        Args:
            mode: "full" (alle 4 Steps) oder "quick" (nur Steps 3+4)
            verbose: Detailliertes Logging
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        start_time = datetime.now()
        job_id = f"temu_inventory_{int(start_time.timestamp())}"
        
        log_service.start_job_capture(job_id, "inventory_workflow")
        
        try:
            if mode == "full":
                # Step 1: TEMU API → JSON
                log_service.log(job_id, "inventory_workflow", "INFO", "[1/4] TEMU API → JSON")
                if not self._step_1_api_to_json(job_id, verbose):
                    raise Exception("API Fetch fehlgeschlagen")
                log_service.log(job_id, "inventory_workflow", "INFO", "✓ [1/4] API → JSON erfolgreich")
                
                # Step 2: JSON → Database
                log_service.log(job_id, "inventory_workflow", "INFO", "[2/4] JSON → Datenbank")
                self._step_2_json_to_db(job_id)
                log_service.log(job_id, "inventory_workflow", "INFO", "✓ [2/4] JSON → DB erfolgreich")
            else:
                log_service.log(job_id, "inventory_workflow", "INFO", 
                              f"Quick Mode: Überspringe Steps 1+2 (SKU-Import)")
            
            # Step 3: JTL Stock → Inventory (immer ausführen)
            log_service.log(job_id, "inventory_workflow", "INFO", "[3/4] JTL → Inventory Update")
            self._step_3_jtl_stock_to_inventory(job_id)
            log_service.log(job_id, "inventory_workflow", "INFO", "✓ [3/4] JTL → Inventory erfolgreich")
            
            # Step 4: Inventory → TEMU API (immer ausführen)
            log_service.log(job_id, "inventory_workflow", "INFO", "[4/4] Inventory → TEMU API")
            self._step_4_sync_to_temu(job_id)
            log_service.log(job_id, "inventory_workflow", "INFO", "✓ [4/4] Sync → API erfolgreich")
            
            # Erfolg
            duration = (datetime.now() - start_time).total_seconds()
            log_service.log(job_id, "inventory_workflow", "INFO", 
                          f"✓ TEMU Inventory Sync erfolgreich (mode={mode}, {duration:.1f}s)")
            log_service.end_job_capture(success=True, duration=duration)
            return True
            
        except Exception as e:
            import traceback
            duration = (datetime.now() - start_time).total_seconds()
            error_trace = traceback.format_exc()
            log_service.log(job_id, "inventory_workflow", "ERROR", 
                          f"✗ TEMU Inventory Sync fehlgeschlagen: {str(e)}\n{error_trace}")
            log_service.end_job_capture(success=False, duration=duration, error=str(e))
            return False
    
    def _step_1_api_to_json(self, job_id: str, verbose: bool) -> bool:
        """Step 1: Hole SKU-Liste von TEMU API und speichere als JSON"""
        try:
            temu_service = TemuMarketplaceService(
                app_key=TEMU_APP_KEY,
                app_secret=TEMU_APP_SECRET,
                access_token=TEMU_ACCESS_TOKEN,
                endpoint=TEMU_API_ENDPOINT,
                verbose=verbose
            )
            
            log_service.log(job_id, "api_to_json", "INFO", 
                          "→ Hole TEMU SKU-Liste (Status 2 & 3, pageSize=100)")
            
            result = temu_service.fetch_inventory_skus(job_id=job_id, page_size=100)
            
            if result:
                log_service.log(job_id, "api_to_json", "INFO", 
                              "✓ SKU-Liste erfolgreich heruntergeladen")
                return True
            
            log_service.log(job_id, "api_to_json", "WARNING", 
                          "⚠ API Abruf fehlgeschlagen oder keine SKUs")
            return False
            
        except Exception as e:
            import traceback
            log_service.log(job_id, "api_to_json", "ERROR", 
                          f"✗ API Abruf Fehler: {str(e)}\n{traceback.format_exc()}")
            return False
    
    def _step_2_json_to_db(self, job_id: str) -> None:
        """Step 2: Importiere JSON SKUs in temu_products Tabelle"""
        try:
            log_service.log(job_id, "json_to_db", "INFO", 
                          "→ Importiere SKU-JSON in temu_products")
            
            toci_conn = get_db_connection(database="toci", use_pool=True)
            product_repo = ProductRepository(connection=toci_conn)
            inv_service = InventoryService()
            
            stats = inv_service.import_products_from_raw(product_repo, job_id=job_id)
            
            log_service.log(job_id, "json_to_db", "INFO", 
                          f"✓ Produkte importiert: {stats}")
            
        except Exception as e:
            import traceback
            log_service.log(job_id, "json_to_db", "ERROR", 
                          f"✗ JSON Import Fehler: {str(e)}\n{traceback.format_exc()}")
            raise
    
    def _step_3_jtl_stock_to_inventory(self, job_id: str) -> None:
        """Step 3: Lese JTL Bestände und aktualisiere temu_inventory"""
        try:
            log_service.log(job_id, "jtl_to_inventory", "INFO", 
                          "→ Lese JTL Bestände und aktualisiere temu_inventory")
            
            toci_conn = get_db_connection(database="toci", use_pool=True)
            jtl_conn = get_db_connection(database="eazybusiness", use_pool=True)
            product_repo = ProductRepository(connection=toci_conn)
            inventory_repo = InventoryRepository(connection=toci_conn)
            jtl_repo = JtlRepository(connection=jtl_conn)
            inv_service = InventoryService()
            
            stats = inv_service.refresh_inventory_from_jtl(
                product_repo, 
                inventory_repo, 
                jtl_repo, 
                job_id=job_id
            )
            
            log_service.log(job_id, "jtl_to_inventory", "INFO", 
                          f"✓ Bestand aktualisiert: {stats}")
            
        except Exception as e:
            import traceback
            log_service.log(job_id, "jtl_to_inventory", "ERROR", 
                          f"✗ Bestands-Update Fehler: {str(e)}\n{traceback.format_exc()}")
            raise
    
    def _step_4_sync_to_temu(self, job_id: str) -> None:
        """Step 4: Sende Delta-Bestände an TEMU API"""
        try:
            log_service.log(job_id, "inventory_to_api", "INFO", 
                          "→ Sende Delta-Bestände an TEMU")
            
            toci_conn = get_db_connection(database="toci", use_pool=True)
            inventory_repo = InventoryRepository(connection=toci_conn)
            temu_service = TemuMarketplaceService(
                app_key=TEMU_APP_KEY,
                app_secret=TEMU_APP_SECRET,
                access_token=TEMU_ACCESS_TOKEN,
                endpoint=TEMU_API_ENDPOINT
            )
            
            sync_service = StockSyncService()
            sync_service.sync_deltas_to_temu(
                temu_service.inventory_api, 
                inventory_repo, 
                job_id=job_id
            )
            
            log_service.log(job_id, "inventory_to_api", "INFO", 
                          "✓ Delta-Upload abgeschlossen")
            
        except Exception as e:
            import traceback
            log_service.log(job_id, "inventory_to_api", "ERROR", 
                          f"✗ Sync Upload Fehler: {str(e)}\n{traceback.format_exc()}")
            raise
