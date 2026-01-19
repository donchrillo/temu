# Projekt-Architektur Analyse & Optimierungsplan

**Datum:** 19. Januar 2026  
**Status:** Analyse durchgeführt  
**Ziel:** Code-Doppelungen entfernen und Single Source of Truth etablieren

---

## 📊 Aktuelle Architektur (IST-Zustand)

### Einstiegspunkte (mehrfach!)

```
┌─────────────────────────────────────────────────────────┐
│                    VERSCHIEDENE EINSTIEGSPUNKTE           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. CLI: python main.py                                 │
│     └─> workflows/temu_orders.py                        │
│     └─> workflows/temu_inventory.py                     │
│                                                          │
│  2. API: uvicorn api.server:app                         │
│     └─> api/server.py (POST /api/jobs/{id}/run-now)    │
│     └─> workers/worker_service.py                      │
│                                                          │
│  3. PM2 Scheduler: pm2 start ecosystem.config.js        │
│     └─> workers/worker_service.py (SchedulerService)   │
│     └─> workers/job_models.py                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Schicht-Übersicht

```
┌─────────────────────────────────────────────────────────┐
│                   FRONTEND (PWA)                         │
│              (HTML/CSS/JS via Browser)                  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│          API LAYER (FastAPI - api/server.py)            │
│  ✓ /api/jobs (GET/POST)                                │
│  ✓ /api/jobs/{id}/run-now (POST)                       │
│  ✓ /api/logs (GET)                                     │
│  ✓ /ws/logs (WebSocket)                                │
└──────────────────────┬──────────────────────────────────┘
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
┌──────────────────────┐  ┌──────────────────────┐
│  WORKERS             │  │  WORKFLOWS           │
│  (workers/*)         │  │  (workflows/*)       │
│                      │  │                      │
│ SchedulerService  ◄──┼──┤ run_temu_orders    │
│ worker_service.py │  │  │ run_temu_inventory │
│                   │  │  │                     │
│ PM2 Scheduler     │  │  │ CLI Entry Points   │
│ job_models.py     │  │  │ (REDUNDANT!)       │
└──────────────────┬─┘  └────┬─────────────────┘
                   │          │
         ┌─────────┴──────────┤
         ▼                    ▼
┌──────────────────────────────────────────────────────────┐
│         BUSINESS LOGIC SERVICES (src/modules/temu/)      │
│                                                          │
│  OrderWorkflowService                                   │
│  InventoryWorkflowService                               │
│  OrderService                                           │
│  InventoryService                                       │
│  TrackingService                                        │
│  StockSyncService                                       │
│  (+ Marketplace Connectors, Repositories)              │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│          DATABASE & EXTERNAL APIs                        │
│  (SQL Server, TEMU API, JTL)                            │
└──────────────────────────────────────────────────────────┘
```

---

## 🔴 Identifizierte Probleme

### 1. **Mehrfache Einstiegspunkte = Code-Dopplung**

| Pfad | Zustand | Problem |
|------|---------|---------|
| `main.py` | ✓ funktioniert | Wird wahrscheinlich nicht verwendet |
| `workflows/temu_*.py` | ✓ funktioniert | Nur Wrapper, echte Logik ist woanders |
| `api/server.py` | ✓ funktioniert | Der Haupteinstiegspunkt |
| `workers/worker_service.py` | ✓ funktioniert | Scheduler - ruft Workflows/Services auf |

**Folge:** 
- Drei verschiedene Wege um die gleiche Logik auszuführen
- Wenn man den Code in einem Ort ändert, muss man ihn möglicherweise an drei Orten ändern
- Wartungsmerkmallos!

### 2. **Workflows sind nur Wrapper (tatsächliche Redundanz)**

**workflows/temu_inventory.py:**
```python
def run_temu_inventory(mode: str = "quick", verbose: bool = False) -> bool:
    service = InventoryWorkflowService()
    return service.run_complete_workflow(mode=mode, verbose=verbose)
```

**workers/worker_service.py:**
```python
elif job_type == JobType.SYNC_INVENTORY:
    from src.modules.temu.inventory_workflow_service import InventoryWorkflowService
    service = InventoryWorkflowService()
    result = await self._async_wrapper(
        service.run_complete_workflow,
        mode=mode,
        verbose=verbose
    )
```

**Problem:** Beide tun das GLEICHE, nur auf unterschiedliche Wege!

### 3. **main.py ist möglicherweise obsolet**

`main.py` hat einen CLI-Parser aber lädt nur `workflows/`, die selbst nur Wrapper sind. Wenn man die App über CLI starten möchte, muss man:
- `python main.py` verwenden (CLI)
- ODER `pm2 start ecosystem.config.js` (Production mit Scheduler)

**Frage:** Braucht man noch main.py? Wird es überhaupt verwendet?

### 4. **Scheduler vs. API - Zwei verschiedene Execution-Modi**

| Mode | Trigger | Ausführung | Zustand |
|------|---------|-----------|---------|
| **API** | HTTP POST `/api/jobs/{id}/run-now` | Immediate | Synchron |
| **Scheduler** | PM2 Timer-basiert | Geplant | Asynchron via Workers |

**Problem:** 
- API triggert direkt den Worker
- Worker nutzt die gleiche Logik wie der Scheduler
- Code wird möglicherweise in beiden Kontexten unterschiedlich ausgeführt

---

## ✅ Optimierungsplan (SOLL-Zustand)

### Ziel: Single Source of Truth

```
UNIFIED ENTRY POINT ARCHITECTURE
═════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────┐
│                   FRONTEND (PWA)                        │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│          API LAYER (FastAPI - api/server.py)            │
│      === EINZIGER EINSTIEGSPUNKT ===                   │
│  ✓ /api/jobs (GET)           ← Jobs auflisten         │
│  ✓ /api/jobs/{id}/run-now (POST) ← Job SOFORT starten │
│  ✓ /api/jobs/{id}/schedule (POST) ← Job planen        │
│  ✓ /api/logs (GET)           ← Logs abfragen          │
│  ✓ /ws/logs (WebSocket)      ← Live Updates           │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│     JOB EXECUTOR SERVICE (neu)                          │
│     src/services/job_executor.py                        │
│                                                         │
│  execute_job(job_id, job_type, params, mode)          │
│  └─> Einheitliche Ausführung für ALLE Quellen        │
│      - API-Anfrage                                    │
│      - Scheduler/PM2                                  │
│      - CLI (optional)                                 │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│      BUSINESS LOGIC SERVICES (src/modules/temu/)        │
│                                                         │
│  OrderWorkflowService.run_complete_workflow()          │
│  InventoryWorkflowService.run_complete_workflow()      │
│  (+ andere Services wie bisher)                       │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│      DATABASE & EXTERNAL APIs                           │
└──────────────────────────────────────────────────────────┘
```

### Konkrete Schritte

#### **Phase 1: Job Executor Service erstellen**

**Datei:** `src/services/job_executor.py`

```python
"""Einheitlicher Job Executor für alle Ausführungskontexte"""

from enum import Enum
from typing import Dict, Any
from src.modules.temu.order_workflow_service import OrderWorkflowService
from src.modules.temu.inventory_workflow_service import InventoryWorkflowService

class JobType(str, Enum):
    SYNC_ORDERS = "sync_orders"
    SYNC_INVENTORY = "sync_inventory"

class JobExecutor:
    """Zentrale Stelle für alle Job-Ausführungen"""
    
    async def execute(
        self, 
        job_id: str,
        job_type: JobType,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Führe einen Job aus - unabhängig von der Quelle
        
        Quellen:
        - API (/api/jobs/{id}/run-now)
        - Scheduler (PM2 timer)
        - CLI (python main.py) - OPTIONAL
        
        Returns:
            {
                "success": bool,
                "job_id": str,
                "result": Any,
                "duration": float
            }
        """
        if job_type == JobType.SYNC_ORDERS:
            service = OrderWorkflowService()
            return await service.run_complete_workflow(
                parent_order_status=kwargs.get('parent_order_status', 2),
                days_back=kwargs.get('days_back', 7),
                verbose=kwargs.get('verbose', False)
            )
        
        elif job_type == JobType.SYNC_INVENTORY:
            service = InventoryWorkflowService()
            return await service.run_complete_workflow(
                mode=kwargs.get('mode', 'quick'),
                verbose=kwargs.get('verbose', False)
            )
        
        else:
            raise ValueError(f"Unknown job type: {job_type}")
```

#### **Phase 2: API anpassen**

**Datei:** `api/server.py`

```python
# VORHER
from workers.worker_service import SchedulerService
scheduler = SchedulerService()

# NACHHER
from src.services.job_executor import JobExecutor
executor = JobExecutor()

@app.post("/api/jobs/{job_id}/run-now")
async def trigger_job(job_id: str, ...):
    """Triggere Job SOFORT"""
    result = await executor.execute(
        job_id=job_id,
        job_type=JobType.SYNC_ORDERS,
        parent_order_status=parent_order_status,
        days_back=days_back,
        verbose=verbose
    )
    return result
```

#### **Phase 3: Worker anpassen**

**Datei:** `workers/worker_service.py`

```python
# STATT direktem Aufruf:
#   service = OrderWorkflowService()
#   result = service.run_complete_workflow(...)

# NEU:
from src.services.job_executor import JobExecutor
executor = JobExecutor()

result = await executor.execute(
    job_id=job_id,
    job_type=job.config.job_type,
    **job.config.parameters
)
```

#### **Phase 4: CLI optional (rückwärts-kompatibel)**

**Option A:** main.py behalten (für Entwickler)
```python
# main.py nutzt Job Executor
from src.services.job_executor import JobExecutor

def run(args):
    executor = JobExecutor()
    result = executor.execute(
        job_id=f"cli_{int(time.time())}",
        job_type=args.job_type,
        **vars(args)
    )
    return result
```

**Option B:** main.py komplett entfernen
- Production verwendet ohnehin PM2/API
- CLI-Nutzer können `curl` verwenden oder `main.py` selbst schreiben

#### **Phase 5: Workflows vereinfachen/entfernen**

```python
# workflows/temu_orders.py und temu_inventory.py können:
# A) Komplett gelöscht werden (nicht mehr verwendet)
# B) Zu einfachen CLI-Wrappern werden (für Rückwärtskompatibilität)
# C) Als Legacy-Module gekennzeichnet werden
```

---

## 📋 Was würde sich ändern?

### Vorher (Aktuell):

1. **API ruft Worker auf:**
   ```
   api/server.py → workers/worker_service.py → OrderWorkflowService
   ```

2. **Scheduler ruft Workflow auf:**
   ```
   workers/worker_service.py → workflows/temu_orders.py → OrderWorkflowService
   ```

3. **CLI ruft Workflow auf:**
   ```
   main.py → workflows/temu_orders.py → OrderWorkflowService
   ```

### Nachher (Optimiert):

1. **Alle rufen Job Executor auf:**
   ```
   api/server.py
   workers/worker_service.py    } → JobExecutor → OrderWorkflowService
   main.py (optional)
   ```

---

## 🎯 Vorteile der Optimierung

| Vorteil | Beschreibung |
|---------|-------------|
| **Single Source of Truth** | Job-Logik nur an EINER Stelle |
| **Weniger Dopplung** | Workflows/main.py können gelöscht/vereinfacht werden |
| **Leichter zu warten** | Code-Änderungen nur an einem Ort nötig |
| **Konsistente Ausführung** | Egal ob API/Scheduler/CLI - gleiche Logik |
| **Besseres Testing** | Nur JobExecutor testen, nicht 3 Wege |
| **Klarer Code Flow** | Einstiegspunkt → JobExecutor → Services |

---

## 🤔 Fragen für Dich

1. **Wird `main.py` noch verwendet?** Oder kann das weg?
2. **Sollen CLI-Befehle weiterhin funktionieren?** (`python main.py --status 2 --days 7`)
3. **Ist Production immer über API+PM2?** Oder wird CLI auch in Production genutzt?
4. **Können wir `workflows/` ganz löschen?** Oder braucht man Legacy-Support?

---

## 📝 Nächste Schritte

Wenn du die Architektur so optimieren möchtest:

1. ✅ Schritt 1: `JobExecutor` in `src/services/job_executor.py` erstellen
2. ✅ Schritt 2: `api/server.py` anpassen um JobExecutor zu nutzen
3. ✅ Schritt 3: `workers/worker_service.py` anpassen
4. ✅ Schritt 4: `main.py` und `workflows/` nach Bedarf anpassen/löschen
5. ✅ Schritt 5: Tests aktualisieren
6. ✅ Schritt 6: Commit & Push

**Sollen wir anfangen?** 🚀
