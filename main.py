"""
Unified API Gateway - TEMU ERP System

Kombiniert alle Module:
- PDF-Reader (modules/pdf_reader)
- TEMU Integration (modules/temu)
- Job Scheduler (workers)
- Shared Services (modules/shared)

Läuft auf Port 8000
"""

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

# Root zum Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent))

# ═══════════════════════════════════════════════════════════════
# Imports
# ═══════════════════════════════════════════════════════════════

from workers.worker_service import SchedulerService
from modules.shared import app_logger
from modules.shared.startup.validation import validate_startup_config

# Module imports
from modules.pdf_reader import get_router as get_pdf_router
from modules.temu import get_router as get_temu_router
from modules.csv_verarbeiter.router import router as csv_router

# Router Imports (extrahiert)
from modules.shared.routers.static_router import get_static_router
from modules.shared.routers.log_router import get_log_router
from modules.shared.routers.ui_router import get_ui_router
from modules.shared.routers.websocket_router import get_websocket_router
from workers.jobs_router import get_jobs_router

# ═══════════════════════════════════════════════════════════════
# Scheduler
# ═══════════════════════════════════════════════════════════════

scheduler = SchedulerService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup und Shutdown Events"""
    
    # Startup Validation (Fail-Fast)
    errors = validate_startup_config()
    if errors:
        for err in errors:
            app_logger.error(f"Startup Validation Error: {err}")
    
    app_logger.info("Startup validation passed")
    
    try:
        scheduler.initialize_from_config()
        scheduler.start()
        app_logger.info("Scheduler gestartet")
    except Exception as e:
        app_logger.error(f"Fehler beim Starten des Schedulers: {e}", exc_info=True)
        raise

    yield

    try:
        scheduler.stop()
        app_logger.info("Scheduler gestoppt")
    except Exception as e:
        app_logger.error(f"Fehler beim Stoppen des Schedulers: {e}", exc_info=True)

# ═══════════════════════════════════════════════════════════════
# FastAPI App
# ═══════════════════════════════════════════════════════════════

# Frontend-Verzeichnis (wird für Static Files benötigt)
frontend_dir = Path(__file__).resolve().parent / "frontend-react" / "dist"

# Hinweis: In Entwicklung läuft das React-Frontend separat auf Port 3000 (Vite)
# Der API-Server auf Port 8000 liefert nur die API-Endpunkte aus

app = FastAPI(
    title="TEMU ERP System",
    description="Unified API Gateway für PDF-Processing & TEMU Integration",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════
# Module einbinden (include_router)
# ═══════════════════════════════════════════════════════════════

# PDF-Reader Modul
app.include_router(
    get_pdf_router(),
    prefix="/api/pdf",
    tags=["PDF Processor"]
)

# TEMU Modul
app.include_router(
    get_temu_router(),
    prefix="/api/temu",
    tags=["TEMU Integration"]
)

# CSV Verarbeiter Modul
app.include_router(
    csv_router,
    prefix="/api/csv",
    tags=["CSV Verarbeiter"]
)

# Log Router (extrahiert)
app.include_router(get_log_router())

# Job Router (extrahiert)
app.include_router(get_jobs_router(scheduler))

# ═══════════════════════════════════════════════════════════════
# Static Files (FastAPI StaticFiles)
# ═══════════════════════════════════════════════════════════════

get_static_router(app, frontend_dir)

# ═══════════════════════════════════════════════════════════════
# Health & Root Endpoints
# ═══════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health():
    """Gateway Health Check"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "modules": ["pdf-reader", "temu", "csv-verarbeiter"]
    }

# UI Router (extrahiert)
app.include_router(get_ui_router(frontend_dir))

# WebSocket Router (extrahiert)
app.include_router(get_websocket_router(lambda: scheduler))

# ═══════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )