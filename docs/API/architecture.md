# 📘 TEMU Integration – Architektur-Dokumentation: API-Layer

**Status:** 🟢 STABLE / VERIFIED  
**Datum:** 23. Januar 2026  
**Bereich:** FastAPI Server, REST Endpoints, WebSocket Integration

---

## Über diesen Layer
Der API-Layer stellt die Schnittstelle zwischen dem Frontend (Web/Mobile) und der Business-Logik dar. Er basiert auf **FastAPI** (moderner als Flask/Django) mit **Uvicorn**-Server und **Starlette** Middleware.

---

## 1. Architektur & Stack

### Komponenten
```
Frontend (JavaScript/HTML)
    ↓ HTTP/WebSocket
FastAPI Server (Port 8000)
    ├── REST Endpoints (/api/...)
    ├── WebSocket Endpoints (/ws/...)
    └── Middleware (CORS, Logging, Exception Handling)
    ↓
Business Logic Layer (Services, Repositories)
    ↓
Database Layer (SQLAlchemy, Connection Pooling)
```

### Technology Stack
| Komponente | Tech | Version | Zweck |
| --- | --- | --- | --- |
| **Server** | Uvicorn | Latest | ASGI Application Server |
| **Framework** | FastAPI | 0.100+ | REST + WebSocket Framework |
| **Middleware** | Starlette | Built-in | Request/Response Processing |
| **Async** | asyncio | Python 3.12 | Concurrent Request Handling |
| **Documentation** | OpenAPI/Swagger | Auto | Interactive API Docs |

---

## 2. Server Setup & Konfiguration

**Datei:** `api/server.py`

### Initialization
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI(
    title="TEMU Integration API",
    description="Job Management & Real-time Logging",
    version="1.0.0"
)

# CORS - Allow Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ In Production: Spezifisch!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Features
- ✅ **Automatic OpenAPI Docs:** `/docs` (Swagger UI)
- ✅ **Async-First:** Alle Endpoints sind `async` für Concurrency
- ✅ **Built-in Validation:** Request/Response Schemas via Pydantic
- ✅ **Error Handling:** Automatische JSON-Error-Responses

---

## 3. REST Endpoints – Pattern & Design

### Grundmuster: Job Management
```python
from fastapi import APIRouter, HTTPException
from src.workers.worker_service import WorkerService

router = APIRouter(prefix="/api", tags=["jobs"])
worker_service = WorkerService()

@router.get("/jobs")
async def list_jobs():
    """
    GET /api/jobs
    Liefert alle Jobs mit aktuellem Status
    """
    try:
        jobs = worker_service.get_all_jobs()
        return [job.to_dict() for job in jobs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/run-now")
async def trigger_job(job_id: str, mode: str = "quick", verbose: bool = False):
    """
    POST /api/jobs/{job_id}/run-now?mode=full&verbose=true
    Triggert einen Job sofort (nicht auf Schedule warten)
    """
    params = {"mode": mode, "verbose": verbose}
    result = worker_service.trigger_job(job_id, params)
    return {"status": "triggered", "job_id": job_id, "params": params}
```

### Response Format
**Erfolg (200):**
```json
{
  "job_id": "sync_inventory_temu",
  "status": {
    "status": "success",
    "last_run": "2026-01-23T13:39:55.061887",
    "next_run": "2026-01-23T13:44:55.176602",
    "last_error": null,
    "last_duration": 0.081407
  }
}
```

**Fehler (500):**
```json
{
  "detail": "Job 'unknown_job' not found",
  "status": 404
}
```

---

## 4. WebSocket Integration – Real-time Logging

### Pattern: Live Job Monitoring
```python
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """
    WebSocket /ws/logs
    Pushes live logs & job updates an verbundene Clients
    """
    await websocket.accept()
    
    try:
        while True:
            # Sammle aktuelle Job-States
            jobs = worker_service.get_all_jobs()
            jobs_serializable = [
                {
                    "job_id": j.job_id,
                    "status": j.status.status,
                    "last_duration": j.status.last_duration,
                }
                for j in jobs
            ]
            
            # Sende an Client
            await websocket.send_json({
                "type": "jobs_update",
                "data": jobs_serializable,
                "timestamp": time.time()
            })
            
            # Update-Frequenz: 2 Sekunden
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        # Client hat sich selbst getrennt (normal)
        logger.info(f"Client disconnected from /ws/logs")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011)  # Server Error
```

### Client-Seite (JavaScript)
```javascript
const ws = new WebSocket("ws://localhost:8000/ws/logs");

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  if (msg.type === "jobs_update") {
    console.log("Job Status Update:", msg.data);
    updateJobsUI(msg.data);
  }
};

ws.onerror = () => console.error("WebSocket error");
ws.onclose = () => console.log("Connection closed");
```

### WebSocket States & Handling
| State | Bedeutung | Handling |
| --- | --- | --- |
| **CONNECTING** | Verbindung wird aufgebaut | Warten |
| **OPEN** | Verbunden, Messages fließen | Normal operation |
| **CLOSING** | Server/Client will schließen | Graceful Shutdown |
| **CLOSED** | Verbindung weg | Reconnect mit Backoff |

---

## 5. Error Handling & HTTP Status Codes

### Standard HTTP Codes
```python
@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = worker_service.find_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=404,  # Not Found
            detail=f"Job '{job_id}' does not exist"
        )
    
    if not job.is_active:
        raise HTTPException(
            status_code=423,  # Locked
            detail="Job is disabled"
        )
    
    return job.to_dict()
```

### Status Code Reference
| Code | Bedeutung | Beispiel |
| --- | --- | --- |
| **200** | OK | Erfolgreiche GET/POST |
| **202** | Accepted | Async Job gestartet |
| **400** | Bad Request | Ungültige Parameter |
| **404** | Not Found | Job existiert nicht |
| **423** | Locked | Ressource gesperrt |
| **500** | Server Error | Unerwarteter Fehler |
| **503** | Service Unavailable | DB down, Service crashed |

### Global Exception Handler
```python
from fastapi import Request
from fastapi.responses import JSONResponse
from src.services.logger import app_logger

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Fangt ALLE unkontrollierten Exceptions ab"""
    app_logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "path": str(request.url),
            "timestamp": datetime.now().isoformat()
        }
    )
```

---

## 6. Authentication & Security

### API-Key Pattern (Optional)
```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    """
    Middleware für API-Key Validierung
    """
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

@router.post("/jobs/{job_id}/run-now")
async def trigger_job(
    job_id: str,
    api_key: str = Depends(verify_api_key)
):
    # Nur wenn API-Key korrekt
    return worker_service.trigger_job(job_id)
```

### CORS Best Practices
```python
# ❌ PRODUCTION UNSICHER:
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# ✅ PRODUCTION SICHER:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://myapp.com",
        "https://www.myapp.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600  # 10 Minuten CORS Cache
)
```

---

## 7. Request/Response Validation mit Pydantic

### Model Definition
```python
from pydantic import BaseModel, Field
from typing import Optional

class JobRequest(BaseModel):
    """Validiertes Request-Schema"""
    mode: str = Field("quick", description="quick oder full")
    verbose: bool = Field(False, description="Debug Output")
    
    # Automatische Validierung:
    # - mode MUSS string sein
    # - verbose MUSS bool sein
    # Falls nicht → 422 Unprocessable Entity

class JobResponse(BaseModel):
    """Validiertes Response-Schema"""
    job_id: str
    status: str
    last_error: Optional[str] = None
    last_duration: float
```

### Verwendung
```python
@router.post("/jobs/{job_id}/run-now")
async def trigger_job(
    job_id: str,
    request: JobRequest  # ← Automatische Validierung!
):
    # request.mode ist garantiert ein String
    # request.verbose ist garantiert ein Bool
    return worker_service.trigger_job(job_id, request.dict())

# ❌ Falscher Request (422 Response):
POST /api/jobs/sync_inventory/run-now
{
  "mode": "quick",
  "verbose": "yes"  # ← String statt Bool!
}

# Response:
{
  "detail": [
    {
      "loc": ["body", "verbose"],
      "msg": "value is not a valid boolean",
      "type": "type_error.boolean"
    }
  ]
}
```

---

## 8. Performance & Optimization

### Async Best Practices
```python
# ❌ BLOCKIEREND - Nur 1 Request gleichzeitig:
@app.get("/jobs")
def list_jobs():  # ← Keine async!
    time.sleep(2)  # ← Blockiert ALLE Requests!
    return worker_service.get_all_jobs()

# ✅ NICHT-BLOCKIEREND - Viele Requests gleichzeitig:
@app.get("/jobs")
async def list_jobs():  # ← Async!
    # Nicht blockierend
    return worker_service.get_all_jobs()
```

### Connection Management
```python
from contextlib import asynccontextmanager
from src.db.connection import db_connect

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Server-Lifecycle: Setup & Teardown"""
    # Startup
    logger.info("API Server starting...")
    # Prüfe DB Connection
    with db_connect(DB_JTL) as conn:
        logger.info("✅ Database connected")
    
    yield  # Server läuft
    
    # Shutdown
    logger.info("API Server shutting down...")

app = FastAPI(lifespan=lifespan)
```

### Response Caching
```python
from fastapi import Response

@router.get("/jobs")
async def list_jobs(response: Response):
    """Cache 5 Sekunden client-side"""
    jobs = worker_service.get_all_jobs()
    
    response.headers["Cache-Control"] = "public, max-age=5"
    return jobs
```

### Request Logging
```python
from starlette.middleware.base import BaseHTTPMiddleware
import time

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        
        logger.info(
            f"{request.method} {request.url.path} "
            f"→ {response.status_code} ({duration:.3f}s)"
        )
        return response

app.add_middleware(RequestLoggingMiddleware)
```

---

## 9. API Dokumentation & Testing

### Auto-Generated OpenAPI Docs
Aktuell verfügbar unter: **http://localhost:8000/docs** (Swagger UI)

**Features:**
- Alle Endpoints automatisch dokumentiert
- Request/Response Schemas sichtbar
- "Try it Out" Button zum Testen direkt im Browser
- Alternative: http://localhost:8000/redoc (ReDoc)

### cURL Testing
```bash
# Jobs auflisten
curl http://localhost:8000/api/jobs

# Job sofort triggern
curl -X POST "http://localhost:8000/api/jobs/sync_inventory_temu/run-now?mode=full"

# Mit Parametern & Header
curl -X POST "http://localhost:8000/api/jobs/sync_orders/run-now" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret123" \
  -d '{"verbose": true}'
```

### Python Client Testing
```python
import requests
import asyncio

# Sync (requests)
response = requests.get("http://localhost:8000/api/jobs")
print(response.json())

# Async (httpx)
import httpx

async def test_api():
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://localhost:8000/api/jobs")
        print(resp.json())

asyncio.run(test_api())
```

---

## 10. Deployment Checklist

### Before Going Live
- [ ] CORS `allow_origins` auf spezifische Domains begrenzen
- [ ] API-Key oder Authentication aktivieren
- [ ] Rate Limiting implementieren
- [ ] HTTPS/SSL Zertifikat konfiguriert
- [ ] Error Logging & Monitoring eingerichtet
- [ ] Database Connection Pool optimiert
- [ ] WebSocket Timeout konfiguriert
- [ ] Request/Response Limits gesetzt
- [ ] API Docs zugänglich (oder deaktiviert)

### Environment Variables
```bash
# .env
API_PORT=8000
API_HOST=0.0.0.0
API_CORS_ORIGINS=https://myapp.com,https://www.myapp.com
API_KEY=your-secret-key-here
DATABASE_POOL_SIZE=20
LOG_LEVEL=INFO
```

### Uvicorn Startup (Production)
```bash
# Development
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn api.server:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info \
  --access-log
```

---

## Technische Parameter (Aktuell)

| Parameter | Wert | Beschreibung |
| :--- | :--- | :--- |
| **Server Port** | 8000 | HTTP Listen Port |
| **Workers** | 1 (Dev) / 4 (Prod) | Parallel Request Handler |
| **WebSocket Timeout** | Standard (60s) | Connection Keep-Alive |
| **Request Size Limit** | 100 MB | Max Upload Size |
| **CORS Origin** | * (Dev) | Spezifisch in Prod! |
| **Log Level** | DEBUG (Dev) / INFO (Prod) | Logging Verbosity |

---

## Häufig gestellte Fragen

**F: Warum async statt sync?**  
A: Async ermöglicht 100+ gleichzeitige Requests auf 1 Server. Sync = nur 1 Request gleichzeitig.

**F: Kann ich WebSocket verwenden um Files zu streamen?**  
A: Nicht empfohlen (HTTP chunked besser). WebSocket = Low-latency Messages, nicht Datei-Transfer.

**F: Wie skaliere ich auf mehrere Server?**  
A: Load Balancer (nginx) vor mehreren Uvicorn-Instanzen. Shared Redis für Session/Cache.

**F: Wie debugge ich einen WebSocket Fehler?**  
A: Browser DevTools → Network Tab → WS → Messages anschauen. Plus Logs in `pm2-error.log`.

---

> **Nächste Schritte:** Workflows-Dokumentation, Performance-Benchmarks, Deployment-Guide.
