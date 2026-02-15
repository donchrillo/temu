# 📊 SHARED SKILL: TOCI ERP LOGGING STANDARD

Jeder Code-Agent (Backend/Frontend) MUSS diesen Standard bei jeder Code-Erstellung implementieren.




## 🛠️ CORE LOGGING GUIDELINES
1. **Frontend-to-Backend Tracing:** Ensure React 19 Error Boundaries send stack traces to `/api/logs/error`.
2. **Job Correlation:** Every async task must carry its `job_id` from the UI to the DB-Log.
3. **Structured Data:** Logs must use structured fields (status, duration, job_type), not just plain strings.
4. **Resilience:** If DB logging fails, ensure `app_logger` (RotatingFileHandler) captures the fallback.

---
# 📚 LEGACY ARCHITECTURE (Existing Knowledge)

Dieses Projekt nutzt **DB-basiertes strukturiertes Logging** (nicht traditionelle File Logs):

### ZENTRALES SYSTEM: `modules/shared/logging/`

1. **log_service.py** — Zentrale LogService Klasse
   - Speichert ALLE Logs in SQL Server (Datenbank)
   - Strukturierte Felder: `job_id`, `job_type`, `level`, `message`, `status`, `duration_seconds`, `error_text`
   - In-Memory Buffer für Performance
   - Nur ERROR-Level schreibt zusätzlich in `app.log`
   - Job-Lifecycle: `start_job_capture()` → `log()` (beliebig oft) → `end_job_capture()`

2. **logger.py** — Fallback File Logger
   - Generische Logger Factory für Module
   - Console Handler: stderr (ERROR+)
   - File Handler: logs/{log_subdir}/{file_name}
   - Wird nur für unerwartete Fehler genutzt (DB-Connection Fehler)

### VERWENDUNG IM PROJEKT

**Order Workflow Beispiel:**
```python
log_service.start_job_capture(job_id, "order_workflow")
log_service.log(job_id, "order_workflow", "INFO", "[1/5] TEMU API → JSON")
# ... Steps 1-5 ...
log_service.end_job_capture(success=True, duration=0.5)
```

**Job Lifecycle:**
- `start_job_capture(job_id, job_type)` — Status: RUNNING, Buffer leer
- `log(job_id, type, level, msg)` — Jede Aktion, in DB + Buffer
- `end_job_capture(success, duration, error)` — Status: SUCCESS/FAILED

### AUDIT-FOKUS

1. **Job-Correlation**: Alle Logs eines Workflows haben gleiche `job_id` ✅
   - Allows tracing von API Call → Worker → Workflow Step 1-5
   
2. **Strukturierte Felder** in DB (nicht string-based):
   - `job_id` — Eindeutige Workflow-Instanz
   - `job_type` — "order_workflow", "inventory_workflow", etc.
   - `level` — INFO, WARNING, ERROR (wird in Code KORREKT gesetzt)
   - `message` — Lesbar, kurz, aktiv (verben: "Importiere", "Aktualisiere")
   - `status` — Am Ende: SUCCESS, FAILED, TIMEOUT
   - `duration_seconds` — Performance Metric
   - `error_text` — Stack Trace bei Fehler

3. **ERROR HANDLING**:
   - Fehler in Datenbank speichern (via `log_service.log(..., level="ERROR")`)
   - Zusätzlich in `app.log` schreiben (Fallback wenn DB-Connection weg)
   - Stack Trace via `traceback.format_exc()` erfasst

4. **PERFORMANCE TRACKING**:
   - Jeder Workflow hat `duration_seconds` am Ende
   - Steps sollten auch Dauer haben (future: micro-timing)

5. **SICHERHEIT**:
   - ✅ Kein API-Key Logging (TEMU_APP_KEY ist nicht in Logs)
   - ✅ Keine Passwords
   - ⚠️ PII Check: Order-IDs, Best-IDs werden geloggt (ist OK für Business-Logs)

### AUDIT-CRITERIA

**GOOD Logs:**
- ✅ Job-ID durchgängig
- ✅ Level korrekt (WARNING für Partial Failures, ERROR für echte Fehler)
- ✅ Messaging klar & kurz
- ✅ Status am Ende gesetzt
- ✅ Duration gemessen

**BAD Logs:**
- ❌ Kein job_id (können nicht getrackt werden)
- ❌ Alle Logs sind ERROR (Alarm Fatigue)
- ❌ DEBUG-Level Messages in Production Code
- ❌ Stack Trace in message statt error_text
- ❌ Status nicht gesetzt

### VERBESSERUNGEN

Wenn du eine Komponente auditierst, prüfe:
1. Wird `log_service` (nicht `logger`) für Business Logs verwendet?
2. Hat jeder Workflow `job_id` durchgehend?
3. Sind Log-Levels konsistent (WARNING ≠ ERROR für nicht-kritisch)?
4. Wird `end_job_capture()` mit Status/Duration aufgerufen?
5. Fehler mit Stack Trace in `error_text`, nicht in `message`?

### IMPLEMENTIERUNGS-PATTERN

```python
# Start
job_id = self._generate_job_id("component_name")
log_service.start_job_capture(job_id, "component_name")

# Steps
log_service.log(job_id, "component_name", "INFO", "→ Starte Verarbeitung")
try:
    # ... Geschäftslogik ...
except Exception as e:
    log_service.log(job_id, "component_name", "ERROR", f"✗ Fehler: {str(e)}", error_text=traceback.format_exc())
    raise

# Ende
duration = (datetime.now() - start_time).total_seconds()
log_service.end_job_capture(success=True, duration=duration)
```
---
