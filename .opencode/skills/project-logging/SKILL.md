---
name: project-logging
description: DB-basiertes strukturiertes Logging-System für TEMU/TOCI ERP mit Job-Tracking und Error-Handling.
---

# 🗄️ DB-basiertes Logging-System

## Philosophie
**Traditionelle File-Logs sind veraltet.**  
Dieses Projekt nutzt **DB-basiertes strukturiertes Logging** für bessere Nachvollziehbarkeit, Filterung und Analyse.

## Zentrale Komponenten

### 1. log_service.py (`modules/shared/logging/`)
**Zentrale LogService Klasse** - Speichert ALLE Logs in SQL Server

**Strukturierte Felder:**
- `job_id` — Eindeutige Workflow-Instanz (für Tracking)
- `job_type` — z.B. "order_workflow", "inventory_workflow"
- `level` — INFO, WARNING, ERROR
- `message` — Lesbare Nachricht (kurz, aktiv)
- `status` — SUCCESS, FAILED, TIMEOUT (am Ende gesetzt)
- `duration_seconds` — Performance Metric
- `error_text` — Stack Trace bei Fehler (getrennt von message)

**Features:**
- In-Memory Buffer für Performance
- Nur ERROR-Level schreibt zusätzlich in `app.log` (Fallback)
- Job-Lifecycle Management

### 2. logger.py (`modules/shared/logging/`)
**Fallback File Logger** - nur für unerwartete Fehler

- Console Handler: stderr (ERROR+)
- File Handler: `logs/{log_subdir}/{file_name}`
- Wird nur genutzt wenn DB-Connection fehlschlägt

## Job-Lifecycle Pattern

```python
# 1. Start Job
job_id = self._generate_job_id("component_name")
log_service.start_job_capture(job_id, "component_name")
# → Status: RUNNING, Buffer leer

# 2. Log Steps (beliebig oft)
log_service.log(job_id, "component_name", "INFO", "→ Starte Verarbeitung")
log_service.log(job_id, "component_name", "INFO", "[1/5] TEMU API → JSON")
log_service.log(job_id, "component_name", "INFO", "[2/5] Validierung")
# → Jeder Log in DB + In-Memory Buffer

# 3. End Job
duration = (datetime.now() - start_time).total_seconds()
log_service.end_job_capture(success=True, duration=duration)
# → Status: SUCCESS/FAILED, Buffer flushed
```

## Implementierungs-Pattern

### Vollständiges Beispiel: Order Workflow

```python
from datetime import datetime
import traceback
from modules.shared.logging.log_service import log_service

class OrderWorkflowService:
    def process_order(self, order_data: dict) -> dict:
        """Process order with structured logging."""
        job_id = self._generate_job_id("order_workflow")
        start_time = datetime.now()
        
        # 1. Start Job Capture
        log_service.start_job_capture(job_id, "order_workflow")
        
        try:
            # 2. Log Steps
            log_service.log(job_id, "order_workflow", "INFO", "→ Starte Order Processing")
            
            # Step 1: API Call
            log_service.log(job_id, "order_workflow", "INFO", "[1/5] TEMU API → JSON")
            raw_data = self._fetch_from_api(order_data['order_id'])
            
            # Step 2: Validation
            log_service.log(job_id, "order_workflow", "INFO", "[2/5] Validierung")
            validated_data = self._validate_order(raw_data)
            
            # Step 3: Transform
            log_service.log(job_id, "order_workflow", "INFO", "[3/5] Transformation")
            transformed = self._transform_data(validated_data)
            
            # Step 4: Database
            log_service.log(job_id, "order_workflow", "INFO", "[4/5] DB Import")
            order_id = self._save_to_database(transformed)
            
            # Step 5: Notification
            log_service.log(job_id, "order_workflow", "INFO", "[5/5] Notification")
            self._send_notification(order_id)
            
            log_service.log(job_id, "order_workflow", "INFO", f"✓ Order {order_id} erfolgreich verarbeitet")
            
            # 3. End Job (Success)
            duration = (datetime.now() - start_time).total_seconds()
            log_service.end_job_capture(success=True, duration=duration)
            
            return {"status": "success", "order_id": order_id}
            
        except ValidationError as e:
            # Partial Failure → WARNING
            log_service.log(
                job_id, 
                "order_workflow", 
                "WARNING", 
                f"⚠ Validierung fehlgeschlagen: {str(e)}"
            )
            duration = (datetime.now() - start_time).total_seconds()
            log_service.end_job_capture(success=False, duration=duration, error=str(e))
            raise
            
        except Exception as e:
            # Critical Failure → ERROR
            error_trace = traceback.format_exc()
            log_service.log(
                job_id, 
                "order_workflow", 
                "ERROR", 
                f"✗ Kritischer Fehler: {str(e)}",
                error_text=error_trace
            )
            duration = (datetime.now() - start_time).total_seconds()
            log_service.end_job_capture(success=False, duration=duration, error=str(e))
            raise
    
    def _generate_job_id(self, component: str) -> str:
        """Generate unique job ID."""
        import uuid
        return f"{component}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
```

## Log-Level Guidelines

### ✅ INFO
**Verwendung:** Normale Workflow-Steps, erfolgreiche Operationen

**Beispiele:**
```python
log_service.log(job_id, "workflow", "INFO", "→ Starte Verarbeitung")
log_service.log(job_id, "workflow", "INFO", "[1/5] API Call erfolgreich")
log_service.log(job_id, "workflow", "INFO", "✓ 150 Orders importiert")
```

### ⚠️ WARNING
**Verwendung:** Partial Failures, nicht-kritische Fehler, Fallback-Logic

**Beispiele:**
```python
log_service.log(job_id, "workflow", "WARNING", "⚠ 5/150 Orders fehlgeschlagen (Validation)")
log_service.log(job_id, "workflow", "WARNING", "⚠ API Slow (5s), nutze Cache")
log_service.log(job_id, "workflow", "WARNING", "⚠ Duplicate Order ID, überspringe")
```

**NICHT für:**
- ❌ Normale Fehler die Workflow stoppen → ERROR
- ❌ Debug-Informationen → gar nicht loggen in Production

### 🚨 ERROR
**Verwendung:** Kritische Fehler die Workflow stoppen

**Beispiele:**
```python
log_service.log(
    job_id, 
    "workflow", 
    "ERROR", 
    f"✗ DB Connection failed: {str(e)}",
    error_text=traceback.format_exc()
)
log_service.log(
    job_id, 
    "workflow", 
    "ERROR", 
    "✗ API Authentication failed (401)"
)
```

**WICHTIG:**
- Immer mit `error_text=traceback.format_exc()` für Stack Trace
- Message kurz halten (nur was schief ging)
- Stack Trace NUR in `error_text`, NICHT in `message`

## Messaging-Konventionen

### ✅ GOOD Messages

```python
# Aktive Verben, kurz, klar
"→ Starte Verarbeitung"
"[1/5] TEMU API → JSON"
"✓ 150 Orders importiert"
"⚠ 5/150 Orders fehlgeschlagen"
"✗ DB Connection failed"

# Mit Kontext
"[2/5] Validierung: 150 Orders, 5 warnings"
"✓ Order #12345 erfolgreich verarbeitet (2.3s)"
```

### ❌ BAD Messages

```python
# Zu lang
"Starting the order processing workflow for TEMU marketplace integration..."

# Zu vague
"Processing..."
"Error"
"Something went wrong"

# Stack Trace in Message
"Error: Traceback (most recent call last):\n  File..."  # → error_text nutzen!

# Passive
"Order was processed"  # → "✓ Order verarbeitet"
```

### Message-Präfixe

- `→` — Aktion startet
- `[N/M]` — Step N von M
- `✓` — Erfolg
- `⚠` — Warning
- `✗` — Fehler

## Job-Correlation

**Alle Logs eines Workflows haben gleiche `job_id`** für Tracing:

```python
# API Call loggt:
job_id = "order_workflow_20260215_143022_a1b2c3d4"

# Worker loggt:
log_service.log(job_id, "order_workflow", "INFO", "[1/5] API Call")

# Service loggt:
log_service.log(job_id, "order_workflow", "INFO", "[2/5] Validation")

# Database loggt:
log_service.log(job_id, "order_workflow", "INFO", "[3/5] DB Import")

# → Alle tracebar durch job_id
```

## Error-Handling Pattern

```python
try:
    # Business Logic
    result = some_operation()
    
except ValidationError as e:
    # Erwartet, nicht kritisch → WARNING
    log_service.log(
        job_id, 
        "component", 
        "WARNING", 
        f"⚠ Validation failed: {str(e)}"
    )
    # Ggf. Fallback-Logic
    result = fallback_value
    
except APIError as e:
    # Erwartet, kritisch → ERROR
    log_service.log(
        job_id,
        "component",
        "ERROR",
        f"✗ API Error: {str(e)}",
        error_text=traceback.format_exc()
    )
    # Re-raise für Error-Handler
    raise
    
except Exception as e:
    # Unerwartet → ERROR
    log_service.log(
        job_id,
        "component",
        "ERROR",
        f"✗ Unexpected error: {str(e)}",
        error_text=traceback.format_exc()
    )
    raise

finally:
    # Immer Job-Status setzen
    duration = (datetime.now() - start_time).total_seconds()
    log_service.end_job_capture(
        success=not error_occurred,
        duration=duration,
        error=error_message if error_occurred else None
    )
```

## Performance-Tracking

```python
# Gesamte Workflow-Duration
start_time = datetime.now()
# ... processing ...
duration = (datetime.now() - start_time).total_seconds()
log_service.end_job_capture(success=True, duration=duration)

# Step-Duration (Optional für Performance-Analyse)
step_start = datetime.now()
result = expensive_operation()
step_duration = (datetime.now() - step_start).total_seconds()
log_service.log(
    job_id,
    "component",
    "INFO",
    f"[3/5] Expensive Operation completed ({step_duration:.2f}s)"
)
```

## Sicherheits-Guidelines

### ✅ DO Log:
- Order IDs, Customer IDs (Business Context)
- Error Messages
- Performance Metrics
- Workflow Steps

### ❌ DON'T Log:
- API Keys (`TEMU_APP_KEY`)
- Passwords
- Credit Card Numbers
- Auth Tokens
- Full Stack Traces in `message` (nur in `error_text`)

```python
# ❌ BAD
log_service.log(job_id, "api", "INFO", f"Calling API with key: {api_key}")

# ✅ GOOD
log_service.log(job_id, "api", "INFO", "→ TEMU API Call")
```

## Audit-Checkliste

Beim Schreiben von neuem Code prüfe:

1. ✅ **Job-ID durchgängig:** Alle Logs eines Workflows haben gleiche `job_id`
2. ✅ **Job-Lifecycle:** `start_job_capture()` → `log()` → `end_job_capture()`
3. ✅ **Level korrekt:** INFO für Normal, WARNING für Partial Failure, ERROR für Critical
4. ✅ **Messages klar:** Aktive Verben, kurz, Präfixe nutzen
5. ✅ **Status gesetzt:** `end_job_capture()` mit `success` und `duration`
6. ✅ **Error-Text getrennt:** Stack Trace in `error_text`, nicht in `message`
7. ✅ **Keine Secrets:** API-Keys, Passwords nicht loggen
8. ✅ **Performance:** Duration gemessen und geloggt

## Häufige Fehler

### ❌ Kein Job-ID
```python
# BAD: Logs nicht tracebar
log_service.log(None, "component", "INFO", "Processing...")
```

### ❌ Falsche Level
```python
# BAD: Normale Operation als ERROR
log_service.log(job_id, "component", "ERROR", "Order processed")

# GOOD:
log_service.log(job_id, "component", "INFO", "✓ Order processed")
```

### ❌ Stack Trace in Message
```python
# BAD:
try:
    ...
except Exception as e:
    log_service.log(
        job_id, 
        "component", 
        "ERROR", 
        f"Error: {traceback.format_exc()}"  # ❌
    )

# GOOD:
log_service.log(
    job_id,
    "component",
    "ERROR",
    f"✗ Error: {str(e)}",
    error_text=traceback.format_exc()  # ✅
)
```

### ❌ Kein end_job_capture()
```python
# BAD: Status bleibt "RUNNING"
log_service.start_job_capture(job_id, "component")
# ... processing ...
# ❌ Kein end_job_capture()

# GOOD:
try:
    log_service.start_job_capture(job_id, "component")
    # ... processing ...
    log_service.end_job_capture(success=True, duration=duration)
except:
    log_service.end_job_capture(success=False, duration=duration, error=str(e))
```

## Integration mit anderen Services

### Mit Repository Pattern
```python
class OrderRepository:
    def __init__(self, connection, log_job_id: str = None):
        self.connection = connection
        self.log_job_id = log_job_id
    
    def create(self, order: Order) -> int:
        if self.log_job_id:
            log_service.log(
                self.log_job_id,
                "order_repository",
                "INFO",
                f"→ Creating order in DB: {order.external_id}"
            )
        
        # DB Logic
        order_id = self._insert(order)
        
        if self.log_job_id:
            log_service.log(
                self.log_job_id,
                "order_repository",
                "INFO",
                f"✓ Order created: ID={order_id}"
            )
        
        return order_id
```

### Mit Worker-Services
```python
class TemuWorker:
    def run_sync_job(self):
        job_id = self._generate_job_id("temu_sync")
        log_service.start_job_capture(job_id, "temu_sync")
        
        try:
            # Pass job_id to services
            orders = self.order_service.fetch_orders(job_id)
            self.order_service.process_orders(orders, job_id)
            
            log_service.end_job_capture(success=True, duration=duration)
        except Exception as e:
            log_service.log(job_id, "temu_sync", "ERROR", f"✗ Sync failed: {str(e)}", error_text=traceback.format_exc())
            log_service.end_job_capture(success=False, duration=duration, error=str(e))
```

## Unterschied zu Dokumentations-Logging

**Wichtig:** Dieses Skill beschreibt das **interne technische Logging** (DB-basiert).  
Das ist **NICHT** das gleiche wie die **Change Documentation** in `docs/AGENT_CHANGES.md`.

| Aspekt | Internes Logging (DB) | Change Documentation (MD) |
|--------|----------------------|---------------------------|
| Zweck | Runtime-Monitoring | Change-Tracking |
| Ziel | SQL Server Database | `docs/AGENT_CHANGES.md` |
| Verwendung | `log_service.log()` | Manueller Eintrag |
| Wer | Produktions-Code | Agenten nach Code-Änderung |
| Skill | **project-logging** | **agent-change-documentation** |
