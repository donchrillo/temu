"""
TEMU Module

TEMU Marketplace Integration:
- Order Sync (5-Step Workflow)
- Inventory Sync (4-Step Workflow)
- Tracking Updates
- APScheduler Jobs
- WebSocket Live-Updates

Module-Struktur:
- router.py: FastAPI Endpoints (Jobs, Manual Triggers)
- jobs.py: Job Registration für APScheduler
- workflows/: Business Logic (re-export von src/modules/temu/)
- frontend/: Dashboard UI (Apple Style)
"""

from .router import router, get_router
from .jobs import register_jobs

__all__ = ["router", "get_router", "register_jobs"]
__version__ = "1.0.0"
