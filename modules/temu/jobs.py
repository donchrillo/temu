"""
TEMU Jobs für APScheduler

Registriert TEMU-spezifische Background-Jobs:
- sync_orders: 5-Step Order Workflow
- sync_inventory: 4-Step Inventory Workflow
- fetch_invoices: Invoice Download (future)
"""

from workers.job_models import JobType


def register_jobs(scheduler_service):
    """
    Registriert TEMU-Jobs beim zentralen SchedulerService

    Args:
        scheduler_service: Instance von SchedulerService (workers/worker_service.py)

    Returns:
        List of created job_ids
    """

    job_ids = []

    # Job 1: Order Sync (5-Step Workflow)
    job_id = scheduler_service.add_job(
        job_type=JobType.SYNC_ORDERS,
        interval_minutes=30,  # Default: alle 30 Minuten
        description="TEMU Order Sync - 5-Step Workflow (Fetch, Import, XML, Upload, Tracking)",
        enabled=True
    )
    job_ids.append(job_id)

    # Job 2: Inventory Sync (4-Step Workflow)
    job_id = scheduler_service.add_job(
        job_type=JobType.SYNC_INVENTORY,
        interval_minutes=60,  # Default: alle 60 Minuten
        description="TEMU Inventory Sync - 4-Step Workflow (Download SKUs, Fetch Stock, Compare, Push)",
        enabled=True
    )
    job_ids.append(job_id)

    # Job 3: Invoice Fetch (future implementation)
    job_id = scheduler_service.add_job(
        job_type=JobType.FETCH_INVOICES,
        interval_minutes=1440,  # Default: täglich
        description="TEMU Invoice Download (future implementation)",
        enabled=False  # Disabled bis implementiert
    )
    job_ids.append(job_id)

    return job_ids


def get_job_info():
    """
    Gibt Info über verfügbare TEMU-Jobs zurück

    Returns:
        dict mit Job-Beschreibungen
    """
    return {
        JobType.SYNC_ORDERS: {
            "name": "Order Sync",
            "description": "5-Step Workflow: Fetch → Import → XML → Upload → Tracking",
            "default_interval": 30,
            "steps": [
                "1. Fetch orders from TEMU API",
                "2. Import to database (temu_orders, temu_order_items)",
                "3. Generate XML for JTL",
                "4. Upload XML to JTL (future)",
                "5. Fetch tracking, update orders, report to TEMU"
            ]
        },
        JobType.SYNC_INVENTORY: {
            "name": "Inventory Sync",
            "description": "4-Step Workflow: Download SKUs → Fetch Stock → Compare → Push",
            "default_interval": 60,
            "steps": [
                "1. Download SKU list from TEMU",
                "2. Fetch stock levels from JTL database",
                "3. Compare and mark deltas in temu_inventory",
                "4. Push updates to TEMU API"
            ]
        },
        JobType.FETCH_INVOICES: {
            "name": "Invoice Fetch",
            "description": "Download invoices from TEMU (future implementation)",
            "default_interval": 1440,
            "steps": [
                "1. Fetch invoice list from TEMU API",
                "2. Download PDFs",
                "3. Store in database"
            ]
        }
    }
