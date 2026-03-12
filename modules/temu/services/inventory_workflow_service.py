"""TEMU Inventory Workflow Service - 4-Schritt Orchestrierung"""

import traceback
from datetime import datetime
from typing import Dict, Any

from modules.shared.config.settings import DB_TOCI, DB_JTL
from modules.shared import log_service
from modules.shared import db_connect
from modules.shared.database.repositories.temu.product_repository import ProductRepository
from modules.shared.database.repositories.temu.inventory_repository import InventoryRepository
from modules.shared.connectors.temu.service import TemuMarketplaceService
from .base_workflow_service import BaseWorkflowService
from .inventory_service import InventoryService
from .stock_sync_service import StockSyncService


class InventoryWorkflowService(BaseWorkflowService):
    """TEMU Inventory Workflow - Split Transactions for Stability"""
    
    def __init__(
        self,
        temu_service: TemuMarketplaceService | None = None,
        inventory_service: InventoryService | None = None,
        stock_sync_service: StockSyncService | None = None,
    ):
        super().__init__()
        # Optionale Injection (für Tests)
        self._temu_service = temu_service
        self._inventory_service = inventory_service
        self._stock_sync_service = stock_sync_service
        
        # Domain-spezifische Repo Caches
        self._product_repo = None
        self._inventory_repo = None
    
    def run_complete_workflow(self, mode: str = "quick", verbose: bool = False) -> bool:
        """
        Führe kompletten TEMU Inventory Sync aus (4 Schritte)
        Splittet Transaktionen in Blöcke für bessere Stabilität.
        """
        start_time = datetime.now()
        job_id = self._generate_job_id("temu_inventory")
        
        log_service.start_job_capture(job_id, "inventory_workflow")

        # Credential Guard
        if not self._validate_credentials(job_id, "inventory_workflow"):
            log_service.end_job_capture(success=False, duration=0, error="missing credentials")
            return False
        
        try:
            # ==============================================================================
            # BLOCK 1: SKU IMPORT (Nur bei mode="full")
            # ==============================================================================
            if mode == "full":
                log_service.log(job_id, "inventory_workflow", "INFO", "[1/4] TEMU API → JSON")
                if not self._step_1_api_to_json(job_id, verbose):
                    raise Exception("API Fetch fehlgeschlagen")
                
                with db_connect(DB_TOCI) as toci_conn:
                    self._toci_conn = toci_conn
                    log_service.log(job_id, "inventory_workflow", "INFO", "[2/4] JSON → Datenbank")
                    self._step_2_json_to_db(job_id)
                
                log_service.log(job_id, "inventory_workflow", "INFO", "✓ Block 1 (SKU Import) abgeschlossen")
                self._cleanup_connections()
            else:
                log_service.log(job_id, "inventory_workflow", "INFO", "Quick Mode: Überspringe Block 1 (SKU-Import)")

            # ==============================================================================
            # BLOCK 2: JTL STOCK UPDATE
            # ==============================================================================
            log_service.log(job_id, "inventory_workflow", "INFO", "[3/4] JTL → Inventory Update")
            with db_connect(DB_TOCI) as toci_conn:
                self._toci_conn = toci_conn
                with db_connect(DB_JTL) as jtl_conn:
                    self._jtl_conn = jtl_conn
                    self._step_3_jtl_stock_to_inventory(job_id)
            
            log_service.log(job_id, "inventory_workflow", "INFO", "✓ Block 2 (JTL Update) abgeschlossen")
            self._cleanup_connections()

            # ==============================================================================
            # BLOCK 3: TEMU API SYNC
            # ==============================================================================
            log_service.log(job_id, "inventory_workflow", "INFO", "[4/4] Inventory → TEMU API")
            # Wir nutzen hier db_connect nur zum Lesen und finalen Markieren.
            # StockSyncService sollte idealerweise intern kleine Transaktionen machen 
            # oder wir akzeptieren hier eine längere Transaktion für den finalen Mark-Sync.
            with db_connect(DB_TOCI) as toci_conn:
                self._toci_conn = toci_conn
                self._step_4_sync_to_temu(job_id)
            
            log_service.log(job_id, "inventory_workflow", "INFO", "✓ Block 3 (API Sync) abgeschlossen")

            # Erfolg
            duration = (datetime.now() - start_time).total_seconds()
            log_service.log(job_id, "inventory_workflow", "INFO", 
                          f"✓ TEMU Inventory Sync erfolgreich (mode={mode}, {duration:.1f}s)")
            log_service.end_job_capture(success=True, duration=duration)
            return True
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_trace = traceback.format_exc()
            log_service.log(job_id, "inventory_workflow", "ERROR", 
                          f"✗ TEMU Inventory Sync fehlgeschlagen: {str(e)}", error_text=error_trace)
            log_service.end_job_capture(success=False, duration=duration, error=str(e))
            return False
        finally:
            self._cleanup_connections()

    def _cleanup_service_caches(self):
        """Setzt domain-spezifische Repo-/Service-Caches zurück."""
        self._product_repo = None
        self._inventory_repo = None
        self._inventory_service = None
        self._stock_sync_service = None
    
    # ... (Restliche Methoden) ...

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

    # --- Lazy Loader Helpers ---

    def _get_product_repo(self) -> ProductRepository:
        if self._product_repo is None:
            self._product_repo = ProductRepository(connection=self._toci_conn)
        return self._product_repo

    def _get_inventory_repo(self) -> InventoryRepository:
        if self._inventory_repo is None:
            self._inventory_repo = InventoryRepository(connection=self._toci_conn)
        return self._inventory_repo

    def _get_inventory_service(self) -> InventoryService:
        if self._inventory_service is None:
            self._inventory_service = InventoryService()
        return self._inventory_service

    def _get_stock_sync_service(self) -> StockSyncService:
        if self._stock_sync_service is None:
            self._stock_sync_service = StockSyncService()
        return self._stock_sync_service