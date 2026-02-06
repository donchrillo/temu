# 📘 TEMU Integration – Architektur-Dokumentation: Workflows

**Status:** 🟢 STABLE / VERIFIED  
**Datum:** 5. Februar 2026  
**Bereich:** Job Orchestrierung, APScheduler, PM2 Integration

---

## Über diesen Layer
Der Workflows-Layer orchestriert längerlaufende, asynchrone Tasks (Inventory Sync, Order Import, etc.). Er kombiniert **APScheduler** (In-Process Scheduling) mit **PM2** (Process Manager) für Reliability, Monitoring und Auto-Restart.

---

## 1. Job System – Architektur Übersicht

### Komponenten
```
PM2 Process Manager (temu-api)
    ↓
FastAPI Server (Port 8000)
    ↓ (Trigger via /api/jobs/:id/run-now)
APScheduler (In-Memory Job Scheduler)
    ├── Scheduled Jobs (Cron)
    └── Triggered Jobs (On-Demand)
    ↓
Worker Service (Job Executor)
    ↓
Business Logic (Workflows)
    ├── InventoryWorkflowService
    ├── OrderWorkflowService
    └── TrackingWorkflowService
    ↓
Database Layer (Transactional)
```

### Job States & Transitions
```
┌─────────────┐
│ NOT_STARTED │
└──────┬──────┘
       │ (schedule triggered / manual trigger)
       ↓
┌──────────────┐
│   RUNNING    │
└──────┬───────┘
       │
    ┌──┴────────────────────┐
    ↓                       ↓
┌──────────┐          ┌──────────┐
│ SUCCESS  │          │  FAILED  │
└──────────┘          └──────────┘
    ↑                       ↑
    └───────────┬───────────┘
                │ (retry)
         ┌──────▼──────┐
         │  RETRYING   │
         └─────────────┘
```

### Status Object (Pro Job)
```python
{
    "status": "success|failed|running|scheduled",
    "last_run": "2026-01-23T13:39:55.061887",     # ISO Timestamp
    "next_run": "2026-01-23T13:44:55.176602",     # Nächste geplante Zeit
    "last_error": null,                            # Exception Message oder null
    "last_duration": 0.081407,                     # Ausführungszeit in Sekunden
    "retry_count": 0,                              # Aktuelle Retry-Nummer
    "max_retries": 3                               # Maximale Retrys
}
```

---

## 2. APScheduler Integration

**Datei:** `workers/worker_service.py` + `workers/config/workers_config.json`

### Initialization
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

class WorkerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler(
            daemon=True,  # Wird mit Hauptprozess beendet
            timezone='Europe/Berlin'
        )
        self.jobs_config = self._load_config()
        self._init_jobs()
    
    def _load_config(self):
        """Lädt Job-Konfiguration aus workers_config.json"""
        with open('workers/config/workers_config.json') as f:
            return json.load(f)
    
    def _init_jobs(self):
        """Registriert alle konfigurierten Jobs"""
        for job_config in self.jobs_config:
            self._add_scheduled_job(job_config)
        self.scheduler.start()
```

### Job Configuration (workers_config.json)
```json
[
  {
    "job_id": "sync_inventory_temu",
    "name": "TEMU Inventory Sync",
    "schedule": {
      "type": "cron",
      "hour": "9-21",
      "minute": "*/5",
      "day_of_week": "0-6"
    },
    "default_params": {
      "mode": "quick",
      "verbose": false
    },
    "timeout_seconds": 120,
    "max_retries": 3,
    "retry_delay_seconds": 30,
    "enabled": true
  },
  {
    "job_id": "sync_orders_temu",
    "name": "TEMU Orders Sync",
    "schedule": {
      "type": "cron",
      "hour": "*",
      "minute": "*/10"
    },
    "default_params": {
      "parent_order_status": 2,
      "days_back": 7
    },
    "timeout_seconds": 180,
    "max_retries": 2,
    "retry_delay_seconds": 60,
    "enabled": true
  }
]
```

### Cron Schedule Erklärung
```
Field          Range        Description
─────────────────────────────────────────
minute         0-59         Minute der Stunde
hour           0-23         Stunde des Tages
day_of_month   1-31         Tag des Monats
month          1-12         Monat
day_of_week    0-6          Tag der Woche (0=Sonntag)

Beispiele:
"minute": "*/5"        → Alle 5 Minuten
"hour": "9,17"         → 09:00 und 17:00
"hour": "9-21"         → Von 9 bis 21 Uhr
"day_of_week": "1-5"   → Montag bis Freitag (Mo=1, Fr=5)
```

### Scheduled Job Registration
```python
def _add_scheduled_job(self, job_config):
    """Registriert einen Cron-Job"""
    job_id = job_config["job_id"]
    schedule = job_config["schedule"]
    
    # Erstelle Trigger aus Config
    trigger = CronTrigger(
        hour=schedule.get("hour", "*"),
        minute=schedule.get("minute", "0"),
        day_of_week=schedule.get("day_of_week", "*"),
        timezone='Europe/Berlin'
    )
    
    self.scheduler.add_job(
        func=self._execute_job,
        trigger=trigger,
        args=[job_id, job_config["default_params"]],
        id=job_id,
        name=job_config["name"],
        max_instances=1,  # Nur 1x gleichzeitig
        replace_existing=True,
        misfire_grace_time=10  # Toleranz bei Verzögerung
    )
```

---

## 3. PM2 Integration

**Datei:** `ecosystem.config.js`

### PM2 Configuration
```javascript
module.exports = {
  apps: [
    {
      name: 'temu-api',
      script: 'main.py',
      interpreter: '/home/chx/temu/.venv/bin/python',
      watch: false,  // Don't auto-restart on file changes
      max_memory_restart: '1G',  // Auto-restart wenn > 1GB RAM
      error_file: './logs/pm2-error.log',
      out_file: './logs/pm2-out.log',
      log_file: './logs/pm2.log',
      time: true,  // Timestamps in Logs
      env: {
        NODE_ENV: 'production',
        LOG_LEVEL: 'INFO'
      }
    }
  ],
  deploy: {
    production: {
      user: 'chx',
      host: 'localhost',
      ref: 'origin/main',
      repo: 'git@github.com:...',
      path: '/home/chx/temu',
      script: 'main.py',
      'pre-deploy-local': '',
      'post-deploy': 'npm install && npm run build',
      'pre-deploy': 'echo "Deploying to production server"',
      'exec-mode': 'cluster'
    }
  }
};
```

### PM2 Commands
```bash
# Start
pm2 start ecosystem.config.js

# Monitor
pm2 monit                    # Live Dashboard
pm2 logs temu-api            # Stream Logs
pm2 logs temu-api --lines 50 # Last 50 lines

# Restart
pm2 restart temu-api
pm2 reload temu-api          # Graceful (0-downtime)

# Status
pm2 list
pm2 show temu-api

# Stop/Delete
pm2 stop temu-api
pm2 delete temu-api

# Autostart on boot
pm2 startup
pm2 save
```

### Log Management
```bash
# PM2 logs automatisch rotieren
pm2 install pm2-logrotate

# Konfiguration
pm2 conf pm2-logrotate "{\"max_size\": \"100M\", \"retain\": 30}"
# → Max 100MB pro Datei, 30 Tage behalten
```

---

## 4. Job Models & State Management

**Datei:** `workers/job_models.py`

### Job Model
```python
from dataclasses import dataclass, asdict
from typing import Dict, Any
from datetime import datetime

@dataclass
class JobStatus:
    """Status eines Jobs"""
    status: str  # "success", "failed", "running", "scheduled"
    last_run: str  # ISO Timestamp
    next_run: str  # ISO Timestamp
    last_error: str = None
    last_duration: float = 0.0
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class Job:
    """Vollständiges Job-Objekt"""
    job_id: str
    name: str
    status: JobStatus
    enabled: bool = True
    schedule_config: Dict[str, Any] = None
    
    def to_dict(self):
        """Konvertiert zu Dict für API-Response"""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "status": asdict(self.status),
            "enabled": self.enabled
        }
    
    def is_running() -> bool:
        return self.status.status == "running"
    
    def mark_started(self):
        self.status.status = "running"
        self.status.last_run = datetime.now().isoformat()
    
    def mark_success(self, duration: float):
        self.status.status = "success"
        self.status.last_error = None
        self.status.last_duration = duration
        self.status.retry_count = 0
    
    def mark_failed(self, error: str):
        self.status.status = "failed"
        self.status.last_error = error
```

### State Persistence (Optional)
```python
import json
from pathlib import Path

class JobStateManager:
    """Speichert Job-States zwischen Restarts"""
    STATE_FILE = Path("./data/jobs_state.json")
    
    @classmethod
    def save_state(cls, jobs: Dict[str, Job]):
        """Speichert Job-Status als JSON"""
        state = {
            job_id: {
                "status": job.status.status,
                "last_run": job.status.last_run,
                "last_error": job.status.last_error,
                "last_duration": job.status.last_duration
            }
            for job_id, job in jobs.items()
        }
        cls.STATE_FILE.write_text(json.dumps(state, indent=2))
    
    @classmethod
    def load_state(cls) -> Dict[str, dict]:
        """Lädt gespeicherte Job-Status"""
        if cls.STATE_FILE.exists():
            return json.loads(cls.STATE_FILE.read_text())
        return {}
```

---

## 5. Worker Service Pattern

**Datei:** `workers/worker_service.py`

### Job Execution
```python
def _execute_job(self, job_id: str, params: Dict[str, Any]):
    """Führt einen Job aus (von APScheduler)"""
    job = self.get_job(job_id)
    if not job:
        logger.error(f"Job {job_id} not found")
        return
    
    if job.is_running():
        logger.warning(f"Job {job_id} is already running, skipping")
        return
    
    try:
        start_time = time.time()
        job.mark_started()
        
        # Rufe Workflow auf
        result = self._execute_workflow(job_id, params)
        
        duration = time.time() - start_time
        job.mark_success(duration)
        logger.info(f"Job {job_id} completed in {duration:.2f}s")
        
    except Exception as e:
        job.mark_failed(str(e))
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        
        # Retry-Logik
        self._schedule_retry(job_id, params)

def _execute_workflow(self, job_id: str, params: Dict[str, Any]):
    """Delegate an entsprechende Workflow-Klasse"""
    if "inventory" in job_id:
        from modules.temu.services.inventory_workflow_service import InventoryWorkflowService
        workflow = InventoryWorkflowService()
        return workflow.run_complete_workflow(
            mode=params.get("mode", "quick"),
            verbose=params.get("verbose", False)
        )
    elif "order" in job_id:
        from modules.temu.services.order_workflow_service import OrderWorkflowService
        workflow = OrderWorkflowService()
        return workflow.run_complete_workflow(**params)
    else:
        raise ValueError(f"Unknown job type: {job_id}")
```

### Manual Job Trigger (via API)
```python
def trigger_job(self, job_id: str, params: Dict[str, Any]) -> bool:
    """Triggert einen Job sofort (nicht auf Schedule warten)"""
    job = self.get_job(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")
    
    # Führe im Thread-Pool aus (non-blocking)
    from concurrent.futures import ThreadPoolExecutor
    executor = ThreadPoolExecutor(max_workers=5)
    executor.submit(self._execute_job, job_id, params)
    
    return True
```

### Retry Logic
```python
def _schedule_retry(self, job_id: str, params: Dict[str, Any]):
    """Plant einen Retry nach exponentieller Backoff"""
    job = self.get_job(job_id)
    if job.status.retry_count >= job.status.max_retries:
        logger.error(f"Job {job_id} max retries exceeded")
        return
    
    job.status.retry_count += 1
    delay = 2 ** job.status.retry_count  # 2s, 4s, 8s ...
    
    logger.info(f"Scheduling retry {job.status.retry_count} for {job_id} in {delay}s")
    
    from datetime import datetime, timedelta
    retry_time = datetime.now() + timedelta(seconds=delay)
    
    self.scheduler.add_job(
        func=self._execute_job,
        trigger='date',
        run_date=retry_time,
        args=[job_id, params],
        id=f"{job_id}_retry_{job.status.retry_count}",
        replace_existing=True
    )
```

---

## 6. Workflow Orchestrierung – Praktische Beispiele

### Inventory Workflow (4 Schritte, 3 Blöcke)
```python
from modules.temu.services.inventory_workflow_service import InventoryWorkflowService

class InventoryWorkflow:
    """4-Schritt Orchestrierung (Transaction Splitting)"""
    
    def run_complete_workflow(self, mode: str = "quick") -> bool:
        """
        Vollständiger Bestandabgleich (in Blöcke unterteilt für Stabilität):
        
        Block 1: Import (Optional)
        1. TEMU API → JSON (Fetch SKU-Liste)
        2. JSON → TOCI (Import in Datenbank, Commit)
        
        Block 2: JTL Update
        3. JTL Bestand → TOCI (Lookup JTL-Stock, Commit)
        
        Block 3: API Sync
        4. TOCI → TEMU API (Update Stock, Commit nach jedem Batch)
        """
        
        # --- BLOCK 1: IMPORT ---
        if mode == "full":
            logger.info("[1/4] Fetching SKU list from TEMU API...")
            api_data = self._step_1_fetch_api()
            
            with db_connect(DB_TOCI) as toci_conn:
                logger.info("[2/4] Importing SKUs into TOCI...")
                result = self._step_2_json_to_db(toci_conn)
                logger.info(f"✓ Inserted: {result['inserted']}, Updated: {result['updated']}")
            # Commit Block 1
        
        # --- BLOCK 2: JTL UPDATE ---
        with db_connect(DB_TOCI) as toci_conn:
            with db_connect(DB_JTL) as jtl_conn:
                logger.info("[3/4] Fetching stock from JTL...")
                self._step_3_jtl_to_inventory(jtl_conn, toci_conn)
        # Commit Block 2

        # --- BLOCK 3: API SYNC ---
        with db_connect(DB_TOCI) as toci_conn:
            logger.info("[4/4] Pushing stock to TEMU API...")
            # Intern: Loop über GoodsID, API Call, dann sofortiges DB-Update
            updated = self._step_4_update_temu_api(toci_conn)
            logger.info(f"✓ Sync Process finished")
        # Commit Block 3
        
        return True
```

### Order Workflow
```python
class OrderWorkflowService:
    """Order Import mit Tracking-Lookup"""
    
    def run_complete_workflow(self, parent_order_status: int = 2, days_back: int = 7) -> bool:
        """
        1. Fetch Orders von TEMU API
        2. Parse & Import in TOCI
        3. Lookup Tracking Info von JTL
        4. Update Order Status
        """
        
        with db_connect(DB_TOCI) as toci_conn:
            with db_connect(DB_JTL) as jtl_conn:
                
                # Step 1: Fetch
                logger.info("[1/4] Fetching orders from TEMU API...")
                orders = self._fetch_orders(parent_order_status, days_back)
                
                # Step 2: Import
                logger.info(f"[2/4] Importing {len(orders)} orders...")
                self._import_orders(orders, toci_conn)
                
                # Step 3: Tracking Lookup
                logger.info("[3/4] Looking up tracking info from JTL...")
                self._enrich_with_tracking(orders, jtl_conn)
                
                # Step 4: Update Status
                logger.info("[4/4] Updating order status...")
                self._update_order_status(orders, toci_conn)
                
                return True
```

---

## 7. Error Handling & Retry Logic

### Strukturiertes Error Handling
```python
class JobException(Exception):
    """Base Exception für Job-Fehler"""
    def __init__(self, message: str, recoverable: bool = True):
        self.message = message
        self.recoverable = recoverable
        super().__init__(self.message)

class RetryableJobException(JobException):
    """Fehler, der automatisch retried werden soll"""
    def __init__(self, message: str):
        super().__init__(message, recoverable=True)

class FatalJobException(JobException):
    """Fehler, der nicht retried werden soll"""
    def __init__(self, message: str):
        super().__init__(message, recoverable=False)

# Verwendung
try:
    api_response = call_temu_api()
except requests.ConnectionError as e:
    raise RetryableJobException(f"API Connection failed: {e}")
except requests.HTTPError as e:
    if e.response.status_code == 401:
        raise FatalJobException("Invalid API credentials")
    else:
        raise RetryableJobException(f"HTTP {e.response.status_code}")
```

### Retry Strategy
```python
import time
from functools import wraps

def with_retries(max_retries: int = 3, backoff_base: int = 2):
    """Decorator für automatische Retrys"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except RetryableJobException as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = backoff_base ** (attempt - 1)
                        logger.warning(
                            f"Attempt {attempt}/{max_retries} failed, "
                            f"retrying in {delay}s: {e.message}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed")
            
            raise last_exception
        return wrapper
    return decorator

# Verwendung
@with_retries(max_retries=3, backoff_base=2)
def fetch_api_data():
    response = requests.get("https://api.temu.com/...", timeout=10)
    response.raise_for_status()
    return response.json()
```

---

## 8. Monitoring & Health Checks

### Job Monitoring
```python
def get_job_health_status(self) -> Dict[str, Any]:
    """Health-Status für Monitoring"""
    now = datetime.now()
    health = {
        "timestamp": now.isoformat(),
        "jobs": {},
        "overall": "healthy"
    }
    
    for job_id, job in self.jobs.items():
        last_run_time = datetime.fromisoformat(job.status.last_run) if job.status.last_run else None
        time_since_run = (now - last_run_time).total_seconds() if last_run_time else None
        
        job_health = {
            "status": job.status.status,
            "last_duration": job.status.last_duration,
            "time_since_last_run": time_since_run,
            "is_overdue": False
        }
        
        # Prüfe ob Job überällig ist
        next_run_time = datetime.fromisoformat(job.status.next_run) if job.status.next_run else None
        if next_run_time and now > next_run_time:
            job_health["is_overdue"] = True
            health["overall"] = "warning"
        
        if job.status.status == "failed":
            health["overall"] = "unhealthy"
        
        health["jobs"][job_id] = job_health
    
    return health
```

### Metrics & Alerts
```python
from modules.shared.logging.logger import app_logger

def log_job_metrics(self, job_id: str, duration: float, success: bool):
    """Logs Job-Metriken für Monitoring"""
    metric = {
        "job_id": job_id,
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": duration,
        "success": success,
        "status": "success" if success else "failed"
    }
    
    # Log als structuierter Metric (für ELK/Prometheus)
    app_logger.info(f"JOB_METRIC: {json.dumps(metric)}")
    
    # Optional: Sende zu Monitoring-System
    if duration > 60:  # Warn wenn > 1 Minute
        app_logger.warning(f"Job {job_id} took {duration:.1f}s (slow)")
    
    if duration > 300:  # Error wenn > 5 Minuten
        app_logger.error(f"Job {job_id} took {duration:.1f}s (very slow)")
```

---

## 9. Scaling & High Availability

### Multi-Instance Setup (mit Load Balancer)
```javascript
// ecosystem.config.js - Cluster Mode
module.exports = {
  apps: [
    {
      name: 'temu-api',
      script: 'main.py',
      interpreter: '/home/chx/temu/.venv/bin/python',
      instances: 4,  // ← 4 Worker-Prozesse
      exec_mode: 'cluster',  // ← Cluster Mode (mit Load Balancer)
      max_memory_restart: '1G'
    }
  ]
};
```

### Distributed Scheduler (mit Redis)
```python
# Für Production: APScheduler mit externem Scheduler
# Verhindert doppelte Ausführung bei mehreren Instances
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

schedulers = BackgroundScheduler({
    'apscheduler.jobstores.default': RedisJobStore(),
    'apscheduler.executors.default': ThreadPoolExecutor(max_workers=20),
    'apscheduler.timezone': 'Europe/Berlin'
})
# → Jobs werden nur auf EINEM Instance ausgeführt
```

---

## 10. Production Deployment Checklist

### Pre-Deployment
- [ ] Alle Jobs testen im Dev/Staging
- [ ] Cron-Expressions validieren (mit crontab.guru)
- [ ] Timeout-Werte realistisch setzen
- [ ] Retry-Strategie testen (mit künstlichem Fehler)
- [ ] Logs & Error Handling konfiguriert
- [ ] Database Connection Pool optimiert
- [ ] Max-Workers für ThreadPool konfiguriert

### Deployment
- [ ] PM2 `ecosystem.config.js` deployed
- [ ] `pm2 startup` ausgeführt (Auto-Restart on Boot)
- [ ] `pm2 save` ausgeführt (Persistent Config)
- [ ] Log Rotation konfiguriert (`pm2-logrotate`)
- [ ] Monitoring Tools angebunden (New Relic, DataDog, etc.)

### Post-Deployment
- [ ] Logs monitoren für Fehler
- [ ] Job-Ausführung im ersten Zyklus prüfen
- [ ] Alerting für Failed Jobs testen
- [ ] Health Check Endpoint verfügbar
- [ ] Rollback-Plan für Fehler

### Monitoring & Alerting
```bash
# Dashboard aufrufen
pm2 monit

# Logs live folgen
pm2 logs temu-api --lines 50 --follow

# Status prüfen
pm2 list

# Health Check API
curl http://localhost:8000/api/health
```

---

## Technische Parameter (Aktuell)

| Parameter | Wert | Beschreibung |
| :--- | :--- | :--- |
| **Scheduler Type** | APScheduler (Background) | In-Process Scheduling |
| **Max Concurrent Jobs** | 1 | Nur ein Job gleichzeitig |
| **Default Max Retries** | 3 | Automatische Retrys |
| **Retry Backoff** | Exponential (2^n) | 2s, 4s, 8s ... |
| **Job Timeout** | Job-spezifisch | 120-300s Timeout |
| **Thread Pool Workers** | 5 | Parallel Job Execution |
| **PM2 Max Memory** | 1 GB | Auto-Restart bei Überschuss |
| **Log Rotation** | Daily | Mit pm2-logrotate |

---

## Häufig gestellte Fragen

**F: Was passiert wenn ein Job länger läuft als sein Timeout?**  
A: Job wird als failed markiert, Error wird geloggt. Retry-Logik greift.

**F: Können mehrere Jobs gleichzeitig laufen?**  
A: Aktuell: Nein (max_instances=1). Mit Redis möglich, braucht aber weitere Config.

**F: Wie teste ich Cron-Expressions?**  
A: Nutze https://crontab.guru/ oder Python `croniter` Modul.

**F: Was wenn der PM2 Prozess crasht?**  
A: `pm2 startup` sorgt für Auto-Restart. Außerdem `pm2 save` persistent.

**F: Wie scale ich auf mehrere Server?**  
A: Redis JobStore + APScheduler Distributed Mode (verhindert doppelte Ausführung).

---

> **Nächste Schritte:** DEPLOYMENT-Dokumentation, PERFORMANCE-Benchmarks, Monitoring-Integration.