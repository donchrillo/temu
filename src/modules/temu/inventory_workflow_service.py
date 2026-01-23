"""TEMU Inventory Workflow Service - 4-Schritt Orchestrierung"""

from datetime import datetime

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
    """TEMU Inventory Workflow mit Dependency Injection und Lazy Caches."""
    
    def __init__(
        self,
        temu_service: TemuMarketplaceService | None = None,
        inventory_service: InventoryService | None = None,
        stock_sync_service: StockSyncService | None = None,
    ):
        self._temu_service = temu_service
        self._inventory_service = inventory_service
        self._stock_sync_service = stock_sync_service

        self._toci_conn = None
        self._jtl_conn = None
        self._product_repo = None
        self._inventory_repo = None
        self._jtl_repo = None
    
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

        # Credential Guard – vermeidet nutzlose API-Aufrufe
        if not all([TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN]):
            log_service.log(job_id, "inventory_workflow", "ERROR", "✗ TEMU Credentials nicht gesetzt!")
            log_service.end_job_capture(success=False, duration=0, error="missing credentials")
            return False
        
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
            temu_service = self._get_temu_service(verbose=verbose)
            inv_service = self._get_inventory_service()

            log_service.log(job_id, "api_to_json", "INFO", 
                          "→ Hole TEMU SKU-Liste (Status 2 & 3, pageSize=100)")

            ok = inv_service.fetch_and_store_raw_skus(
                temu_inventory_api=temu_service.inventory_api,
                job_id=job_id,
            )

            if ok:
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

            product_repo = self._get_product_repo()
            inv_service = self._get_inventory_service()

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

            product_repo = self._get_product_repo()
            inventory_repo = self._get_inventory_repo()
            jtl_repo = self._get_jtl_repo()
            inv_service = self._get_inventory_service()

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

            inventory_repo = self._get_inventory_repo()
            temu_service = self._get_temu_service()
            sync_service = self._get_stock_sync_service()

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

    # --- Lazy Loader Helpers ---

    def _get_toci_conn(self):
        if self._toci_conn is None:
            self._toci_conn = get_db_connection(database="toci", use_pool=True)
        return self._toci_conn

    def _get_jtl_conn(self):
        if self._jtl_conn is None:
            self._jtl_conn = get_db_connection(database="eazybusiness", use_pool=True)
        return self._jtl_conn

    def _get_product_repo(self):
        if self._product_repo is None:
            self._product_repo = ProductRepository(connection=self._get_toci_conn())
        return self._product_repo

    def _get_inventory_repo(self):
        if self._inventory_repo is None:
            self._inventory_repo = InventoryRepository(connection=self._get_toci_conn())
        return self._inventory_repo

    def _get_jtl_repo(self):
        if self._jtl_repo is None:
            try:
                self._jtl_repo = JtlRepository(connection=self._get_jtl_conn())
            except Exception:
                self._jtl_repo = None
        return self._jtl_repo

    def _get_temu_service(self, verbose: bool = False):
        if self._temu_service is None:
            self._temu_service = TemuMarketplaceService(
                app_key=TEMU_APP_KEY,
                app_secret=TEMU_APP_SECRET,
                access_token=TEMU_ACCESS_TOKEN,
                endpoint=TEMU_API_ENDPOINT,
                verbose=verbose,
            )
        return self._temu_service

    def _get_inventory_service(self):
        if self._inventory_service is None:
            self._inventory_service = InventoryService()
        return self._inventory_service

    def _get_stock_sync_service(self):
        if self._stock_sync_service is None:
            self._stock_sync_service = StockSyncService()
        return self._stock_sync_service
