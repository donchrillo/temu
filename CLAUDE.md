# CLAUDE.md

> ✅ **UPDATED:** 3. Februar 2026 - Monorepo Migration Complete
>
> This file describes the NEW monorepo structure.
>
> **Migration completed successfully** - all modules migrated to `modules/` structure.

---

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a TEMU marketplace integration system that synchronizes orders, inventory, and documents between TEMU's marketplace API and a JTL ERP system running on SQL Server. The system consists of a FastAPI backend with scheduled jobs, a PWA frontend with real-time WebSocket updates, and PDF processing capabilities.

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Edit modules/shared/config/.env with database credentials and TEMU API keys
```

### Running the Application

**Development (local):**
```bash
# Start the unified gateway with auto-reload
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Production (PM2):**
```bash
# Start with PM2 (process manager)
pm2 start ecosystem.config.js

# View logs
pm2 logs temu-api

# Restart after changes
pm2 restart temu-api

# Stop the application
pm2 stop temu-api

# View status
pm2 status
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=modules --cov-report=html

# Run specific test file
pytest tests/test_order_service.py

# Run specific test
pytest tests/test_order_service.py::test_import_orders
```

### Code Quality

```bash
# Format code with Black
black modules/ workers/ main.py

# Lint with flake8
flake8 modules/ workers/ main.py

# Type checking with mypy
mypy modules/ workers/ main.py
```

## Architecture

### Core Components

**API Gateway** (`main.py`)
- Unified FastAPI gateway serving all module routes
- Mounts TEMU module (`/api/temu/*`) and PDF Reader module (`/api/pdf/*`)
- WebSocket endpoint (`/ws/logs`) broadcasts real-time job updates every 2 seconds
- Serves module-specific frontends (`/temu/`, `/pdf/`)

**Scheduler** (`workers/worker_service.py`)
- APScheduler (AsyncIO-based) manages periodic jobs
- Job configuration persisted to `workers/config/workers_config.json`
- Three job types: `SYNC_ORDERS`, `SYNC_INVENTORY`, `FETCH_INVOICES`
- Jobs can be triggered manually via API or run on schedule

**Frontend** (`frontend/`)
- Progressive Web App with service worker for offline support
- Real-time job monitoring via WebSocket connection
- Log filtering, export, and PDF upload interfaces

### Data Flow Patterns

**5-Step Order Workflow** (`modules/temu/services/order_workflow_service.py`):
1. Fetch orders from TEMU API → save JSON response
2. Import JSON to database (`temu_orders`, `temu_order_items`)
3. Generate XML exports for JTL via `modules/jtl/xml_export/`
4. Upload XML to JTL (future: direct API integration)
5. Fetch tracking from JTL, update orders, report back to TEMU

**4-Step Inventory Workflow** (`modules/temu/services/inventory_workflow_service.py`):
1. Download SKU list from TEMU
2. Fetch stock levels from JTL database
3. Compare and mark deltas in `temu_inventory` table
4. Push updates to TEMU API

Each workflow step uses separate database transactions to ensure data persistence even if later steps fail.

### Database Architecture

**Two Databases:**
- `toci`: Primary application database (TEMU orders, inventory, logs)
- `eazybusiness`: JTL ERP database (read-only access for stock levels)

**Key Tables in TOCI:**
- `temu_orders`: Order headers with status tracking (`importiert` → `xml_erstellt` → `versendet` → `storniert`)
- `temu_order_items`: Line items with product details, quantities, prices
- `temu_xml_export`: XML generation queue for JTL integration
- `temu_products`: TEMU SKU to JTL article ID mapping
- `temu_inventory`: Stock synchronization with `needs_sync` flag
- `temu_logs`: Job execution logs with filtering support

**Connection Management:**
- SQLAlchemy engine with connection pooling (size: 10, overflow: 20)
- Platform-aware ODBC driver selection (Linux vs Windows)
- Repository pattern for all database operations (`modules/shared/database/repositories/`)
- Context managers handle transaction lifecycle

### Module Structure (Monorepo Architecture)

**`modules/shared/`** - Common Infrastructure
- `database/`: Connection management, repositories (TOCI + JTL)
  - `connection.py`: Engine pooling, db_connect context manager
  - `repositories/temu/`: Order, OrderItem, Product, Inventory repositories
  - `repositories/jtl_common/`: JTL database access
  - `repositories/common/`: Log repository
- `connectors/temu/`: TEMU API client (HTTP, signing, endpoints)
- `logging/`: Log service, logger factory
- `config/`: Settings loader, .env file

**`modules/temu/`** - TEMU Marketplace Integration
- `router.py`: FastAPI routes (`/api/temu/*`)
- `jobs.py`: APScheduler job definitions
- `frontend/`: PWA interface
- `services/`: Business logic
  - `order_workflow_service.py`: 5-step order sync orchestration
  - `inventory_workflow_service.py`: 4-step inventory sync
  - `tracking_service.py`: Tracking updates from JTL
  - `order_service.py`, `inventory_service.py`: Core business logic

**`modules/pdf_reader/`** - PDF Processing
- `router.py`: FastAPI routes (`/api/pdf/*`)
- `frontend/`: Upload interface
- `services/`: PDF extraction (rechnungen, werbung)

**`modules/jtl/`** - JTL ERP Integration
- `xml_export/`: XML generation service for JTL
  - `xml_export_service.py`: Converts orders to JTL XML format
  - Future: Direct API connector module

### Important Patterns

**SQL Server 2100 Parameter Limit:**
Database batch operations must chunk parameters to avoid SQL Server's 2100 parameter limit. Repository methods handle this automatically when inserting/updating large batches.

**PDF Reader Filename Mapping:**
The advertising invoice workflow (`werbung_service.py`) renames PDFs during extraction to `{country}_{start_date}_{end_date}.pdf`. To preserve original filenames in Excel exports, a mapping file (`filename_mapping.json`) is saved in the TMP directory. The `process_ad_pdfs()` function automatically loads this mapping when processing.

**Currency-Aware Number Parsing:**
The `parse_amount()` function in `werbung_service.py` handles decimal separators based on currency:
- GBP/USD: Period is decimal separator (e.g., "121.22")
- EUR/SEK/PLN: Comma is decimal separator (e.g., "121,22")
This ensures correct amount parsing for invoices from different countries.

**Job State Management:**
Jobs transition through states: `pending` → `running` → `completed`/`failed`. State persists in database (`temu_logs`) and broadcasts via WebSocket. Jobs can be manually triggered even if scheduled.

**Module Logging:**
Centralized logging via shared module:
```python
from modules.shared.logging.log_service import log_service
log_service.log(job_id, "order_workflow", "INFO", "Processing order...")
```
Logs write to database (`scheduler_logs`) and broadcast via WebSocket to frontend.

**Configuration Management:**
- Environment variables loaded from `modules/shared/config/.env` via python-dotenv
- `modules/shared/config/settings.py` provides centralized access to credentials
- Never commit `.env` file (contains database passwords, API keys)

**WebSocket Updates:**
The log service captures job execution and broadcasts updates to all connected WebSocket clients. Frontend automatically reconnects on disconnect with exponential backoff.

## Directory Layout (Monorepo Structure)

```
/modules/              - ALL application modules (monorepo)
  /shared/            - Common infrastructure
    /database/        - Connection, repositories (TOCI + JTL)
    /connectors/      - Marketplace API clients (TEMU)
    /logging/         - Log service, logger factory
    /config/          - Settings, .env file
  /temu/              - TEMU marketplace integration
    /services/        - Business logic (orders, inventory, tracking)
    /frontend/        - PWA interface
    router.py         - API routes
    jobs.py           - Scheduled jobs
  /pdf_reader/        - PDF processing module
    /services/        - PDF extraction logic
    /frontend/        - Upload interface
    router.py         - API routes
  /jtl/               - JTL ERP integration
    /xml_export/      - XML generation service

/workers/             - APScheduler job management
/data/                - Runtime data (JSON, XML, PDFs)
/docs/                - Architecture documentation
/logs/                - Runtime logs by module
/main.py              - Unified FastAPI gateway
/ecosystem.config.js  - PM2 configuration
```

## Critical Files

- `main.py`: Unified gateway mounting all module routes
- `workers/worker_service.py`: Job scheduler implementation
- `workers/config/workers_config.json`: Job schedules (persisted across restarts)
- `modules/shared/config/.env`: Credentials and secrets (NOT in git)
- `modules/shared/config/settings.py`: Configuration loader
- `db_schema.sql`: Database schema definition
- `ecosystem.config.js`: PM2 production deployment config
- `requirements.txt`: Python dependencies

## Common Tasks

**Add a new scheduled job:**
1. Define job function in relevant service (e.g., `modules/temu/services/`)
2. Add job type to `workers/job_models.py` JobType enum
3. Register job in `SchedulerService.initialize_from_config()`
4. Job configuration auto-saves to `workers/config/workers_config.json`

**Add a new REST endpoint:**
1. Add route to module router (e.g., `modules/temu/router.py`)
2. Use dependency injection for services (avoid global state)
3. Return structured responses (use Pydantic models)
4. Add error handling with appropriate HTTP status codes
5. Routes auto-mount in `main.py` via module routers

**Add a new database table:**
1. Update `db_schema.sql` with table definition
2. Create repository class in `modules/shared/database/repositories/`
3. Inherit from `BaseRepository` for common operations
4. Use context managers for transaction handling

**Debug a workflow:**
1. Check database logs in `scheduler_logs` table
2. View WebSocket updates in frontend for real-time status
3. Use `pm2 logs temu-api` for server logs
3. Query `temu_logs` table for historical job execution
4. Use `/api/logs` endpoint with filters for specific job types

## Deployment Notes

**Environment Variables Required:**
- `SQL_SERVER`, `SQL_USERNAME`, `SQL_PASSWORD`: Database credentials
- `TEMU_APP_KEY`, `TEMU_APP_SECRET`, `TEMU_ACCESS_TOKEN`: TEMU API credentials
- Optional: `JTL_WAEHRUNG`, `JTL_SPRACHE`, `JTL_K_BENUTZER`, `JTL_K_FIRMA`

**PM2 Process Management:**
PM2 auto-restarts on crash, limits memory to 500MB, logs to `logs/pm2-*.log`. Configuration in `ecosystem.config.js`.

**Frontend PWA:**
Progressive Web App supports offline mode via service worker. Manifest at `/frontend/manifest.json`. Icons must be served from `/static/icons/` route.

**Database Connections:**
Connection pool shared across requests. Avoid holding transactions open across async boundaries. Use repository context managers for proper cleanup.

## Documentation

Comprehensive architecture documentation located in `docs/` directory:
- `ARCHITECTURE/code_structure.md`: Project structure and module overview
- `API/architecture.md`: FastAPI, WebSocket, security patterns
- `DATABASE/architecture.md`: SQLAlchemy, connection pooling, batch queries
- `WORKFLOWS/architecture.md`: APScheduler, PM2, job orchestration
- `FRONTEND/architecture.md`: PWA, WebSocket integration, offline support
- `DEPLOYMENT/architecture.md`: Remote SSH, PM2 commands
- `PERFORMANCE/architecture.md`: Benchmarks, monitoring, optimization
- `FIXES/`: Critical bug fixes and their solutions
  - `pdf_reader_fixes_2026-02-02.md`: Filename mapping, decimal separators, import fixes

Refer to these docs for detailed patterns, troubleshooting, and best practices.
