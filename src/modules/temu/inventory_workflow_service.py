"""TEMU Inventory Workflow Service - 4-Schritt Orchestrierung (Final)"""

from datetime import datetime
from typing import Dict, Any

from config.settings import TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT, DB_TOCI, DB_JTL
from src.services.log_service import log_service
from src.db.connection import db_connect
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

        # Shared DB Connections (werden im run gesetzt)
        self._toci_conn = None
        self._jtl_conn = None
        
        # Repo Caches
        self._product_repo = None
        self._inventory_repo = None
        self._jtl_repo = None
    
    def run_complete_workflow(self, mode: str = "quick", verbose: bool = False) -> bool:
        """
        Führe kompletten TEMU Inventory Sync aus (4 Schritte)
        Transaktionssicher: Alles oder nichts.
        """
        start_time = datetime.now()
        job_id = f"temu_inventory_{int(start_time.timestamp())}"
        
        log_service.start_job_capture(job_id, "inventory_workflow")

        # Credential Guard
        if not all([TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN]):
            log_service.log(job_id, "inventory_workflow", "ERROR", "✗ TEMU Credentials nicht gesetzt!")
            log_service.end_job_capture(success=False, duration=0, error="missing credentials")
            return False
        
        try:
            # --- TRANSAKTIONS-START ---
            # Wir öffnen beide Connections. Wenn eine crasht, rollen beide zurück.
            with db_connect(DB_TOCI) as toci_conn:
                self._toci_conn = toci_conn
                
                with db_connect(DB_JTL) as jtl_conn:
                    self._jtl_conn = jtl_conn
                    
                    # Step 1 & 2: Full Mode (SKU Import)
                    if mode == "full":
                        log_service.log(job_id, "inventory_workflow", "INFO", "[1/4] TEMU API → JSON")
                        # Step 1 braucht keine DB Transaction, ist nur API Call
                        if not self._step_1_api_to_json(job_id, verbose):
                            raise Exception("API Fetch fehlgeschlagen")
                        log_service.log(job_id, "inventory_workflow", "INFO", "✓ [1/4] API → JSON erfolgreich")
                        
                        log_service.log(job_id, "inventory_workflow", "INFO", "[2/4] JSON → Datenbank")
                        # Step 2 schreibt in DB_TOCI
                        self._step_2_json_to_db(job_id)
                        log_service.log(job_id, "inventory_workflow", "INFO", "✓ [2/4] JSON → DB erfolgreich")
                    else:
                        log_service.log(job_id, "inventory_workflow", "INFO", 
                                      f"Quick Mode: Überspringe Steps 1+2 (SKU-Import)")
                    
                    # Step 3: JTL Stock → Inventory (Lesen von JTL, Schreiben in TOCI)
                    log_service.log(job_id, "inventory_workflow", "INFO", "[3/4] JTL → Inventory Update")
                    self._step_3_jtl_stock_to_inventory(job_id)
                    log_service.log(job_id, "inventory_workflow", "INFO", "✓ [3/4] JTL → Inventory erfolgreich")
                    
                    # Step 4: Inventory → TEMU API (Lesen von TOCI, API Upload, Update TOCI)
                    log_service.log(job_id, "inventory_workflow", "INFO", "[4/4] Inventory → TEMU API")
                    self._step_4_sync_to_temu(job_id)
                    log_service.log(job_id, "inventory_workflow", "INFO", "✓ [4/4] Sync → API erfolgreich")
            
            # --- TRANSAKTIONS-ENDE (Auto-Commit) ---

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
                          f"✗ TEMU Inventory Sync fehlgeschlagen (Rollback): {str(e)}\n{error_trace}")
            log_service.end_job_capture(success=False, duration=duration, error=str(e))
            return False
        finally:
            # Aufräumen für nächsten Run
            self._toci_conn = None
            self._jtl_conn = None
            self._product_repo = None
            self._inventory_repo = None
            self._jtl_repo = None
    
    # ... (Step Methoden bleiben fast gleich, nur Aufrufe sind jetzt sicher) ...

    def _step_1_api_to_json(self, job_id: str, verbose: bool) -> bool:
        """Step 1: Hole SKU-Liste von TEMU API"""
        try:
            temu_service = self._get_temu_service(verbose=verbose)
            inv_service = self._get_inventory_service()

            ok = inv_service.fetch_and_store_raw_skus(
                temu_inventory_api=temu_service.inventory_api,
                job_id=job_id,
            )
            return ok
        except Exception as e:
            log_service.log(job_id, "api_to_json", "ERROR", f"✗ API Fehler: {str(e)}")
            return False
    
    def _step_2_json_to_db(self, job_id: str) -> None:
        """Step 2: Importiere JSON SKUs"""
        # Repo nutzt jetzt self._toci_conn aus dem Kontext
        product_repo = self._get_product_repo()
        inv_service = self._get_inventory_service()
        inv_service.import_products_from_raw(product_repo, job_id=job_id)
    
    def _step_3_jtl_stock_to_inventory(self, job_id: str) -> None:
        """Step 3: JTL -> Toci"""
        product_repo = self._get_product_repo()
        inventory_repo = self._get_inventory_repo()
        jtl_repo = self._get_jtl_repo()
        inv_service = self._get_inventory_service()

        inv_service.refresh_inventory_from_jtl(
            product_repo, 
            inventory_repo, 
            jtl_repo, 
            job_id=job_id
        )
    
    def _step_4_sync_to_temu(self, job_id: str) -> None:
        """Step 4: Toci -> API"""
        inventory_repo = self._get_inventory_repo()
        temu_service = self._get_temu_service()
        sync_service = self._get_stock_sync_service()

        sync_service.sync_deltas_to_temu(
            temu_service.inventory_api, 
            inventory_repo, 
            job_id=job_id
        )

    # --- Lazy Loader Helpers (angepasst auf Injection) ---

    def _get_product_repo(self):
        if self._product_repo is None:
            # WICHTIG: Nutze die aktive Connection aus dem Context
            self._product_repo = ProductRepository(connection=self._toci_conn)
        return self._product_repo

    def _get_inventory_repo(self):
        if self._inventory_repo is None:
            self._inventory_repo = InventoryRepository(connection=self._toci_conn)
        return self._inventory_repo

    def _get_jtl_repo(self):
        if self._jtl_repo is None:
            self._jtl_repo = JtlRepository(connection=self._jtl_conn)
        return self._jtl_repo

    # ... (Restliche Getter für Services bleiben gleich) ...
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