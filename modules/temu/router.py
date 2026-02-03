"""
TEMU API Router

REST API Endpoints für TEMU Integration:
- Job Management (List, Trigger, Schedule, Toggle)
- Manual Workflow Triggers (Orders, Inventory)
- Status & Info
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime

from modules.shared import log_service, app_logger
from .jobs import get_job_info

# Router erstellen
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# HEALTH & STATUS
# ═══════════════════════════════════════════════════════════════

@router.get("/health")
async def health_check():
    """Health Check für TEMU Modul"""
    return {
        "status": "healthy",
        "module": "temu",
        "version": "1.0.0",
        "workflows": {
            "orders": "5-Step (Fetch → Import → XML → Upload → Tracking)",
            "inventory": "4-Step (Download SKUs → Fetch Stock → Compare → Push)"
        }
    }

@router.get("/info")
async def get_info():
    """Info über TEMU-Jobs und Workflows"""
    return {
        "module": "TEMU Integration",
        "version": "1.0.0",
        "jobs": get_job_info()
    }

# ═══════════════════════════════════════════════════════════════
# JOB MANAGEMENT (delegiert an SchedulerService)
# ═══════════════════════════════════════════════════════════════

# HINWEIS: Die eigentlichen Job-Endpoints sind im Gateway unter /api/jobs
# Hier dokumentieren wir nur die TEMU-spezifischen Trigger

@router.post("/orders/sync")
async def trigger_order_sync(
    parent_order_status: int = 2,
    days_back: int = 7,
    verbose: bool = False
):
    """
    Manueller Trigger: Order Sync Workflow

    5-Step Workflow:
    1. Fetch orders from TEMU API
    2. Import to database
    3. Generate XML for JTL
    4. Upload XML to JTL (future)
    5. Fetch tracking, update orders, report to TEMU

    Query Params:
    - parent_order_status: TEMU order status filter (default: 2 = shipped)
    - days_back: How many days to look back (default: 7)
    - verbose: Detailed logging (default: false)
    """
    # Diese Funktion wird vom Gateway aufgerufen
    # Das Gateway holt sich den SchedulerService und triggert den Job
    # Hier nur Dokumentation und Validierung

    if parent_order_status not in [0, 1, 2, 3, 4, 5]:
        raise HTTPException(
            status_code=400,
            detail="Invalid parent_order_status. Must be 0-5"
        )

    if days_back < 1 or days_back > 90:
        raise HTTPException(
            status_code=400,
            detail="days_back must be between 1 and 90"
        )

    return {
        "status": "triggered",
        "workflow": "order_sync",
        "params": {
            "parent_order_status": parent_order_status,
            "days_back": days_back,
            "verbose": verbose
        },
        "message": "Order Sync Workflow wurde gestartet. Siehe /api/jobs für Status."
    }

@router.post("/inventory/sync")
async def trigger_inventory_sync(
    mode: str = "quick",
    verbose: bool = False
):
    """
    Manueller Trigger: Inventory Sync Workflow

    4-Step Workflow:
    1. Download SKU list from TEMU
    2. Fetch stock levels from JTL database
    3. Compare and mark deltas
    4. Push updates to TEMU API

    Query Params:
    - mode: "quick" (nur deltas) or "full" (alle SKUs) (default: quick)
    - verbose: Detailed logging (default: false)
    """
    if mode not in ["quick", "full"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid mode. Must be 'quick' or 'full'"
        )

    return {
        "status": "triggered",
        "workflow": "inventory_sync",
        "params": {
            "mode": mode,
            "verbose": verbose
        },
        "message": "Inventory Sync Workflow wurde gestartet. Siehe /api/jobs für Status."
    }

# ═══════════════════════════════════════════════════════════════
# STATISTICS & MONITORING
# ═══════════════════════════════════════════════════════════════

@router.get("/stats")
async def get_stats():
    """
    Statistiken über TEMU Integration

    TODO: Implement actual statistics from database
    """
    # TODO: Query database for real stats
    return {
        "orders": {
            "total": 0,
            "imported": 0,
            "xml_generated": 0,
            "uploaded": 0,
            "tracked": 0
        },
        "inventory": {
            "total_skus": 0,
            "synced": 0,
            "pending": 0,
            "errors": 0
        },
        "last_sync": {
            "orders": None,
            "inventory": None
        }
    }

# ═══════════════════════════════════════════════════════════════
# EXPORT FUNCTION (für Gateway Integration)
# ═══════════════════════════════════════════════════════════════

def get_router() -> APIRouter:
    """Wird vom Gateway aufgerufen"""
    return router
