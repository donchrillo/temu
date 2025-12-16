"""TEMU Order Sync Workflow - kompletter 5-Schritt Prozess (immer mit Logging)"""

from datetime import datetime
from typing import Dict

from config.settings import (
    TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT
)
from src.marketplace_connectors.temu.service import TemuMarketplaceService
from src.db.connection import get_db_connection
from src.db.repositories.order_repository import OrderRepository
from src.db.repositories.order_item_repository import OrderItemRepository
from src.db.repositories.jtl_repository import JtlRepository
from src.modules.orders.order_service import OrderService
from src.modules.xml_export.xml_export_service import XmlExportService
from src.modules.tracking.tracking_service import TrackingService
from src.services.log_service import log_service



def run_temu_orders(parent_order_status: int = 2, days_back: int = 7, verbose: bool = False) -> bool:
    """
    TEMU Order Sync - kompletter 5-Schritt Prozess
    Immer vollständiges Logging (DB + Logger).
    """
    start_time = datetime.now()
    job_id = f"temu_orders_{int(start_time.timestamp())}"

    valid_status = [2, 3, 4, 5]
    if parent_order_status not in valid_status:
        log_service.log(job_id, "temu_orders""ERROR", f"Ungültiger Status: {parent_order_status}")
        return False
    if days_back < 1:
        log_service.log(job_id, "temu_orders", "ERROR", "Days muss >= 1 sein")
        return False

    log_service.start_job_capture(job_id, "temu_orders")
    log_service.log(job_id, "temu_orders","INFO", f"→ Start TEMU  Order Sync (Status: {parent_order_status}, Tage: {days_back})")

    try:
        log_service.log(job_id,"temu_orders", "INFO", "[1/6] TEMU chx API → JSON")
        if not _step_1_api_to_json(parent_order_status, days_back, verbose, job_id):
            raise Exception("API Fetch fehlgeschlagen")
        log_service.log(job_id, "temu_orders", "INFO", "✓ [1/6] API → JSON erfolgreich")

        log_service.log(job_id, "temu_orders", "INFO", "[2/6] JSON → Datenbank")
        result = _step_2_json_to_db(job_id)
        log_service.log(job_id, "temu_orders", "INFO", f"✓ [2/6] JSON → DB: {result.get('imported', 0)} neu, {result.get('updated', 0)} aktualisiert")

        log_service.log(job_id, "temu_orders", "INFO", "[3/6] Datenbank → XML Export")
        xml_result = _step_3_db_to_xml(job_id)
        if xml_result.get('success'):
            log_service.log(job_id, "temu_orders", "INFO", f"✓ [3/6] DB → XML: {xml_result.get('exported', 0)} exportiert")
        else:
            log_service.log(job_id, "temu_orders", "INFO", f"✓ [3/6] DB → XML: {xml_result.get('message', 'Keine Orders')}")

        log_service.log(job_id, "temu_orders", "INFO", "[4/6] JTL → Tracking Update")
        tracking_result = _step_4_tracking_to_db(job_id)
        log_service.log(job_id, "temu_orders", "INFO", f"✓ [4/6] JTL → Tracking: {tracking_result.get('updated', 0)} aktualisiert")

        log_service.log(job_id, "temu_orders", "INFO", "[5/6] Tracking → TEMU API")
        if not _step_5_db_to_api(job_id):
            log_service.log(job_id, "temu_orders", "WARNING", "⚠ [5/6] Tracking Export fehlgeschlagen")
        else:
            log_service.log(job_id, "temu_orders", "INFO", "✓ [5/6] Tracking → API erfolgreich")  
        duration = (datetime.now() - start_time).total_seconds()
        log_service.log(job_id, "temu_orders", "INFO", f"✓ TEMU Order Sync erfolgreich ({duration:.1f}s)")
        log_service.end_job_capture(success=True, duration=duration)
        return True

    except Exception as e:
        import traceback
        duration = (datetime.now() - start_time).total_seconds()
        error_trace = traceback.format_exc()
        log_service.log(job_id, "temu_orders", "ERROR", f"✗ TEMU Order Sync fehlgeschlagen: {str(e)}\n{error_trace}")
        log_service.end_job_capture(success=False, duration=duration, error=str(e))
        return False


def _step_1_api_to_json(parent_order_status: int, days_back: int, verbose: bool, job_id: str) -> bool:
    try:
        log_service.log(job_id, "api_to_json", "INFO",
                        f"→ Hole TEMU Orders (Status: {parent_order_status}, Tage: {days_back})")
        # log_service.log(job_id, "api_to_json", "INFO",
        #                f"→ Hole TEMU Orders (Status CHX: {parent_order_status}, Tage: {days_back})")        
        temu_service = TemuMarketplaceService(
            app_key=TEMU_APP_KEY,
            app_secret=TEMU_APP_SECRET,
            access_token=TEMU_ACCESS_TOKEN,
            endpoint=TEMU_API_ENDPOINT,
            verbose=verbose
        )
        result = temu_service.fetch_orders(parent_order_status=parent_order_status, days_back=days_back, job_id=job_id)
        if result:
            log_service.log(job_id, "api_to_json", "INFO", "✓ API Orders erfolgreich heruntergeladen und gespeichert")
            return True
        log_service.log(job_id, "api_to_json", "WARNING", "⚠ API Abruf fehlgeschlagen oder keine neuen Orders")
        return False
    except Exception as e:
        import traceback
        log_service.log(job_id, "api_to_json", "ERROR", f"✗ API Abruf Fehler: {str(e)}\n{traceback.format_exc()}")
        return False


def _step_2_json_to_db(job_id: str) -> Dict:
    try:
        log_service.log(job_id, "json_to_db", "INFO", "→ Importiere Orders aus JSON in Datenbank")
        toci_conn = get_db_connection(database='toci', use_pool=True)
        order_repo = OrderRepository(connection=toci_conn)
        item_repo = OrderItemRepository(connection=toci_conn)
        order_service = OrderService(order_repo, item_repo)
        result = order_service.import_from_json_files(job_id=job_id)
        log_service.log(job_id, "json_to_db", "INFO",
                        f"✓ Import abgeschlossen: {result.get('total', 0)} Orders "
                        f"(Neu: {result.get('imported', 0)}, Aktualisiert: {result.get('updated', 0)})")
        return result
    except Exception as e:
        import traceback
        log_service.log(job_id, "json_to_db", "ERROR", f"✗ JSON Import Fehler: {str(e)}\n{traceback.format_exc()}")
        return {'imported': 0, 'updated': 0}


def _step_3_db_to_xml(job_id: str) -> Dict:
    try:
        log_service.log(job_id, "db_to_xml", "INFO", "→ Exportiere Orders als XML für JTL")
        toci_conn = get_db_connection(database='toci', use_pool=True)
        order_repo = OrderRepository(connection=toci_conn)
        item_repo = OrderItemRepository(connection=toci_conn)

        jtl_repo = None
        try:
            jtl_conn = get_db_connection(database='eazybusiness', use_pool=True)
            jtl_repo = JtlRepository(connection=jtl_conn)
            log_service.log(job_id, "db_to_xml", "INFO", "  ✓ JTL Verbindung erfolgreich")
        except Exception as e:
            log_service.log(job_id, "db_to_xml", "WARNING", f"  ⚠ JTL Verbindung fehlgeschlagen: {e}")

        service = XmlExportService(order_repo=order_repo, item_repo=item_repo, jtl_repo=jtl_repo)
        result = service.export_to_xml(save_to_disk=True, import_to_jtl=jtl_repo is not None, job_id=job_id)
        if result.get('success'):
            log_service.log(job_id, "db_to_xml", "INFO", "✓ XML Export erfolgreich")
        else:
            log_service.log(job_id, "db_to_xml", "INFO", f"✓ XML Export: {result.get('message', 'Keine Orders')}")
        return result
    except Exception as e:
        import traceback
        log_service.log(job_id, "db_to_xml", "ERROR", f"✗ XML Export Fehler: {str(e)}\n{traceback.format_exc()}")
        return {'success': False, 'message': str(e)}


def _step_4_tracking_to_db(job_id: str) -> Dict:
    try:
        log_service.log(job_id, "tracking_to_db", "INFO", "→ Hole Tracking-Daten aus JTL")
        toci_conn = get_db_connection(database='toci', use_pool=True)
        jtl_conn = get_db_connection(database='eazybusiness', use_pool=True)
        order_repo = OrderRepository(connection=toci_conn)
        jtl_repo = JtlRepository(connection=jtl_conn)
        tracking_service = TrackingService(order_repo=order_repo, jtl_repo=jtl_repo)
        result = tracking_service.update_tracking_from_jtl()
        log_service.log(job_id, "tracking_to_db", "INFO",
                        f"✓ Tracking-Update abgeschlossen (Aktualisiert: {result.get('updated', 0)}, "
                        f"Fehler: {result.get('errors', 0)})")
        return result
    except Exception as e:
        import traceback
        log_service.log(job_id, "tracking_to_db", "ERROR", f"✗ Tracking Update Fehler: {str(e)}\n{traceback.format_exc()}")
        return {'updated': 0, 'errors': 0}


def _step_5_db_to_api(job_id: str) -> bool:
    try:
        log_service.log(job_id, "tracking_to_api", "INFO", "→ Exportiere Tracking zu TEMU API")
        if not all([TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN]):
            log_service.log(job_id, "tracking_to_api", "ERROR", "✗ TEMU Credentials nicht gesetzt!")
            return False

        toci_conn = get_db_connection(database='toci', use_pool=True)
        order_repo = OrderRepository(connection=toci_conn)
        tracking_service = TrackingService(order_repo=order_repo)
        temu_service = TemuMarketplaceService(
            app_key=TEMU_APP_KEY,
            app_secret=TEMU_APP_SECRET,
            access_token=TEMU_ACCESS_TOKEN,
            endpoint=TEMU_API_ENDPOINT
        )

        log_service.log(job_id, "tracking_to_api", "INFO", "  → Hole Orders mit Tracking...")
        orders_data = order_repo.get_orders_for_tracking_export()
        if not orders_data:
            log_service.log(job_id, "tracking_to_api", "INFO", "  ✓ Keine Bestellungen zum Exportieren")
            return True

        log_service.log(job_id, "tracking_to_api", "INFO", f"  ✓ {len(orders_data)} Bestellungen mit Tracking")
        log_service.log(job_id, "tracking_to_api", "INFO", "  → Konvertiere zu API Format...")
        tracking_data_for_api = tracking_service.prepare_tracking_for_api(orders_data)
        if not tracking_data_for_api:
            log_service.log(job_id, "tracking_to_api", "INFO", "  ✓ Keine Tracking-Daten zum Upload")
            return True

        log_service.log(job_id, "tracking_to_api", "INFO", f"  ✓ {len(tracking_data_for_api)} Positionen zum Upload")
        log_service.log(job_id, "tracking_to_api", "INFO", "  → Lade zu TEMU API hoch...")
        success, error_code, error_msg = temu_service.upload_tracking(tracking_data_for_api)

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
        log_service.log(job_id, "tracking_to_api", "ERROR", f"✗ Tracking Export Fehler: {str(e)}\n{traceback.format_exc()}")
        return False




if __name__ == "__main__":
    run_temu_orders(parent_order_status=2, days_back=7, verbose=False)