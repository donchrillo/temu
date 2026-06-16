# TEMU ERP - API Architecture

Status: STABLE / VERIFIED
Last checked: 2026-03-12
Scope: FastAPI Gateway, REST APIs, WebSocket, Router composition

---

## 1. Purpose and Scope

This document describes the active API architecture in the repository.
Source of truth is runtime code, primarily `main.py` and the routers under `modules/*` and `workers/*`.

The system uses one unified FastAPI gateway and includes domain routers for:
- PDF processing
- TEMU integration
- CSV processing
- Job scheduling
- Logs
- WebSocket live updates

---

## 2. Runtime Topology

```text
React Frontend (Vite dev: :3000 / build: frontend-react/dist)
        |
        | HTTP + WebSocket
        v
FastAPI Gateway (main.py)
        |- /api/pdf/*        (modules/pdf_reader/router.py)
        |- /api/temu/*       (modules/temu/router.py)
        |- /api/csv/*        (modules/csv_verarbeiter/router.py)
        |- /api/jobs/*       (workers/jobs_router.py)
        |- /api/logs/*       (modules/shared/routers/log_router.py)
        |- /ws/logs          (modules/shared/routers/websocket_router.py)
        |- /assets, /icons   (modules/shared/routers/static_router.py)
        |- /, /pdf, /temu... (modules/shared/routers/ui_router.py)
        v
Services / repositories / workflows / DB access
```

---

## 3. Gateway Configuration

Primary file: `main.py`

Key points:
- FastAPI app with lifespan startup/shutdown logic.
- Startup validation via `validate_startup_config()`.
- Scheduler lifecycle managed by `SchedulerService`.
- CORS currently open (`allow_origins=["*"]`) for development.
- API docs mounted at:
  - `/api/docs`
  - `/api/redoc`
- Health endpoint:
  - `GET /api/health`

Port usage:
- Development API port: `8888` (`start_dev.sh`)
- Production templates/reference often use port `8401` (deploy level)

---

## 4. Router Composition (Current)

### Domain routers
- `app.include_router(get_pdf_router(), prefix="/api/pdf", tags=["PDF Processor"])`
- `app.include_router(get_temu_router(), prefix="/api/temu", tags=["TEMU Integration"])`
- `app.include_router(csv_router, prefix="/api/csv", tags=["CSV Verarbeiter"])`

### Shared/system routers
- Logs router: `get_log_router()` -> `/api/logs/*`
- Jobs router: `get_jobs_router(scheduler)` -> `/api/jobs/*`
- WebSocket router: `get_websocket_router(...)` -> `/ws/logs`
- UI router: `get_ui_router(frontend_dir)` -> `/`, `/pdf`, `/temu`, `/csv`, `/docs`, `/manifest.json`
- Static assets: `get_static_router(app, frontend_dir)` -> `/assets`, `/icons`

---

## 5. Important Endpoint Groups

### Gateway/system
- `GET /api/health`
- `GET /api/docs`
- `GET /api/redoc`

### Jobs (`workers/jobs_router.py`)
- `GET /api/jobs`
- `GET /api/jobs/{job_id}`
- `POST /api/jobs/{job_id}/run-now`
- `POST /api/jobs/{job_id}/schedule`
- `POST /api/jobs/{job_id}/toggle`

### WebSocket
- `WS /ws/logs` sends `{"type": "jobs_update", "data": ...}` roughly every 2 seconds.

### Logs (`modules/shared/routers/log_router.py`)
- `GET /api/logs`
- `GET /api/logs/stats`
- `GET /api/logs/export`
- `POST /api/logs/cleanup`

### PDF (`modules/pdf_reader/router.py`)
- Health/status, upload/process/result flows for `werbung` and `rechnungen`
- Input guards include file extension and max upload size checks

### TEMU (`modules/temu/router.py`)
- Health/info/stats
- Manual sync trigger endpoints (`/orders/sync`, `/inventory/sync`)

### CSV (`modules/csv_verarbeiter/router.py`)
- Health/status/upload/process/result/report style endpoints for DATEV CSV workflows

---

## 6. Frontend Integration

Development:
- React app runs separately on `:3000`.
- API served by FastAPI on `:8888`.

Built frontend:
- Gateway can serve static build files from `frontend-react/dist`.
- UI fallback routes (`/`, `/pdf`, `/temu`, `/csv`) return `index.html` when build is present.

---

## 7. Security and Operational Notes

Current state:
- CORS is open for development convenience.
- No global API-key enforcement at gateway level.
- Validation and error handling are mainly endpoint-local.

Recommended production hardening:
- Restrict CORS origins.
- Add auth/authz where needed.
- Keep scheduler as single-process ownership where required by deployment model.

---

## 8. Known Transition Area

`modules/temu_datev/` exists as an imported transition module (subtree).
It is not yet fully integrated into the primary gateway and frontend structure.

---

## 9. Verification Checklist

This document is considered up-to-date if all checks still pass:
- `main.py` still defines one FastAPI gateway.
- Router prefixes match section 4.
- Docs URLs remain `/api/docs` and `/api/redoc`.
- Dev startup still uses port `8888` in `start_dev.sh`.
- WebSocket path remains `/ws/logs`.

If one check fails, update this file and `docs/AGENT_CHANGES.md`.
