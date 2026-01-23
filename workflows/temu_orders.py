"""TEMU Order Workflow - CLI Wrapper"""

from src.modules.temu.order_workflow_service import OrderWorkflowService


def run_temu_orders(parent_order_status: int = 2, days_back: int = 7, verbose: bool = False) -> bool:
    """
    CLI Wrapper für TEMU Order Sync
    Delegiert an OrderWorkflowService für die eigentliche Logik
    """
    service = OrderWorkflowService()
    return service.run_complete_workflow(
        parent_order_status=parent_order_status,
        days_back=days_back,
        verbose=verbose
    )


# Einzelne Steps für flexible CLI/Testing-Nutzung
def step_1_api_to_json(parent_order_status: int, days_back: int, verbose: bool, job_id: str) -> bool:
    """Wrapper für Step 1 - Hole Orders von TEMU API und speichere als JSON"""
    service = OrderWorkflowService()
    return service._step_1_api_to_json(parent_order_status, days_back, verbose, job_id)


def step_2_json_to_db(job_id: str) -> dict:
    """Wrapper für Step 2 - Importiere JSON Orders in Datenbank"""
    service = OrderWorkflowService()
    return service._step_2_json_to_db(job_id)


def step_3_db_to_xml(job_id: str) -> dict:
    """Wrapper für Step 3 - Exportiere Orders als XML für JTL"""
    service = OrderWorkflowService()
    return service._step_3_db_to_xml(job_id)


def step_4_tracking_to_db(job_id: str) -> dict:
    """Wrapper für Step 4 - Hole Tracking-Daten aus JTL"""
    service = OrderWorkflowService()
    return service._step_4_tracking_to_db(job_id)


def step_5_db_to_api(job_id: str) -> bool:
    """Wrapper für Step 5 - Exportiere Tracking zu TEMU API"""
    service = OrderWorkflowService()
    return service._step_5_db_to_api(job_id)


if __name__ == "__main__":
    run_temu_orders(parent_order_status=2, days_back=7, verbose=False)