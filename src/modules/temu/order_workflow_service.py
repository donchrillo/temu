"""TEMU Order Workflow Service - 5-Schritt Orchestrierung"""

import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

from config.settings import (
    TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT,
    TEMU_API_RESPONSES_DIR, DB_TOCI, DB_JTL
)
from src.db.connection import db_connect
from src.db.repositories.temu.order_repository import OrderRepository
from src.db.repositories.temu.order_item_repository import OrderItemRepository
from src.db.repositories.jtl_common.jtl_repository import JtlRepository
from src.marketplace_connectors.temu.service import TemuMarketplaceService
from src.modules.temu.order_service import OrderService
from src.modules.xml_export.xml_export_service import XmlExportService
from src.modules.temu.tracking_service import TrackingService
from src.services.log_service import log_service


class OrderWorkflowService:
    """
    Orchestriert den kompletten TEMU Order Sync Workflow.
    Splittet Transaktionen in logische Blöcke (Import vs. Tracking).
    """
    
    def __init__(self):
        # Service Caches
        self._temu_service = None
        self._order_service = None
        self._xml_service = None
        self._tracking_service = None
        
        # Connection & Repo Caches (werden pro Block neu gesetzt)
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
        start_time = datetime.now()
        job_id = f"temu_orders_{int(start_time.timestamp())}"
        
        # Validierung
        if parent_order_status not in [2, 3, 4, 5]:
            log_service.log(job_id, "order_workflow", "ERROR", f"Ungültiger Status: {parent_order_status}")
            return False
        
        if not all([TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN]):
            log_service.log(job_id, "order_workflow", "ERROR", "TEMU Credentials fehlen")
            return False
        
        log_service.start_job_capture(job_id, "order_workflow")
        
        workflow_success = True
        
        # ==============================================================================
        # BLOCK 1: IMPORT & XML (Kritisch - Neue Bestellungen anlegen)
        # ==============================================================================
        try:
            # Step 1: API → JSON (Keine DB notwendig)
            log_service.log(job_id, "order_workflow", "INFO", "[1/5] TEMU API → JSON")
            if not self._step_1_api_to_json(parent_order_status, days_back, verbose, job_id):
                raise Exception("API Fetch fehlgeschlagen")
            
            # DB Transaktion für Import (Step 2: JSON → DB)
            with db_connect(DB_TOCI) as toci_conn:
                self._toci_conn = toci_conn
                
                with db_connect(DB_JTL) as jtl_conn:
                    self._jtl_conn = jtl_conn

                    # Step 2: JSON → Database
                    log_service.log(job_id, "order_workflow", "INFO", "[2/5] JSON → Datenbank")
                    result = self._step_2_json_to_db(job_id)
                    log_service.log(job_id, "order_workflow", "INFO", 
                                  f"✓ [2/5] Import: {result.get('imported', 0)} neu, {result.get('updated', 0)} update")
            
            # COMMIT nach Step 2 - Daten sind jetzt in DB sichtbar!
            log_service.log(job_id, "order_workflow", "INFO", "✓ Step 2 committed - Daten persistent")

            # Repositories/Services verwerfen, damit Step 3 frische Connections nutzt
            self._reset_repos_and_services()
            
            # Neue Transaktion für XML Export (Step 3)
            with db_connect(DB_TOCI) as toci_conn:
                self._toci_conn = toci_conn
                
                with db_connect(DB_JTL) as jtl_conn:
                    self._jtl_conn = jtl_conn
                    
                    # Step 3: Database → XML Export
                    log_service.log(job_id, "order_workflow", "INFO", "[3/5] Datenbank → XML Export")
                    xml_result = self._step_3_db_to_xml(job_id)
                    if not xml_result.get('success'):
                        log_service.log(job_id, "order_workflow", "WARNING", f"⚠ [3/5] XML: {xml_result.get('message')}")
                    else:
                        log_service.log(job_id, "order_workflow", "INFO", f"✓ [3/5] XML: {xml_result.get('exported', 0)} exportiert")
            
            # HIER COMMIT für Block 1 (automatisch durch with db_connect exit)
            log_service.log(job_id, "order_workflow", "INFO", "✓ Import-Phase abgeschlossen & gespeichert")

        except Exception as e:
            workflow_success = False
            error_trace = traceback.format_exc()
            log_service.log(job_id, "order_workflow", "ERROR", f"✗ Import-Phase fehlgeschlagen (Rollback): {str(e)}\n{error_trace}")
            # Wir brechen hier ab, weil ohne Import auch kein Tracking Sinn macht
            log_service.end_job_capture(success=False, duration=0, error=str(e))
            return False
        finally:
            self._cleanup_connections() # Clean für nächsten Block

        # ==============================================================================
        # BLOCK 2: TRACKING UPDATE (Unabhängig - Bestehende Bestellungen updaten)
        # ==============================================================================
        try:
            # Neue Transaktion für Tracking
            with db_connect(DB_TOCI) as toci_conn:
                self._toci_conn = toci_conn
                
                with db_connect(DB_JTL) as jtl_conn:
                    self._jtl_conn = jtl_conn
            
                    # Step 4: JTL → Tracking Update
                    log_service.log(job_id, "order_workflow", "INFO", "[4/5] JTL → Tracking Update")
                    tracking_result = self._step_4_tracking_to_db(job_id)
                    
                    # Wenn Fehler in Step 4, loggen wir, aber lassen Step 5 ggf. zu (falls Teilupdates möglich)
                    if tracking_result.get('errors', 0) > 0:
                         log_service.log(job_id, "order_workflow", "WARNING", f"⚠ [4/5] {tracking_result.get('errors')} Tracking Fehler")
                    else:
                         log_service.log(job_id, "order_workflow", "INFO", f"✓ [4/5] Tracking Update OK")

                    # Step 5: Tracking → TEMU API
                    log_service.log(job_id, "order_workflow", "INFO", "[5/5] Tracking → TEMU API")
                    if not self._step_5_db_to_api(job_id):
                        log_service.log(job_id, "order_workflow", "WARNING", "⚠ [5/5] API Upload fehlgeschlagen")
                        # Hier kein 'raise', damit DB-Updates aus Step 4 (JTL->DB) trotzdem committet werden!
                    else:
                        log_service.log(job_id, "order_workflow", "INFO", "✓ [5/5] API Upload erfolgreich")

            # HIER COMMIT für Block 2
            
        except Exception as e:
            # Fehler im Tracking-Block gefährdet nicht den Import-Block
            workflow_success = False 
            error_trace = traceback.format_exc()
            log_service.log(job_id, "order_workflow", "ERROR", f"✗ Tracking-Phase fehlgeschlagen: {str(e)}")
        finally:
            self._cleanup_connections()

        # Abschluss
        duration = (datetime.now() - start_time).total_seconds()
        status_msg = "erfolgreich" if workflow_success else "mit Fehlern beendet"
        log_service.log(job_id, "order_workflow", "INFO", f"✓ Workflow {status_msg} ({duration:.1f}s)")
        
        log_service.end_job_capture(success=workflow_success, duration=duration)
        return workflow_success

    def _cleanup_connections(self):
        """Hilfsmethode zum Zurücksetzen der Referenzen"""
        self._toci_conn = None
        self._jtl_conn = None
        self._order_repo = None
        self._item_repo = None
        self._jtl_repo = None
        self._reset_repos_and_services()

    def _reset_repos_and_services(self):
        """Setzt Repo- und Service-Caches zurück, um geschlossene Verbindungen zu vermeiden."""
        self._order_repo = None
        self._item_repo = None
        self._jtl_repo = None
        self._xml_service = None
        self._order_service = None
        self._tracking_service = None

    # --- STEPS (Identisch zum vorherigen Code) ---
    
    def _step_1_api_to_json(self, status: int, days: int, verbose: bool, job_id: str) -> bool:
        try:
            srv = self._get_temu_service(verbose)
            return srv.fetch_orders(parent_order_status=status, days_back=days, job_id=job_id)
        except Exception as e:
            log_service.log(job_id, "api_to_json", "ERROR", f"API Error: {e}")
            return False

    def _step_2_json_to_db(self, job_id: str) -> Dict:
        """Lädt JSONs und importiert sie in die DB (innerhalb der Transaktion)"""
        try:
            # Pfade
            api_response_dir = TEMU_API_RESPONSES_DIR
            orders_file = api_response_dir / 'api_response_orders.json'
            shipping_file = api_response_dir / 'api_response_shipping_all.json'
            amount_file = api_response_dir / 'api_response_amount_all.json'
            
            if not all(f.exists() for f in [orders_file, shipping_file, amount_file]):
                log_service.log(job_id, "json_to_db", "ERROR", "Dateien fehlen")
                return {'imported': 0}

            # Laden
            with open(orders_file, 'r', encoding='utf-8') as f: orders_resp = json.load(f)
            with open(shipping_file, 'r', encoding='utf-8') as f: shipping_resp = json.load(f)
            with open(amount_file, 'r', encoding='utf-8') as f: amount_resp = json.load(f)
            
            orders = orders_resp.get('result', {}).get('pageItems', [])
            
            # Verarbeiten mit INJIZIERTEN Repositories (Shared Connection)
            order_srv = self._get_order_service()
            return order_srv.import_from_api_response(
                orders, shipping_resp, amount_resp,
                order_repo=self._get_order_repo(),
                item_repo=self._get_item_repo(),
                job_id=job_id
            )
        except Exception as e:
            log_service.log(job_id, "json_to_db", "ERROR", f"Import Error: {e}")
            raise # Re-raise für Rollback

    def _step_3_db_to_xml(self, job_id: str) -> Dict:
        try:
            xml_srv = self._get_xml_service()
            # Nutzt automatisch die injizierten Repos aus __init__ (via _get_xml_service)
            return xml_srv.export_to_xml(save_to_disk=True, import_to_jtl=True, job_id=job_id)
        except Exception as e:
            log_service.log(job_id, "db_to_xml", "ERROR", f"XML Error: {e}")
            raise

    def _step_4_tracking_to_db(self, job_id: str) -> Dict:
        try:
            tracking_srv = self._get_tracking_service()
            return tracking_srv.update_tracking_from_jtl(job_id)
        except Exception as e:
            log_service.log(job_id, "tracking_to_db", "ERROR", f"Tracking Update Error: {e}")
            raise

    def _step_5_db_to_api(self, job_id: str) -> bool:
        try:
            order_repo = self._get_order_repo()
            tracking_srv = self._get_tracking_service()
            temu_srv = self._get_temu_service()
            
            orders_data = order_repo.get_orders_for_tracking_export()
            if not orders_data:
                return True
                
            payload = tracking_srv.prepare_tracking_for_api(orders_data, job_id)
            if not payload:
                return True
                
            success, code, msg = temu_srv.upload_tracking(payload, job_id)
            
            if success:
                for o in orders_data:
                    order_repo.update_temu_tracking_status(o['order_id'])
            return success
        except Exception as e:
            log_service.log(job_id, "tracking_to_api", "ERROR", f"Upload Error: {e}")
            return False # Hier kein Raise, damit DB-Updates (Tracking aus JTL) erhalten bleiben

    # --- LAZY LOADERS (Dependency Injection) ---

    def _get_order_repo(self):
        if not self._order_repo:
            self._order_repo = OrderRepository(connection=self._toci_conn)
        return self._order_repo

    def _get_item_repo(self):
        if not self._item_repo:
            self._item_repo = OrderItemRepository(connection=self._toci_conn)
        return self._item_repo

    def _get_jtl_repo(self):
        if not self._jtl_repo and self._jtl_conn:
            self._jtl_repo = JtlRepository(connection=self._jtl_conn)
        return self._jtl_repo

    def _get_temu_service(self, verbose=False):
        if not self._temu_service:
            self._temu_service = TemuMarketplaceService(
                TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT, verbose
            )
        return self._temu_service

    def _get_order_service(self):
        if not self._order_service:
            self._order_service = OrderService(self._get_order_repo(), self._get_item_repo())
        return self._order_service

    def _get_xml_service(self):
        if not self._xml_service:
            self._xml_service = XmlExportService(
                self._get_order_repo(), self._get_item_repo(), self._get_jtl_repo()
            )
        return self._xml_service

    def _get_tracking_service(self):
        if not self._tracking_service:
            self._tracking_service = TrackingService(
                self._get_order_repo(), self._get_jtl_repo()
            )
        return self._tracking_service
