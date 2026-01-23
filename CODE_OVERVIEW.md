# TEMU Integration – Code & Struktur Überblick

## Projektstruktur (Top-Level)
- `api/`: FastAPI-Server (`server.py`) mit REST/WebSocket
- `config/`: Einstellungen (`settings.py`)
- `data/`: Persistierte API-Outputs & Exporte (z.B. `api_responses/`, `jtl_temu_bestellungen.xml`)
- `frontend/`: PWA (HTML/JS/CSS, Service Worker)
- `src/`: Business-Logik, DB-Layer, Connectoren, Module, Services
- `workers/`: Scheduler/Jobs (APScheduler), Worker-Config
- `workflows/`: Historische CLI-Wrapper (aktuell deaktiviert/backups)

## Kern-Module
- **API**: `api/server.py`
  - FastAPI + WebSocket für Job-Updates
  - Endpunkte: Health, Jobs, Trigger
  - JSON-Serialization fix via `jsonable_encoder`

- **DB**: `src/db/`
  - `connection.py`: DB-Verbindung (pyodbc, Pooling)
  - `repositories/`: CRUD für TEMU/JTL Tabellen (Orders, Items, Products, Inventory, Logs)

- **Marketplace Connector (TEMU)**: `src/marketplace_connectors/temu/`
  - `api_client.py`: Low-level Signaturen/HTTP
  - `orders_api.py`, `inventory_api.py`: Spezifische Endpunkte
  - `service.py`: High-level Connector; Orders & Shipping & Amount Fetch; (SKU-Fetch aktuell auskommentiert, nun im InventoryService)

- **Module TEMU**: `src/modules/temu/`
  - `order_service.py`: Importiert Orders aus JSON in DB
  - `inventory_service.py`: SKU-Download/Import, Inventory-Refresh aus JTL
  - `stock_sync_service.py`: Sendet Bestands-Deltas zu TEMU; gruppiert per goodsId
  - `tracking_service.py`: Holt Tracking aus JTL, schreibt in DB, mappt Carrier IDs für API
  - **Workflows** (Orchestrierung):
    - `order_workflow_service.py`: 5 Schritte Orders (API→JSON, JSON→DB, DB→XML, JTL→Tracking, Tracking→API); DI + lazy Services/Connections
    - `inventory_workflow_service.py`: 4 Schritte Inventory (API/JSON optional, JSON→DB, JTL→Inventory, Inventory→API); DI + lazy Services/Connections; SKU-Download nun via `InventoryService.fetch_and_store_raw_skus`

- **Services**: `src/services/`
  - `log_service.py`: Zentrales Logging mit Job-Capture
  - `logger.py`: Logger-Setup

- **Workers/Scheduler**: `workers/`
  - `worker_service.py`: Startet Jobs (sync_orders, sync_inventory, fetch_invoices)
  - `workers_config.json`: Intervalle/Enabled-Flags

- **Frontend**: `frontend/`
  - `index.html`, `app.js`, `service-worker.js`, `styles.css` etc.
  - PWA mit WebSocket für Live-Job-Status

## Wichtige Flows
### Order Workflow (5 Steps) – `order_workflow_service.py`
1) API→JSON: TEMU Orders holen, Shipping/Amounts je Order speichern
2) JSON→DB: Orders/Items importieren
3) DB→XML: Export für JTL (optional Import in JTL, falls Repo verfügbar)
4) JTL→Tracking: Tracking aus JTL in DB schreiben
5) DB→API: Tracking an TEMU hochladen, Status updaten
- DI + Lazy Loading: TemuService, Order/Item Repos, JTL Repo, XML/Tracking Services, DB-Connections
- Credential Guard (TEMU Keys/Tokens)

### Inventory Workflow (4 Steps) – `inventory_workflow_service.py`
- Modi: `full` (Steps 1-4) oder `quick` (nur 3+4)
1) API→JSON: SKU-Listen (Status 2 & 3) via `InventoryService.fetch_and_store_raw_skus`
2) JSON→DB: SKUs in `temu_products` importieren
3) JTL→Inventory: Bestände aus JTL nach `temu_inventory`
4) Inventory→API: Deltas zu TEMU; `StockSyncService` gruppiert per goodsId, markiert synced
- DI + Lazy Loading wie beim Order Workflow

### Tracking Service – `tracking_service.py`
- Holt Orders ohne Tracking, sucht Tracking in JTL, schreibt in DB
- Carrier-ID-Mapping für TEMU-API Upload
- Guard, falls kein JTL-Repo vorhanden

### Stock Sync – `stock_sync_service.py`
- Holt Deltas (`needs_sync=1`) aus `temu_inventory`
- Gruppiert per goodsId, sendet `update_stock_target`
- Skip/Warning bei fehlender goods_id/sku_id; markiert erfolgreiche Syncs in DB

## Daten / Artefakte
- `data/api_responses/temu_sku_status2.json` & `temu_sku_status3.json`: SKU-Listen (Status 2 & 3)
- `data/api_responses/api_response_orders.json`: Orders-Rohdaten
- `data/api_responses/api_response_shipping_all.json`, `api_response_amount_all.json`: Versand-/Preisdaten pro Order
- `data/jtl_temu_bestellungen.xml`: JTL-Export (Orders→XML)

## Aktuelle Änderungen / Besonderheiten
- Orders: Refactored auf DI/Lazy, JSON-Serialization Fix im WebSocket
- Inventory: Workflow refactored auf DI/Lazy; SKU-Download nur noch über `InventoryService.fetch_and_store_raw_skus`; alter SKU-Fetch im Temu-Service auskommentiert
- Stock Sync: Guard für fehlende IDs
- Tracking: Guard für fehlendes JTL-Repo, updated_count Fix

## Jobs (APScheduler)
- `sync_orders`: ruft OrderWorkflow (mode fix)
- `sync_inventory`: ruft InventoryWorkflow (default quick)
- `fetch_invoices`: Platzhalter/optional

## Nutzung
- API via PM2: Prozess `temu-api` (uvicorn/FastAPI)
- Health: `/api/health`
- Jobs: `/api/jobs` (inkl. Status/Logs), WebSocket für Live-Updates

