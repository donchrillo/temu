# Code Structure – Projektarchitektur & Modul-Overview

Quick Reference für die TEMU-Integration Codebase.

---

**Datum:** 5. Februar 2026

---

## 1. Projektbaum

```
/home/chx/temu/
├── .venv/                         # Python Virtual Environment
├── data/                          # Runtime Data (JSON, XML, PDFs)
│   ├── csv_verarbeiter/
│   │   ├── eingang/
│   │   ├── ausgang/
│   │   └── reports/
│   ├── pdf_reader/
│   │   ├── eingang/{rechnungen,werbung}
│   │   ├── ausgang/
│   │   └── tmp/
│   └── temu/
│       ├── api_responses/
│       ├── xml/
│       └── export/
├── docs/                          # Project Documentation
├── frontend/                      # Main PWA Frontend
│   ├── dashboard.css
│   ├── index-new.html             # Main HTML (PWA Entry)
│   ├── manifest.json
│   ├── service-worker.js
│   └── icons/
├── logs/                          # Runtime Logs by Module
│   ├── app/
│   ├── csv_verarbeiter/
│   └── pdf_reader/
├── modules/                       # ALL application modules (monorepo)
│   ├── shared/                    # Common Infrastructure
│   │   ├── config/                # Settings, .env file
│   │   ├── connectors/temu/       # TEMU API Client
│   │   ├── database/              # Connection, Repositories (TOCI + JTL)
│   │   └── logging/               # Log Service, Logger Factory
│   ├── temu/                      # TEMU Marketplace Integration
│   │   ├── frontend/              # PWA Interface
│   │   ├── services/              # Business Logic (Orders, Inventory, Tracking)
│   │   ├── jobs.py                # APScheduler Job Definitions
│   │   └── router.py              # FastAPI Routes
│   ├── pdf_reader/                # PDF Processing Module
│   │   ├── frontend/              # Upload Interface
│   │   ├── services/              # PDF Extraction Logic
│   │   └── router.py              # FastAPI Routes
│   ├── jtl/                       # JTL ERP Integration
│   │   └── xml_export/            # XML Generation Service
│   └── csv_verarbeiter/           # CSV Processing (JTL2DATEV) [🔄 In Dev]
│       ├── frontend/              # Light Apple-design UI
│       ├── services/              # CSV Processing Logic
│       └── router.py              # FastAPI Routes
├── workers/                       # APScheduler Job Management
│   ├── config/
│   │   └── workers_config.json    # Schedule + Intervals
│   ├── job_models.py
│   ├── worker_service.py
│   └── workers_config.py
├── scripts/                       # Shell scripts (e.g., setup, export)
├── .gitignore
├── CLAUDE.md
├── db_schema.sql
├── ecosystem.config.js            # PM2 Configuration
├── main.py                        # Unified FastAPI Gateway
├── MIGRATION_STATUS.md
└── requirements.txt
```

---

## 2. Kern-Module (Verantwortlichkeiten)

### API Layer – `main.py`
**Verantwortung:** HTTP/WebSocket Schnittstelle

```python
# Endpoints:
GET /api/health              # Health Check
GET /api/jobs/status         # All Jobs Status
GET /api/jobs/<job_id>       # Specific Job Details
POST /api/jobs/<job_id>/execute # Trigger Job
WebSocket /ws/logs           # Live Job Updates
GET /icons/{filename}        # Icon-Serving
```

**Features:**
- FastAPI (async, ASGI)
- Pydantic für Request/Response Validation
- WebSocket für Live-Updates (JSON messages)
- Error Handling mit HTTP Status Codes
- CORS + Security Headers

---

### Database Layer – `modules/shared/database/`

#### `connection.py`
**Verantwortung:** SQLAlchemy Engine + Connection Pool

```python
# Config:
- Driver: ODBC Driver 18 for SQL Server
- Pool Size: 10 (base connections)
- Max Overflow: 20 (zusätzliche bei Spikes)
- Pool Pre-Ping: True (self-healing)
- Pool Recycle: 3600s (Connections erneuern)

# Exports:
- get_engine(db_name) → Engine
- db_connect(db_name) → Context Manager
```

**Patterns:**
```python
# Transactional (mit auto-rollback):
with db_connect(DB_TOCI) as conn:
    repo.insert(conn, data)  # Wenn Error → ROLLBACK
    # conn committed automatically

# Standalone:
repo = ProductRepository()  # Erstellt interne Connection
repo.update(data)          # Auto-commit
```

#### `repositories/`
**Verantwortung:** CRUD Operations pro Tabelle

**Repositories:**
- `temu/product_repository.py` – temu_products (Insert, Update, Get)
- `temu/inventory_repository.py` – temu_inventory (Stock Tracking)
- `temu/order_repository.py` – temu_orders (Order CRUD)
- `temu/order_item_repository.py` – temu_order_items (Line Items)
- `jtl_common/jtl_repository.py` – JTL Lookups (tArtikel, vLagerbestandProLager)
- `common/log_repository.py` – Logging

**Interface:**
```python
class Repository:
    def __init__(self, connection=None):
        # Optional connection injection für Transaktionen
        pass
    
    def insert(self, data): ...
    def update(self, id, data): ...
    def delete(self, id): ...
    def get_by_id(self, id): ...
    def get_all(self): ...
```

---

### Marketplace Connector – `modules/shared/connectors/temu/`

**Verantwortung:** TEMU API Kommunikation

#### `api_client.py` – Low-Level
```python
class TemuApiClient:
    - _sign_request(method, path, params) → Signed URL
    - get(path, params) → JSON Response
    - post(path, body) → JSON Response
```

**Nur für:** Raw HTTP + Request Signing (SHA256 HMAC)

#### `orders_api.py` – Orders Endpoint
```python
class TemuOrdersApi:
    fetch_orders() → List[Order]           # API: getOrderList
    fetch_shipping(order_ids) → Dict       # API: getShippingList
    fetch_amounts(order_ids) → Dict        # API: getShippingList (amounts)
    update_tracking(order_id, tracking)    # API: updateOrderDelivery
```

#### `inventory_api.py` – Inventory Endpoint
```python
class TemuInventoryApi:
    fetch_skus(status) → List[SKU]         # API: getGoodsList (Status 2 & 3)
    update_stock(goods_id, quantity)       # API: updateStockTarget
```

#### `service.py` – High-Level
```python
class TemuService:
    # Combines all APIs
    get_orders_with_shipping_and_amounts()
    get_skus_by_status(status_2, status_3)
    push_stock_updates(updates)
```

---

### Business Logic – `modules/temu/services/`

**Verantwortung:** Domain Logic (Orders, Inventory, Tracking, Stock Sync)

#### `order_service.py` – Order Import
```python
class OrderService:
    import_orders_from_json(json_data) → Inserted Orders
    
    Steps:
    1. Parse JSON
    2. Deduplicate by order_id
    3. Insert into DB (transactional)
    4. Return Count
```

#### `inventory_service.py` – Inventory Management
```python
class InventoryService:
    fetch_and_store_raw_skus(status_list) → Stored SKUs
  # Holt SKUs von TEMU API, speichert in data/temu/api_responses/
    
    import_skus_from_json(json_data) → Imported Count
    # Parst JSON, speichert in temu_products DB
    
    refresh_inventory_from_jtl() → Inventory Dict
    # Holt Stock von JTL, speichert in temu_inventory DB
    # Kalkuliert: available_stock = max(0, fBestand - nPuffer)
```

#### `tracking_service.py` – Tracking Management
```python
class TrackingService:
    sync_tracking_from_jtl(order_ids) → Synced Count
    
    Steps:
    1. Find Orders without Tracking in DB
    2. Lookup Order ID in JTL (lvLieferschein)
    3. Get Tracking Number + Carrier
    4. Map Carrier to TEMU Carrier ID
    5. Store in temu_orders.tracking_number
    
    Carrier Mapping:
    - "Hermes" → 1
    - "DPD" → 2
    - "UPS" → 3
    etc.
```

#### `stock_sync_service.py` – Stock Delta Sync
```python
class StockSyncService:
    sync_stock_deltas() → Synced Count
    
    Steps:
    1. Get all temu_inventory where needs_sync=1
    2. Group by goods_id
    3. For each group: Call TEMU API updateStockTarget
    4. Mark synced_at, needs_sync=0
    5. Log errors (missing ID, API fail)
    
    Error Handling:
    - Skip if goods_id NULL
    - Skip if sku_id NULL
    - Log API errors, don't crash
```

---

### Workflow Orchestration – `modules/temu/services/`

**Verantwortung:** Multi-Step Job Orchestrierung mit DI (Dependency Injection)

#### `order_workflow_service.py` – 5-Step Order Sync
```
Step 1: API→JSON
  - Fetch Orders + Shipping + Amounts from TEMU
  - Save as JSON files in data/temu/api_responses/

Step 2: JSON→DB
  - Parse JSON
  - Import Orders + Items into temu_orders

Step 3: DB→XML
  - Export Orders as XML (for JTL import)
  - Save to data/temu/xml/jtl_temu_bestellungen.xml

Step 4: JTL→Tracking
  - Lookup Tracking numbers in JTL
  - Store in temu_orders.tracking_number

Step 5: Tracking→API
  - Upload Tracking to TEMU
  - Update Order Status

Architecture:
- DI: Services injiziert (TemuService, Repos, JTL Repo)
- Lazy Loading: Connections erst bei Bedarf
- Error Handling: Catch + Log, nicht crash
- Transactional: Context Manager für multi-step safety
```

**Praktisches Example:**
```python
@dataclass
class OrderWorkflowService:
    temu_service: TemuService
    order_repo: OrderRepository
    order_item_repo: OrderItemRepository
    jtl_repo: Optional[JltRepository]
    tracking_service: TrackingService
    
    def execute(self, mode: str = "full") -> WorkflowResult:
        # mode = "full" (all 5) oder "tracking_only" (nur 4+5)
        result = WorkflowResult()
        
        try:
            # Step 1+2: API→JSON→DB
            orders = self.temu_service.get_orders_with_shipping_and_amounts()
            self.order_repo.import_orders(orders)
            result.orders_imported = len(orders)
            
            # Step 3: DB→XML (optional)
            self.export_orders_to_xml()
            
            # Step 4: JTL→Tracking
            if self.jtl_repo:
                synced = self.tracking_service.sync_tracking_from_jtl(
                    [o.order_id for o in orders]
                )
                result.tracking_synced = synced
            
            # Step 5: Tracking→API
            synced = self.push_tracking_to_temu()
            result.tracking_pushed = synced
            
            result.status = "success"
        except Exception as e:
            result.status = "failed"
            result.error = str(e)
        
        return result
```

#### `inventory_workflow_service.py` – 4-Step Inventory Sync
```
Step 1: API→JSON
  - Fetch SKU Lists (Status 2 & 3) from TEMU
  - Save as JSON

Step 2: JSON→DB
  - Import SKUs into temu_products

Step 3: JTL→Inventory
  - Fetch Stock from JTL (vLagerbestandProLager)
  - Calculate: available = max(0, fBestand - nPuffer)
  - Store in temu_inventory

Step 4: Inventory→API
  - Get Deltas (needs_sync=1)
  - Push to TEMU updateStockTarget

Modes:
- "full": All 4 steps
- "quick": Skip steps 1+2, only refresh from JTL (3+4)

DI Pattern: Wie OrderWorkflow
```

---

### Services – `modules/shared/logging/`

#### `log_service.py` – Centralized Logging
```python
class LogService:
    log_job(job_id, job_type, level, message, status=None)
    get_job_logs(job_id, limit=50)
    get_job_stats(job_id)  # success rate, duration avg
```

Speichert in `dbo.scheduler_logs` (SQL Server).

---

### Scheduler & Jobs – `workers/`

#### `worker_service.py` – Job Execution
```python
class WorkerService:
    schedule_jobs(config)          # APScheduler Setup
    execute_job(job_id)            # Run specific job
    
    Jobs:
    - temu_orders_sync → OrderWorkflowService.execute()
    - temu_inventory_sync → InventoryWorkflowService.execute()
    - fetch_invoices → Placeholder
```

**APScheduler Integration:**
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=execute_job,
    args=("temu_orders_sync",),
    trigger="cron",
    hour=9, minute=0,  # 09:00 täglich
    timezone="Europe/Berlin",
    id="temu_orders_sync"
)
scheduler.start()
```

#### `workers_config.json` – Configuration
```json
{
  "jobs": {
    "temu_orders_sync": {
      "enabled": true,
      "schedule": "0 9 * * *",     // 09:00 täglich
      "timeout_seconds": 300,
      "max_retries": 3,
      "retry_delay_seconds": 30
    },
    "temu_inventory_sync": {
      "enabled": true,
      "schedule": "*/30 * * * *",   // Alle 30 Minuten
      "timeout_seconds": 60
    }
  }
}
```

---

## 3. Data Flow Diagramme

### Order Workflow (5 Steps)
```
TEMU API
   ↓
[Step 1] fetch_orders_with_shipping_and_amounts()
   ↓ JSON Files
   ↓
[Step 2] import_orders_from_json()
   ↓ DB (temu_orders, temu_order_items)
   ↓
[Step 3] export_orders_to_xml() [Optional]
   ↓ XML File (data/jtl_temu_bestellungen.xml)
   ↓
[Step 4] sync_tracking_from_jtl()
   ↓ DB (temu_orders.tracking_number)
   ↓
[Step 5] push_tracking_to_temu()
   ↓
TEMU API (status updated)
```

### Inventory Workflow (4 Steps)
```
TEMU API (getGoodsList)
   ↓
[Step 1] fetch_and_store_raw_skus()
   ↓ JSON Files
   ↓
[Step 2] import_skus_from_json()
   ↓ DB (temu_products)
   ↓
[Step 3] refresh_inventory_from_jtl()
   ↓ DB (temu_inventory) + Calculation
   ↓
[Step 4] sync_stock_deltas()
   ↓
TEMU API (updateStockTarget)
```

### Request Processing (API)
```
Browser
   ↓ HTTP
   ↓
FastAPI (main.py)
   ↓ Route Handler
   ↓
Business Logic (modules/temu/)
   ↓
Database (SQLAlchemy)
   ↓ SQL
   ↓
SQL Server
   ↓
Response JSON
   ↓
Browser
```

---

## 4. Wichtige Patterns & Conventions

### Dependency Injection
```python
@dataclass
class MyService:
    repo: MyRepository           # Injiziert
    other_service: OtherService
    connection: Optional[Connection] = None
    
    def __post_init__(self):
        # Lazy Loading
        if self.connection is None:
            self.connection = db_connect(DB_TOCI)
```

**Nutzen:**
- Einfacher zu testen (Mock Repos)
- Transactional Control (externe Connection)
- Klar welche Dependencies nötig sind

### Context Manager Pattern (Transactions)
```python
with db_connect(DB_TOCI) as conn:
    repo1 = ProductRepository(conn)  # Teilt Connection
    repo2 = InventoryRepository(conn)
    
    repo1.insert(product)
    repo2.insert(inventory)
    # → Auto COMMIT wenn kein Exception
    # → Auto ROLLBACK wenn Exception
```

### SQLAlchemy + Raw SQL
```python
sql = text("""
    SELECT * FROM table
    WHERE id IN :ids
""")
result = conn.execute(sql, {"ids": [1, 2, 3]})

# Für IN mit vielen Items: Expanding
from sqlalchemy import bindparam, expanding
sql = text("""
    SELECT * FROM table
    WHERE id IN :ids
""").bindparams(bindparam("ids", expanding=True))

result = conn.execute(sql, {"ids": list_of_1000_items})
```

**Nutzen:**
- Type Safety
- SQL Injection Protection
- Batch Query Optimization

---

## 5. Häufig verwendete SQL Queries

### Stock Lookup (JTL)
```sql
-- Get Available Stock (nach Puffer)
SELECT 
    kArtikel,
    fBestand - nPuffer AS available_stock
FROM tArtikel t
LEFT JOIN vLagerbestandProLager v ON t.kArtikel = v.kArtikel
WHERE t.cArtNr = :sku
```

### Tracking Lookup (JTL)
```sql
-- Get Tracking for Order
SELECT 
    ls.cLieferscheinnummer AS tracking_number,
    lp.cVersandartName AS carrier_name
FROM lvLieferschein ls
LEFT JOIN lvLieferscheinpaket lp ON ls.kLieferschein = lp.kLieferschein
WHERE ls.kBestellung = :order_id
```

### Job Status
```sql
-- Get Recent Job Logs
SELECT TOP 50 *
FROM dbo.scheduler_logs
WHERE job_id = :job_id
ORDER BY timestamp DESC
```

---

## 6. Performance Notes

### Batch Queries (2100 Parameter Limit)
```python
# SQL Server hat Limit: 2100 Parameter pro Query
# Lösung: Chunking in 1000er Blöcken

def query_in_batches(repo, ids, chunk_size=1000):
    results = {}
    for chunk in chunked(ids, chunk_size):
        chunk_results = repo.get_batch(chunk)
        results.update(chunk_results)
    return results

# Benchmark:
# - 1000 Items: 1x Query (~0.08s)
# - 4000 Items: 4x Queries (~0.32s)
# - N+1 (4000x einzeln): ~2.5s ❌
```

### Connection Pooling
```python
# SQLAlchemy Pool
pool_size=10              # Basis
max_overflow=20           # Zusätzliche bei Last
pool_pre_ping=True        # Tote Connections filtern
pool_recycle=3600         # Alte erneuern nach 1h

# Nutzen:
# - Schnellerer Zugriff (reuse connections)
# - Thread-safe
# - Overflow bei gleichzeitigen Requests
```

### API Response Times
```
GET /api/jobs/status
  - Cold Start: ~0.1s (cache aufwärmen)
  - Warm: ~0.05s (in-memory cache)
  
POST /api/jobs/temu_inventory_sync/execute
  - Trigger: ~0.02s (nur Queue, nicht warten)
  - Actual Job: ~12s (abhängig von Datenmenge)
```

---

## 7. Testing & Debugging

### Manueller Job-Test
```bash
# SSH zum Server
ssh chx@server.de
cd /home/chx/temu

# Aktiviere venv
source .venv/bin/activate

# Teste Order Workflow
python -c "
from modules.temu.services.order_workflow_service import OrderWorkflowService
workflow = OrderWorkflowService()
result = workflow.execute()
print(result)
"
```

### API Health Check
```bash
curl http://localhost:8000/api/health
# {"status": "ok"}

curl http://localhost:8000/api/jobs/status
# {"temu_orders_sync": {...}, ...}
```

### WebSocket Test
```bash
# Öffne in Browser:
http://localhost:8000/test_websocket.html
# Sollte "✅ Connected" zeigen
```

### PM2 Logs
```bash
pm2 logs temu-api --err    # Nur Errors
pm2 logs | grep ERROR      # Alle Error-Lines
pm2 monit                   # Live Monitoring
```

---

**Summe:** TEUM-Integration ist modular aufgebaut mit klaren Verantwortlichkeiten pro Layer (API, DB, Services, Workflows, Jobs). DI + Lazy Loading für Flexibilität, Context Manager für Transactional Safety, Batch Queries für Performance.
