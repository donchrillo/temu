# Workers - Job Scheduler Module

## Überblick

Das `workers/` Modul verwaltet alle **geplanten Background-Jobs** für Marketplace-Integrationen. Es nutzt **APScheduler** (AsyncIO-basiert) für zeitgesteuerte Aufgaben.

## Aktuelle Jobs (Februar 2026)

### TEMU Marketplace

| Job Type | Beschreibung | Intervall | Modul |
|----------|-------------|-----------|-------|
| `SYNC_ORDERS` | Bestellungen synchronisieren (5-Schritt Workflow) | 5 Min | `modules.temu.services.order_workflow_service` |
| `SYNC_INVENTORY` | Lagerbestände abgleichen (4-Schritt Workflow) | 5 Min | `modules.temu.services.inventory_workflow_service` |

### Andere Marketplaces

**Aktuell:** Noch nicht implementiert

**Geplant:**
- Amazon (Order Sync, Inventory Sync, Tracking)
- Ebay (Order Sync, Inventory Sync)
- Kaufland (Order Sync, Inventory Sync)
- Otto (Order Sync, Inventory Sync)

## Architektur

### Dateien

```
workers/
├── README.md              ← Diese Datei
├── worker_service.py      ← APScheduler Service (Job-Verwaltung)
├── job_models.py          ← Job-Typen (Enum), Status, Config Models
├── workers_config.py      ← Config-Loader (lädt/speichert Jobs)
└── config/
    └── workers_config.json  ← Persistierte Job-Konfigurationen
```

### Workflow

1. **Initialisierung:** `SchedulerService.initialize_from_config()` lädt Jobs aus `workers_config.json`
2. **Ausführung:** APScheduler ruft `_run_job()` im konfigurierten Intervall auf
3. **Logging:** Alle Job-Logs werden in SQL Server (`scheduler_logs` Tabelle) gespeichert
4. **WebSocket:** Job-Status wird live an Frontend gesendet
5. **Persistierung:** Job-Konfiguration wird automatisch gespeichert

## Neuen Job hinzufügen

### Schritt 1: Job-Typ definieren

Bearbeite `job_models.py`:

```python
class JobType(str, Enum):
    SYNC_ORDERS = "order_workflow"
    SYNC_INVENTORY = "inventory_workflow"
    FETCH_INVOICES = "fetch_invoices"

    # NEU: Amazon Job
    AMAZON_SYNC_ORDERS = "amazon_order_workflow"  # ← Hinzufügen
```

### Schritt 2: Service-Logik erstellen

Erstelle z.B. `modules/amazon/services/order_workflow_service.py`:

```python
class AmazonOrderWorkflowService:
    def run_complete_workflow(self, ...):
        # Deine Amazon-Logik hier
        pass
```

### Schritt 3: Job in Scheduler registrieren

Bearbeite `worker_service.py` → `_run_job()`:

```python
elif job_type == JobType.AMAZON_SYNC_ORDERS:
    from modules.amazon.services.order_workflow_service import AmazonOrderWorkflowService
    service = AmazonOrderWorkflowService()
    result = await self._async_wrapper(
        service.run_complete_workflow,
        # Parameter hier
    )
```

### Schritt 4: Job hinzufügen (via API oder Code)

**Via API:**
```bash
curl -X POST http://localhost:8000/api/jobs/add \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "amazon_order_workflow",
    "interval_minutes": 10,
    "description": "Amazon Bestellungen synchronisieren",
    "enabled": true
  }'
```

**Via Code (beim Start):**
```python
scheduler.add_job(
    job_type=JobType.AMAZON_SYNC_ORDERS,
    interval_minutes=10,
    description="Amazon Bestellungen synchronisieren",
    enabled=True
)
```

## Job-Status

Jobs durchlaufen folgende Stati:

- `IDLE` - Wartet auf nächste Ausführung
- `RUNNING` - Wird gerade ausgeführt
- `SUCCESS` - Erfolgreich abgeschlossen
- `FAILED` - Mit Fehler beendet

## Logging

Alle Job-Logs werden strukturiert gespeichert:

**Datenbank:** `scheduler_logs` Tabelle in TOCI
- `job_id` - Eindeutige Job-Ausführungs-ID
- `job_type` - Typ des Jobs (z.B. "order_workflow")
- `level` - Log-Level (INFO, WARNING, ERROR)
- `message` - Log-Nachricht
- `timestamp` - Zeitstempel

**WebSocket:** Live-Updates an Frontend (`/ws/logs`)

**Log-Service:**
```python
from modules.shared.logging.log_service import log_service

log_service.start_job_capture(job_id, job_type)
log_service.log(job_id, job_type, "INFO", "Job gestartet")
log_service.end_job_capture(success=True, duration=10.5)
```

## Konfiguration

### Job-Konfiguration (workers_config.json)

```json
{
  "jobs": [
    {
      "job_type": "order_workflow",
      "interval_minutes": 5,
      "enabled": true,
      "description": "TEMU Bestellungen synchronisieren"
    }
  ]
}
```

### Job-Parameter

Jobs können mit individuellen Parametern getriggert werden:

```python
scheduler.trigger_job_now(
    job_id="temu_orders_123",
    parent_order_status=2,  # Nur Status 2 (paid)
    days_back=7,            # Letzte 7 Tage
    verbose=False,
    mode="quick"            # Für Inventory: quick/full
)
```

## Best Practices

### 1. Transaktions-Management

**Splitte kritische Operationen in separate Transaktionen:**

```python
# BLOCK 1: Import (kritisch - neue Daten)
with db_connect(DB_TOCI) as conn:
    import_orders(conn)
    # Auto-Commit beim Verlassen

# BLOCK 2: Tracking (unkritisch - Updates)
with db_connect(DB_TOCI) as conn:
    update_tracking(conn)
    # Unabhängiger Commit
```

### 2. Fehlerbehandlung

**Fange Fehler und logge sie strukturiert:**

```python
try:
    result = process_orders()
    log_service.log(job_id, job_type, "INFO", f"✓ {result['count']} Orders verarbeitet")
except Exception as e:
    log_service.log(job_id, job_type, "ERROR", f"✗ Fehler: {str(e)}")
    log_service.end_job_capture(success=False, error=str(e))
    raise  # Re-raise für APScheduler
```

### 3. Idempotenz

**Jobs sollten idempotent sein** (mehrfaches Ausführen = gleiches Ergebnis):

- Prüfe vor Import, ob Daten bereits existieren
- Nutze `INSERT ... ON DUPLICATE KEY UPDATE` oder `MERGE`
- Vermeide doppelte API-Aufrufe durch Caching

### 4. Timeouts

**Setze sinnvolle Timeouts:**

```python
# Für lange laufende Jobs
max_instances=1,          # Nur 1 Instanz gleichzeitig
misfire_grace_time=None,  # Ignoriere verpasste Zyklen
coalesce=True             # Springe verpasste Ausführungen
```

## Monitoring

### PM2 Logs

```bash
# Live-Logs anzeigen
pm2 logs temu-api

# Letzte 50 Zeilen
pm2 logs temu-api --lines 50

# Nach Job-Typ filtern
pm2 logs temu-api | grep order_workflow
```

### Datenbank-Abfragen

```sql
-- Letzte 10 Jobs
SELECT TOP 10 * FROM scheduler_logs
ORDER BY timestamp DESC

-- Fehler heute
SELECT * FROM scheduler_logs
WHERE level = 'ERROR'
  AND CAST(timestamp AS DATE) = CAST(GETDATE() AS DATE)

-- Job-Dauer Statistik
SELECT
    job_type,
    AVG(duration_seconds) as avg_duration,
    MAX(duration_seconds) as max_duration
FROM scheduler_logs
WHERE status = 'SUCCESS'
GROUP BY job_type
```

### Frontend

Öffne `http://localhost:8000/temu` für Live-Monitoring:
- Job-Status in Echtzeit
- Log-Filtering nach Job-Typ
- Manuelle Job-Trigger
- Intervall-Anpassung

## Zukünftige Erweiterungen

### Multi-Marketplace Strategie

**Geplante Struktur:**

```
modules/
├── temu/              ✅ Implementiert
│   └── services/
├── amazon/            🔜 Geplant
│   └── services/
├── ebay/              🔜 Geplant
│   └── services/
├── kaufland/          🔜 Geplant
│   └── services/
└── otto/              🔜 Geplant
    └── services/
```

Alle Marketplaces nutzen:
- `modules/shared/database/` für DB-Zugriff
- `modules/shared/logging/` für strukturiertes Logging
- `modules/jtl/xml_export/` für JTL-Integration
- `workers/` für Job-Scheduling

### Geplante Features

- [ ] Job-Priorisierung (high/medium/low)
- [ ] Conditional Jobs (nur wenn neue Daten vorhanden)
- [ ] Job-Chains (Job A → Job B → Job C)
- [ ] Retry-Mechanismus mit Exponential Backoff
- [ ] Prometheus Metrics für Monitoring

---

**Letzte Aktualisierung:** 3. Februar 2026
**Maintainer:** System Admin + AI Development Team
