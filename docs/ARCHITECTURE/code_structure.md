# Code Structure – Projektarchitektur & Modul-Overview

Quick Reference für die TEMU-Integration Codebase.

---

**Datum:** 19. Februar 2026

---

## 1. Projektbaum (Stand: 19. Februar 2026)

```
/home/chx/entwicklung/
├── .venv/                         # Python Virtual Environment
├── data/                          # Runtime Data (JSON, XML, PDFs)
│   ├── csv_verarbeiter/
│   │   ├── eingang/
│   │   ├── ausgang/
│   │   ├── ausgang_archive/
│   │   ├── archive/
│   │   ├── reports/
│   │   └── tmp/
│   ├── pdf_reader/
│   │   ├── eingang/{rechnungen,werbung}
│   │   ├── ausgang/
│   │   └── tmp/
│   └── temu/
│       ├── api_responses/
│       ├── xml/
│       └── export/
├── docs/                          # Project Documentation
├── frontend-react/                # React 19 SPA (aktiviert am 19.02.2026)
│   ├── src/
│   │   ├── components/           # UI Components (shadcn/ui)
│   │   │   ├── ui/               # Button, Card, Input, Select, Dialog, Table, Tabs
│   │   │   ├── layout/           # App Shell, Sidebar, Header
│   │   │   └── shared/           # Spinner, Skeleton, Toast, Error Boundary
│   │   ├── pages/                # Page Components
│   │   │   ├── dashboard.tsx
│   │   │   ├── temu-connector.tsx
│   │   │   ├── csv/
│   │   │   │   └── processor.tsx
│   │   │   └── pdf-reader.tsx
│   │   ├── hooks/                # Custom Hooks (use-api, use-websocket)
│   │   ├── lib/                  # Utilities
│   │   │   ├── api-client.ts    # axios instance + TypeScript Interfaces
│   │   │   └── utils.ts         # Tailwind helper
│   │   ├── types/                # TypeScript Type Definitions
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── public/
│   │   └── icons/
│   ├── dist/                     # Build Output (wird von API served)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts            # Proxy: /api → localhost:8888
│   ├── tailwind.config.js
│   └── tsconfig.json
├── logs/                          # Runtime Logs by Module
│   ├── app/
│   ├── csv_verarbeiter/
│   ├── pdf_reader/
│   └── temu/
├── modules/                       # ALL application modules (monorepo)
│   ├── shared/                    # Common Infrastructure
│   │   ├── config/                # Settings, .env file
│   │   ├── connectors/
│   │   │   ├── base_connector.py  # Basis-Connector Klasse
│   │   │   └── temu/              # TEMU API Client
│   │   ├── database/
│   │   │   ├── connection.py      # SQLAlchemy Engine + Pool
│   │   │   └── repositories/
│   │   │       ├── _log_helper.py # Zentralisierte Log-Service Lazy-Init
│   │   │       ├── base.py        # BaseRepository Pattern
│   │   │       ├── common/        # Log Repository
│   │   │       ├── jtl_common/    # JTL Lookups
│   │   │       └── temu/          # TEMU Repositories
│   │   │           ├── models.py  # Domain Models (Order, OrderItem)
│   │   │           ├── inventory_repository.py
│   │   │           ├── order_repository.py
│   │   │           ├── order_item_repository.py
│   │   │           └── product_repository.py
│   │   ├── logging/               # Log Service + Logger Factory
│   │   │   ├── log_service.py     # DB-basiertes Logging (Business Events)
│   │   │   └── logger.py          # RotatingFileHandler (Technical Errors)
│   │   ├── errors/                # Error Handling (NEW ✅ 19.02.2026)
│   │   │   └── handler.py         # @handle_api_errors Decorator
│   │   └── routers/               # Extrahiert aus main.py (NEW ✅ 19.02.2026)
│   │       ├── static_router.py   # FastAPI StaticFiles (/static, /icons, /components)
│   │       ├── ui_router.py       # UI-Routen → frontend-react/dist
│   │       ├── log_router.py      # Log Management (/api/logs)
│   │       └── websocket_router.py # WebSocket (/ws/logs)
│   ├── temu/                      # TEMU Marketplace Integration
│   │   ├── services/
│   │   │   ├── config.py          # Zentralisierte Constants (15+ Named Constants)
│   │   │   ├── base_workflow_service.py  # Shared Workflow Infrastructure
│   │   │   ├── order_service.py          # Order Import (God Method → 5 Helpers)
│   │   │   ├── order_workflow_service.py # 5-Step Order Sync
│   │   │   ├── inventory_service.py      # Inventory Management
│   │   │   ├── inventory_workflow_service.py # 4-Step Inventory Sync
│   │   │   ├── tracking_service.py       # JTL→TEMU Tracking
│   │   │   └── stock_sync_service.py     # Stock Delta Push
│   │   ├── jobs.py                # APScheduler Job Definitions
│   │   └── router.py              # FastAPI Routes
│   ├── pdf_reader/                # PDF Processing Module
│   │   ├── services/
│   │   │   ├── amount_utils.py    # Zentralisierte Betrags-Utilities
│   │   │   ├── config.py          # PDF Config
│   │   │   ├── document_identifier.py    # PDF-Typ Erkennung
│   │   │   ├── patterns.py               # Regex Patterns (DE/UK/IT/FR/SE)
│   │   │   ├── rechnungen_service.py     # Rechnungs-Parsing
│   │   │   ├── werbung_service.py        # Werbungs-Parsing
│   │   │   └── werbung_extraction_service.py # Seiten-Extraktion
│   │   └── router.py              # FastAPI Routes
│   ├── jtl/                       # JTL ERP Integration
│   │   └── xml_export/
│   │       └── xml_export_service.py  # XML Generation (refactored)
│   └── csv_verarbeiter/           # CSV Processing (JTL→DATEV) [✅ Abgeschlossen]
│       ├── services/              # CSV Processing Logic
│       └── router.py              # FastAPI Routes
├── workers/                       # APScheduler Job Management
│   ├── config/
│   │   └── workers_config.json    # Schedule + Intervals
│   ├── job_models.py
│   ├── worker_service.py
│   ├── workers_config.py
│   └── jobs_router.py             # Job Management Router (NEW ✅ 19.02.2026)
├── .gitignore
├── AI_GUIDE.md                    # Haupt-Projektleitfaden für AI
├── db_schema.sql
├── ecosystem.config.js            # PM2 Configuration
├── main.py                        # Unified FastAPI Gateway (refactored: 419→162 Zeilen)
├── requirements.txt
└── start_dev.sh                   # Development Start Script
```

---

## 2. Kern-Module (Verantwortlichkeiten)

### API Layer – `main.py` (Refactored: 419→162 Zeilen ✅)
**Verantwortung:** HTTP/WebSocket Schnittstelle

**Metriken (Phase 1 Refactoring - 19.02.2026):**
- Vorher: 419 Zeilen
- Nachher: 162 Zeilen (-61%)
- Ziel: ~150 Zeilen ✅

**Features:**
- FastAPI (async, ASGI)
- Pydantic für Request/Response Validation
- WebSocket für Live-Updates (JSON messages)
- Error Handling mit HTTP Status Codes
- CORS + Security Headers

**Router-Struktur (extrahierte Module):**
```
main.py (162 Zeilen)
├── modules/shared/routers/static_router.py     # /static, /icons, /components
├── modules/shared/routers/ui_router.py         # /, /pdf, /temu, /csv, /docs
├── modules/shared/routers/log_router.py        # /api/logs
├── modules/shared/routers/websocket_router.py  # /ws/logs
├── workers/jobs_router.py                      # /api/jobs
├── modules/temu/router.py                      # /api/temu
├── modules/pdf_reader/router.py                # /api/pdf
└── modules/csv_verarbeiter/router.py           # /api/csv
```

---

### PDF Reader – `modules/pdf_reader/`
**Verantwortung:** PDF Upload, Extraktion (Werbung/Rechnungen) und Excel-Export

**Kern-Dateien:**
- `router.py` – Upload, Extract, Process, Result Endpoints
- `services/rechnungen_service.py` – Rechnungs-Parsing
- `services/werbung_service.py` – Werbungs-Parsing
- `services/werbung_extraction_service.py` – Erste Seite extrahieren
- `services/amount_utils.py` – Gemeinsame Betrags-Parsing-Utilities

**Datenpfade:**
- `data/pdf_reader/eingang/{rechnungen,werbung}` – Uploads
- `data/pdf_reader/tmp` – extrahierte Einzelseiten (Werbung)
- `data/pdf_reader/ausgang` – Excel-Exporte

**Security/Robustheit:**
- Uploads akzeptieren nur `.pdf`
- 50 MB Größenlimit pro Datei
- Dateiname wird bereinigt (Path Traversal Schutz)
- `extract_text()` None-safe für bildbasierte PDFs

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
- `_log_helper.py` – Zentralisierte `_get_log_service()` Lazy-Import (DRY, ersetzt 6× kopierte Funktion)
- `base.py` – BaseRepository Pattern (gemeinsame CRUD-Methoden)
- `temu/models.py` – Domain Models `Order` und `OrderItem` (extrahiert aus Repositories)
- `temu/product_repository.py` – temu_products (Insert, Update, Get)
- `temu/inventory_repository.py` – temu_inventory (Stock Tracking, `mark_synced` mit explizitem Loop)
- `temu/order_repository.py` – temu_orders (Order CRUD, `_ORDER_COLUMNS` Klassenkonstante, Batch-Query für Tracking)
- `temu/order_item_repository.py` – temu_order_items (Line Items, `_ITEM_COLUMNS` Klassenkonstante)
- `jtl_common/jtl_repository.py` – JTL Lookups (tArtikel, vLagerbestandProLager) — Dead Code bereinigt
- `common/log_repository.py` – Logging (parametrisiertes `SELECT TOP`, Input-Clamping)

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

**Basis-Klasse:** `base_connector.py` – Gemeinsame Connector-Infrastruktur

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

#### `order_service.py` – Order Import (Refactored ✅)
```python
class OrderService:
    import_orders_from_json(json_data) → Inserted Orders
    
    # Orchestrator Pattern (vorher 120-Zeilen God Method):
    _load_json_responses()            # JSON-File-Handling + Validation
    _parse_shipping_data(order)       # Customer/Address-Extraktion
    _parse_amount_data(order)         # Pricing-Extraktion (AMOUNT_DIVISOR, TAX_RATE_DIVISOR)
    _upsert_order(conn, order_data)   # Order Insert/Update Logic
    _upsert_order_items(conn, items)  # Order Items Processing
    
    # Return: {"inserted": n, "updated": n, "errors": n}
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

#### `tracking_service.py` – Tracking Management (Refactored ✅)
```python
class TrackingService:
    sync_tracking_from_jtl(order_ids) → Synced Count
    
    Steps:
    1. Find Orders without Tracking in DB
    2. Lookup Order ID in JTL (lvLieferschein)
    3. Get Tracking Number + Carrier
    4. Map Carrier to TEMU Carrier ID (via CARRIER_MAPPING constant)
    5. Store in temu_orders.tracking_number
    
    # Carrier Mapping (aus config.py):
    # CARRIER_MAPPING = {'dhl': 141252268, 'dpd': 998264853, ...}
    # 201 → 159 Zeilen (-21%) nach Dead Code Cleanup
```

#### `stock_sync_service.py` – Stock Delta Sync (Refactored ✅)
```python
class StockSyncService:
    sync_stock_deltas() → {"processed": n}
    
    Steps:
    1. Get all temu_inventory where needs_sync=1
    2. Group by goods_id
    3. For each group: Call TEMU API updateStockTarget
    4. Mark synced_at, needs_sync=0 (sofort nach jedem Teil-Update)
    5. Log errors (missing ID, API fail)
    
    # 105 → 80 Zeilen (-24%) nach Dead Code Cleanup
    # Counter vereinfacht: "processed" statt "inserted/updated" (MERGE unterscheidet nicht)
    
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

#### `base_workflow_service.py` – Shared Workflow Infrastructure (NEW ✅)
**Verantwortung:** Gemeinsame Connection-, Credential- und Job-Lifecycle-Verwaltung für alle Workflow-Services

**Basis-Klasse für Workflow Services:**
```python
class BaseWorkflowService:
    def _validate_credentials(self) → bool
        # Check TEMU API keys vorhanden
    
    def _generate_job_id(self) → str
        # Unique Job ID mit Timestamp
    
    def _cleanup_connections(self) → None
        # Reset connection state, call subclass cleanup hook
    
    def _cleanup_service_caches(self) → None
        # Override hook für Subclasses, z.B. für Domain-spezifische Repos
    
    def _get_temu_service(self) → TemuService
        # Lazy-load shared TemuMarketplaceService
    
    def _get_jtl_repo(self) → JltRepository
        # Lazy-load shared JltRepository
```

**Vorteile:**
- ✅ **Eliminiert 55+ Zeilen Duplikation** zwischen OrderWorkflowService und InventoryWorkflowService
- ✅ **DRY Prinzip:** Credential checking, job ID generation, connection lifecycle zentral
- ✅ **Inheritance Chain:** OrderWorkflowService → BaseWorkflowService → object
- ✅ **MRO validiert:** Korrekte Method Resolution Order für Override patterns
- ✅ **Testierbar:** Mocks für Basis-Funktionalität möglich

**Subclass Example:**
```python
class OrderWorkflowService(BaseWorkflowService):
    def run_complete_workflow(self) → WorkflowResult:
        self._validate_credentials()  # From base
        job_id = self._generate_job_id()  # From base
        
        # Domain-specific logic
        result = self._step_1_fetch_api()  # Nur in Order
        result += self._step_2_import_db()  # Nur in Order
        # ...
        
        self._cleanup_connections()  # From base
        return result
    
    def _cleanup_service_caches(self) → None:
        # Override for Order-specific repos
        self.order_repo = None
        self.order_item_repo = None
        # ...
```

**Metriken:**
- OrderWorkflowService: 312 → 259 Zeilen (-17% Duplikation)
- InventoryWorkflowService: 211 → 189 Zeilen (-10% Duplikation)
- BaseWorkflowService: 97 neue Zeilen (gut investiert)

Architecture:
- DI: Services injiziert (TemuService, Repos, JTL Repo)
- Lazy Loading: Connections erst bei Bedarf
- Error Handling: Catch + Log, nicht crash
- Transactional: Context Manager für multi-step safety
- **NEW:** BaseWorkflowService für shared infrastructure
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

### Config & Constants – `modules/temu/config/config.py`

**Verantwortung:** Zentralisierte Geschäftskonstanten und Magic Numbers

**Neue Constants (Prio 3 Refactoring: 15+ Named Constants):**
```python
# API Response Parsing
AMOUNT_DIVISOR = 100              # TEMU API gibt Beträge in Cents
TAX_RATE_DIVISOR = 1_000_000      # TEMU Tax Rate in Mikrotax (19000000 = 19%)

# Status & Mapping
ORDER_STATUS_MAP = {
    1: 'pending',
    2: 'processing',
    3: 'shipped',
    4: 'delivered',
    5: 'cancelled',
}
VALID_ORDER_STATUSES = {0, 1, 2, 3, 4, 5}           # Router Validierung
WORKFLOW_ORDER_STATUSES = {2, 3, 4, 5}             # Workflow execution filter

# Carrier Mapping (TEMU Carrier IDs)
CARRIER_MAPPING = {
    'dhl': 141252268,
    'dpd': 998264853,
    'hermes': 414141241,
    'ups': 141241414,
    'gls': 141214124,
}

# Scheduler Defaults
ORDER_SYNC_INTERVAL_MINUTES = 30          # Default: alle 30 Min
INVENTORY_SYNC_INTERVAL_MINUTES = 60      # Default: alle 60 Min
```

**Vorteile:**
- ✅ **Single Source of Truth:** Alle Magic Numbers zentral
- ✅ **Weniger Fehler:** Keine Typos bei hardcoded values
- ✅ **Einfach zu testen:** Constants mockbar
- ✅ **Runtime-Tuning:** Interval-Änderungen ohne Code-Restart
- ✅ **Konsistenz:** Router + Service validieren mit gleichen Sets

**Metriken:**
- config.py: 29 → 97 Zeilen (gut investiert)
- ~20 Hardcoded Values ersetzt verteilt über 5+ Dateien
- Imports in order_service.py, router.py, jobs.py aktualisiert

---

### Services – `modules/shared/logging/`

#### `log_service.py` – Centralized Logging (DB-basiert)
```python
class LogService:
    log_job(job_id, job_type, level, message, status=None)
    get_job_logs(job_id, limit=50)
    get_job_stats(job_id)  # success rate, duration avg
    _ensure_table()  # Lazy Init — App startet auch ohne DB
```

Speichert in `dbo.scheduler_logs` (SQL Server).
**Lazy Init:** `ensure_table_exists()` aus `__init__` in Lazy `_ensure_table()` verschoben — Server startet auch wenn DB offline ist.

#### `logger.py` – File-based Logging (Technical Errors)
```python
# RotatingFileHandler (10MB, 5 Backups) — verhindert unbegrenztes Log-Wachstum
# Ersetzt früheren FileHandler
# print()-Fallbacks durch app_logger.error() ersetzt
```

---

### JTL XML-Export – `modules/jtl/xml_export/xml_export_service.py` (Refactored ✅)

**Verantwortung:** XML-Generierung für JTL ERP Import (Bestellungen aus TEMU)

**Methoden-Übersicht (logisch gruppiert):**
```python
class XmlExportService:
    # ── Public API ──
    export_to_xml(order_ids) → ExportResult
    
    # ── Order Processing ──
    _process_single_order(order) → ET.Element      # Aus Loop-Body extrahiert
    _fetch_order_items(order_id) → list[OrderItem]  # Item-Fetching isoliert
    
    # ── XML Generation ──
    _generate_order_xml(order) → ET.Element
    _add_header_fields(elem, order) → None          # Header-Felder extrahiert
    _prettify_wrapped_xml(root, elem) → str         # DRY: 3× Pattern konsolidiert
    _prettify_xml(xml_string) → str                 # + Control-Char Sanitization
    
    # ── Customer Lookup ──
    _get_customer_number(order) → str               # Cache mit MAXSIZE=1000
    
    # ── Persistence ──
    _save_xml_to_disk(root) → Path
    _import_to_jtl(root) → None                     # copy.deepcopy() für append
    _archive_order_to_docs(root) → None             # copy.deepcopy() für append
    _save_xml_to_db(root) → None                    # copy.deepcopy() für append
```

**Wichtige Konstanten:**
- `VERSAND_MWST_SATZ = 19.0` (ersetzt Magic Number `1.19`)
- `_CUSTOMER_CACHE_MAXSIZE = 1000` (begrenzt Memory-Wachstum)

**Bug Fix (Critical):** `ET.Element.append()` verschiebt Elemente statt zu kopieren → `copy.deepcopy()` in 3 Persistence-Methoden

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
curl http://localhost:8401/api/health
# {"status": "ok"}

curl http://localhost:8401/api/jobs/status
# {"temu_orders_sync": {...}, ...}
```

### WebSocket Test
```bash
# Öffne in Browser:
http://localhost:8401/test_websocket.html
# Sollte "✅ Connected" zeigen
```

### PM2 Logs
```bash
pm2 logs temu-api --err    # Nur Errors
pm2 logs | grep ERROR      # Alle Error-Lines
pm2 monit                   # Live Monitoring
```

---

**Summe:** TEMU-Integration ist modular aufgebaut mit klaren Verantwortlichkeiten pro Layer (API, DB, Services, Workflows, Jobs). DI + Lazy Loading für Flexibilität, Context Manager für Transactional Safety, Batch Queries für Performance.
