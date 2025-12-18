import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT
from src.services.log_service import log_service
from src.db.connection import get_db_connection
from src.db.repositories.product_repository import ProductRepository
from src.db.repositories.inventory_repository import InventoryRepository
from src.marketplace_connectors.temu.service import TemuMarketplaceService
from src.modules.inventory.inventory_service import InventoryService
from src.modules.inventory.stock_sync_service import StockSyncService


def run_temu_inventory(verbose: bool = False) -> bool:
    start_time = datetime.now()
    job_id = f"temu_inventory_{int(start_time.timestamp())}"
    log_service.start_job_capture(job_id, "temu_inventory")
    try:
        # [1/4] TEMU API -> JSON (Platzhalter)
        if not _step_1_api_to_json(job_id, verbose):
            raise Exception("API Fetch fehlgeschlagen")

        # [2/4] JSON -> DB (temu_products)
        _step_2_json_to_db(job_id)

        # [3/4] JTL → temu_inventory (Initial/Delta)
        _step_3_jtl_stock_to_inventory(job_id)

        # [4/4] temu_inventory → TEMU API (nur Deltas)
        _step_4_sync_to_temu(job_id)

        duration = (datetime.now() - start_time).total_seconds()
        log_service.end_job_capture(success=True, duration=duration)
        return True
    except Exception as e:
        import traceback
        duration = (datetime.now() - start_time).total_seconds()
        log_service.log(job_id, "temu_inventory", "ERROR", f"{e}\n{traceback.format_exc()}")
        log_service.end_job_capture(success=False, duration=duration, error=str(e))
        return False


def _step_1_api_to_json(job_id: str, verbose: bool) -> bool:
    temu_service = TemuMarketplaceService(
        app_key=TEMU_APP_KEY,
        app_secret=TEMU_APP_SECRET,
        access_token=TEMU_ACCESS_TOKEN,
        endpoint=TEMU_API_ENDPOINT,
        verbose=verbose
    )
    log_service.log(job_id, "api_to_json", "INFO", "→ Hole TEMU SKU-Liste (Status 2 & 3, pageSize=100)")
    inv_service = InventoryService()
    return inv_service.fetch_and_store_raw_skus(temu_service.inventory_api, job_id=job_id)


def _step_2_json_to_db(job_id: str) -> None:
    toci_conn = get_db_connection(database="toci", use_pool=True)
    product_repo = ProductRepository(connection=toci_conn)
    inv_service = InventoryService()
    log_service.log(job_id, "json_to_db", "INFO", "→ Importiere SKU-JSON in temu_products")
    stats = inv_service.import_products_from_raw(product_repo, job_id=job_id)
    log_service.log(job_id, "json_to_db", "INFO", f"✓ Produkte importiert: {stats}")


def _step_3_jtl_stock_to_inventory(job_id: str) -> None:
    toci_conn = get_db_connection(database="toci", use_pool=True)
    jtl_conn = get_db_connection(database="eazybusiness", use_pool=True)
    product_repo = ProductRepository(connection=toci_conn)
    inventory_repo = InventoryRepository(connection=toci_conn)
    inv_service = InventoryService()
    log_service.log(job_id, "jtl_to_inventory", "INFO", "→ Lese JTL Bestände und aktualisiere temu_inventory")
    stats = inv_service.refresh_inventory_from_jtl(product_repo, inventory_repo, job_id=job_id)
    log_service.log(job_id, "jtl_to_inventory", "INFO", f"✓ Bestand aktualisiert: {stats}")


def _step_4_sync_to_temu(job_id: str) -> None:
    toci_conn = get_db_connection(database="toci", use_pool=True)
    inventory_repo = InventoryRepository(connection=toci_conn)
    temu_service = TemuMarketplaceService(
        app_key=TEMU_APP_KEY,
        app_secret=TEMU_APP_SECRET,
        access_token=TEMU_ACCESS_TOKEN,
        endpoint=TEMU_API_ENDPOINT
    )
    log_service.log(job_id, "inventory_to_api", "INFO", "→ Sende Delta-Bestände an TEMU")
    sync_service = StockSyncService()
    sync_service.sync_deltas_to_temu(temu_service.inventory_api, inventory_repo, job_id=job_id)
    log_service.log(job_id, "inventory_to_api", "INFO", "✓ Delta-Upload abgeschlossen")


if __name__ == "__main__":
    run_temu_inventory(verbose=False)
