# TEMU ERP System Context

This `GEMINI.md` file provides context for AI agents interacting with the TEMU ERP System codebase.

## 1. Project Overview

The **TEMU ERP System** is a modular integration platform designed to synchronize data between the **TEMU Marketplace** and a **JTL ERP** system (Microsoft SQL Server). It handles orders, inventory, tracking, and document processing (PDFs, CSVs).

**Key Capabilities:**
*   **Order Sync:** Fetches orders from TEMU, imports them into a local database, and prepares them for JTL (XML export).
*   **Inventory Sync:** Synchronizes stock levels from JTL to TEMU (4-step workflow).
*   **PDF Processing:** Extracts data from invoices and advertising reports (Amazon/TEMU) and exports to Excel.
*   **CSV Processing:** (In Progress) Converts JTL CSV exports to DATEV format.
*   **Job Scheduling:** Automated background tasks via APScheduler.
*   **Frontend:** Progressive Web App (PWA) with real-time dashboards (WebSocket).

## 2. Architecture & Directory Structure

The project follows a **Monorepo** structure with strict separation of concerns.

### Top-Level Directories
*   `modules/`: Contains all application logic, split by domain.
    *   `shared/`: Common infrastructure (Database, Logging, Config, Connectors).
    *   `temu/`: TEMU Marketplace logic (Services, API, Frontend).
    *   `pdf_reader/`: PDF extraction logic (Services, API, Frontend).
    *   `csv_verarbeiter/`: CSV processing logic (In Development).
    *   `jtl/`: JTL-specific logic (XML Export).
*   `workers/`: APScheduler configuration and job runners.
*   `data/`: Runtime storage for processed files (JSON, XML, PDFs).
*   `docs/`: Comprehensive project documentation (Architecture, API, Fixes).
*   `frontend/`: Shared frontend assets and PWA entry point (`index-new.html`).
*   `logs/`: Application log files (technical logs).

### Key Files
*   `main.py`: Central **FastAPI Gateway**. Mounts routers from all modules.
*   `requirements.txt`: Python dependencies.
*   `ecosystem.config.js`: PM2 process manager configuration.
*   `AI_GUIDE.md`: Guidelines for AI agents working on this project.

## 3. Technology Stack

*   **Language:** Python 3.11+
*   **Framework:** FastAPI (Async/Await)
*   **Database:** MSSQL (pyodbc + SQLAlchemy)
*   **Scheduling:** APScheduler
*   **Data Processing:** Pandas, PDFPlumber, OpenPyXL
*   **Process Management:** PM2 (Node.js)
*   **Frontend:** Vanilla JS, CSS (Apple-style, zentralisiert in master.css), HTML5, PWA

## 4. Building and Running

### Development Environment
The project uses a Python virtual environment (`.venv`).

```bash
# 1. Activate Virtual Environment
source .venv/bin/activate

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Run Development Server (Auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment
Production is managed by PM2.

```bash
# Start/Restart Application
pm2 start ecosystem.config.js
# OR
pm2 restart temu-api

# Check Logs
pm2 logs temu-api
```

## 5. Development Conventions

### Code Style & Principles
*   **Modular Monorepo:** Logic must reside in `modules/<domain>/`. Shared code goes to `modules/shared/`.
*   **Dependency Injection:** Services inject Repositories and other Services. Avoid global state where possible.
*   **Transactional Safety:** Use `with db_connect(DB_NAME) as conn:` context managers for database operations.
*   **Logging:**
    *   **Business Logic:** Use `modules.shared.log_service` (writes to SQL DB for Frontend display).
    *   **Technical Errors:** Use `modules.shared.app_logger` (writes to `logs/` files for debugging).
*   **Configuration:** All config via `.env` files loaded in `modules/shared/config/settings.py`.
*   **Frontend CSS:** Use `master.css` for shared styles, module-specific CSS only for unique components.
*   **Central Navigation:** All pages use `nav-loader.js` for dynamic menu loading.

### Documentation Rules
*   **Live Docs:** Documentation in `docs/` is treated as code. Update it immediately upon changing logic.
*   **Key Docs:**
    *   `docs/CURRENT_STATUS.md`: Project progress and active tasks.
    *   `docs/TODO_LIST.md`: Backlog and known issues.
    *   `docs/FIXES/OVERVIEW.md`: Solutions to past complex bugs.

### Database Interaction
*   Use **Repositories** (`modules/shared/database/repositories/`) for all DB access.
*   **SQLAlchemy Core** is preferred over ORM for performance and explicit control.
*   **Batch Operations:** Use batch inserts/updates for large datasets (TEMU orders/inventory).

## 6. Current Status (Feb 2026)
*   **Stable:** TEMU Order/Inventory Sync, PDF Reader, Frontend Architecture (CSS Consolidation, Central Navigation).
*   **In Progress:** Migration of CSV Verarbeiter (JTL2DATEV) to the monorepo structure (`feature/csv-verarbeiter-migration`).
*   **Recent:** CSS Consolidation eliminierte 1,537 Zeilen Duplikate (44% Reduktion), Zentrale Navigation für alle Module.
