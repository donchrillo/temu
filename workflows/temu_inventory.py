"""TEMU Inventory Workflow - CLI Wrapper"""

from src.modules.temu.inventory_workflow_service import InventoryWorkflowService


def run_temu_inventory(mode: str = "quick", verbose: bool = False) -> bool:
    """
    CLI Wrapper für TEMU Inventory Sync
    Delegiert an InventoryWorkflowService für die eigentliche Logik
    
    Args:
        mode: "full" (alle 4 Steps) oder "quick" (nur Steps 3+4, Standard)
        verbose: Detailliertes Logging
    """
    service = InventoryWorkflowService()
    return service.run_complete_workflow(mode=mode, verbose=verbose)


# Einzelne Steps für Rückwärtskompatibilität (Worker nutzt diese)
def step_1_api_to_json(job_id: str, verbose: bool) -> bool:
    """Wrapper für Step 1 - für Worker-Kompatibilität"""
    service = InventoryWorkflowService()
    return service._step_1_api_to_json(job_id, verbose)


def step_2_json_to_db(job_id: str) -> None:
    """Wrapper für Step 2 - für Worker-Kompatibilität"""
    service = InventoryWorkflowService()
    service._step_2_json_to_db(job_id)


def step_3_jtl_stock_to_inventory(job_id: str) -> None:
    """Wrapper für Step 3 - für Worker-Kompatibilität"""
    service = InventoryWorkflowService()
    service._step_3_jtl_stock_to_inventory(job_id)


def step_4_sync_to_temu(job_id: str) -> None:
    """Wrapper für Step 4 - für Worker-Kompatibilität"""
    service = InventoryWorkflowService()
    service._step_4_sync_to_temu(job_id)


if __name__ == "__main__":
    run_temu_inventory(mode="quick", verbose=False)
