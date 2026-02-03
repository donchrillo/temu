# TEMU Module

TEMU Marketplace Integration mit Order & Inventory Synchronisation.

## Features

### Order Sync (5-Step Workflow)
1. ✅ Fetch orders from TEMU API
2. ✅ Import to database (`temu_orders`, `temu_order_items`)
3. ✅ Generate XML for JTL
4. ⏳ Upload XML to JTL (future)
5. ✅ Fetch tracking, update orders, report to TEMU

### Inventory Sync (4-Step Workflow)
1. ✅ Download SKU list from TEMU
2. ✅ Fetch stock levels from JTL database
3. ✅ Compare and mark deltas in `temu_inventory`
4. ✅ Push updates to TEMU API

### Job Scheduling
- ✅ APScheduler Integration (AsyncIO)
- ✅ Configurable intervals
- ✅ Manual triggers via API
- ✅ Enable/Disable jobs
- ✅ Persistent configuration

### UI
- ✅ Modernes, helles Apple-Style Design
- ✅ Responsive (Mobile & Desktop)
- ✅ Live Job-Status-Updates
- ✅ Manual Workflow-Triggers
- ✅ Progress-Bar mit smooth Animation
- ✅ Toast-Notifications

## API Endpoints

### Health & Info
- `GET /health` - Health Check
- `GET /info` - Job-Info und Workflow-Beschreibungen
- `GET /stats` - Statistiken (Orders, Inventory)

### Manual Triggers
- `POST /orders/sync` - Trigger Order Sync Workflow
  - Query Params: `parent_order_status`, `days_back`, `verbose`
- `POST /inventory/sync` - Trigger Inventory Sync Workflow
  - Query Params: `mode` (quick/full), `verbose`

## Jobs

Jobs werden über das zentrale SchedulerService verwaltet:
- **GET /api/jobs** - Liste aller Jobs
- **POST /api/jobs/{job_id}/run-now** - Job manuell starten
- **POST /api/jobs/{job_id}/schedule** - Intervall ändern
- **POST /api/jobs/{job_id}/toggle** - Job enable/disable

## Verwendung

### Im Gateway (main.py)
```python
from modules.temu import get_router, register_jobs

# Router einbinden
app.include_router(
    get_router(),
    prefix="/api/temu",
    tags=["TEMU"]
)

# Jobs registrieren (beim SchedulerService)
from workers.worker_service import SchedulerService
scheduler = SchedulerService()
from modules.temu import register_jobs
register_jobs(scheduler)
```

### Frontend
Das Frontend liegt in `modules/temu/frontend/`:
- `temu.html` - Dashboard UI
- `temu.css` - Apple-Style CSS
- `temu.js` - Funktionalität (Jobs, Triggers, Progress)

Frontend wird über das Gateway bedient:
- HTML: `/temu-new` → `modules/temu/frontend/temu.html`
- Assets: `/static/temu.css`, `/static/temu.js`

## Workflows

### Order Sync Workflow
```
src/modules/temu/order_workflow_service.py
↓
1. fetch_orders() → data/temu/api_responses/
2. import_orders() → temu_orders, temu_order_items
3. generate_xml() → data/temu/xml/
4. upload_to_jtl() → (future)
5. sync_tracking() → JTL → TEMU API
```

### Inventory Sync Workflow
```
src/modules/temu/inventory_workflow_service.py
↓
1. download_skus() → TEMU API
2. fetch_stock() → JTL database (eazybusiness)
3. compare_and_mark() → temu_inventory (needs_sync flag)
4. push_to_temu() → TEMU API
```

## Business Logic (bestehende Services)

Die Business Logic bleibt in `src/modules/temu/`:
- `order_service.py` - Order Import
- `order_workflow_service.py` - 5-Step Workflow
- `inventory_service.py` - Inventory Sync
- `inventory_workflow_service.py` - 4-Step Workflow
- `stock_sync_service.py` - Stock Level Sync
- `tracking_service.py` - Tracking Updates

Das Modul ist ein **Wrapper** - keine Änderungen an der bestehenden Logik!

## Design

**Apple-Style UI:**
- Helle Farben (#F2F2F7 Background)
- San Francisco Font
- Status-Cards mit Icons
- Trigger-Cards für manuelle Workflows
- Jobs-Liste mit Live-Updates
- Logs mit Filter
- Smooth Progress-Bar

## Job Configuration

Jobs werden in `workers/config/workers_config.json` gespeichert:
```json
[
    {
        "job_type": "sync_orders",
        "interval_minutes": 30,
        "enabled": true,
        "description": "TEMU Order Sync - 5-Step Workflow"
    },
    {
        "job_type": "sync_inventory",
        "interval_minutes": 60,
        "enabled": true,
        "description": "TEMU Inventory Sync - 4-Step Workflow"
    }
]
```

## Dependencies

Benötigt:
- `modules/shared` (Database, Logging, Config)
- `src/modules/temu` (Business Logic)
- `src/marketplace_connectors/temu` (API Client)
- `workers/worker_service` (APScheduler)

## Version

1.0.0 - Initial Release
