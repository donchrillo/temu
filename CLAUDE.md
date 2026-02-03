# CLAUDE.md

> ⚠️ **MIGRATION IN PROGRESS (3. Feb 2026)**
>
> This file describes the OLD structure (`src/`, `api/`, `config/`).
>
> **For current migration status, see:** [MIGRATION_STATUS.md](MIGRATION_STATUS.md)
>
> This file will be completely rewritten after migration is complete (Phase 8).

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
# Edit config/.env with database credentials and TEMU API keys
```

### Running the Application

**Development (local):**
```bash
# Start the API server with auto-reload
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
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
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_order_service.py

# Run specific test
pytest tests/test_order_service.py::test_import_orders
```

### Code Quality

```bash
# Format code with Black
black src/ api/ workers/

# Lint with flake8
flake8 src/ api/ workers/

# Type checking with mypy
mypy src/ api/ workers/
```

## Architecture

### Core Components

**API Server** (`api/server.py`)
- FastAPI application serving REST endpoints and WebSocket connections
- Handles job management, PDF uploads, and log queries
- WebSocket endpoint (`/ws/logs`) broadcasts real-time job updates every 2 seconds
- Serves static frontend files from `/frontend/` directory

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

**5-Step Order Workflow** (`src/modules/temu/order_workflow_service.py`):
1. Fetch orders from TEMU API → save JSON response
2. Import JSON to database (`temu_orders`, `temu_order_items`)
3. Generate XML exports for JTL
4. Upload XML to JTL (future implementation)
5. Fetch tracking from JTL, update orders, report back to TEMU

**4-Step Inventory Workflow** (`src/modules/temu/inventory_workflow_service.py`):
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
- Repository pattern for all database operations (`src/db/repositories/`)
- Context managers handle transaction lifecycle

### Module Structure

**`src/marketplace_connectors/temu/`**
- `api_client.py`: Low-level HTTP client with request signing
- `orders_api.py`, `inventory_api.py`: API endpoint wrappers
- `service.py`: High-level marketplace connector
- `signature.py`: TEMU request signature generation

**`src/modules/temu/`**
- Business logic services for order import, inventory sync, tracking
- Workflow orchestration services coordinate multi-step processes
- Module-specific logger writes to `logs/temu/`

**`src/modules/pdf_reader/`**
- PDF processing for invoices (`rechnungen`) and advertisements (`werbung`)
- Extract first pages, generate Excel reports
- Input/output directories in `data/pdf_reader/`

**`src/db/repositories/`**
- Repository pattern isolates database operations
- Base repository provides common CRUD operations
- Specialized repositories for orders, products, inventory, logs

**`src/services/`**
- `log_service.py`: Job logging to database with WebSocket broadcasting
- `logger.py`: Logger factory for module-specific logging

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
Each module creates its own logger with the module name:
```python
from src.modules.temu.logger import temu_logger
temu_logger.info("Processing order...")
```
Logs write to both console and module-specific files in `logs/<module>/`.

**Configuration Management:**
- Environment variables loaded from `config/.env` via python-dotenv
- `config/settings.py` provides centralized access to credentials
- Never commit `.env` file (contains database passwords, API keys)

**WebSocket Updates:**
The log service captures job execution and broadcasts updates to all connected WebSocket clients. Frontend automatically reconnects on disconnect with exponential backoff.

## Directory Layout

```
/api/           - FastAPI server and REST endpoints
/config/        - Configuration (settings.py reads from .env)
/data/          - Runtime data (JSON responses, XML exports, PDFs)
/docs/          - Detailed architecture documentation by topic
/frontend/      - PWA frontend (HTML, CSS, JavaScript)
/logs/          - Runtime logs organized by module
/src/           - Core application logic
  /db/          - Database connection and repositories
  /marketplace_connectors/  - External marketplace integrations
  /modules/     - Domain-specific business logic
  /services/    - Cross-cutting concerns (logging)
/workers/       - Background job scheduler and models
```

## Critical Files

- `api/server.py`: API server entry point with lifespan management
- `workers/worker_service.py`: Job scheduler implementation
- `workers/config/workers_config.json`: Job schedules (persisted across restarts)
- `config/.env`: Credentials and secrets (NOT in git)
- `config/settings.py`: Configuration loader
- `db_schema.sql`: Database schema definition
- `ecosystem.config.js`: PM2 production deployment config
- `requirements.txt`: Python dependencies

## Common Tasks

**Add a new scheduled job:**
1. Define job function in relevant service (e.g., `src/modules/temu/`)
2. Add job type to `workers/job_models.py` JobType enum
3. Register job in `SchedulerService.initialize_from_config()`
4. Job configuration auto-saves to `workers/config/workers_config.json`

**Add a new REST endpoint:**
1. Add route handler to `api/server.py`
2. Use dependency injection for services (avoid global state)
3. Return structured responses (use Pydantic models)
4. Add error handling with appropriate HTTP status codes

**Add a new database table:**
1. Update `db_schema.sql` with table definition
2. Create repository class in `src/db/repositories/`
3. Inherit from `BaseRepository` for common operations
4. Use context managers for transaction handling

**Debug a workflow:**
1. Check logs in `logs/<module>/` for detailed execution traces
2. View WebSocket updates in frontend for real-time status
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
