# docs/AGENT_CHANGES.md

# Agent Change Log

Dieses Dokument wird automatisch von Agenten gefüllt, wenn sie Änderungen vornehmen.
Der Dokumentations-Agent verarbeitet diese Einträge regelmäßig.

## Format
Jeder Agent dokumentiert seine Änderungen in folgendem Format:

---
### [DATUM] - [AGENT-NAME]
**Modul/Datei:** `pfad/zur/datei.py`
**Art der Änderung:** [Refactoring|Bug Fix|Security|Performance|Feature]
**Beschreibung:** Kurzbeschreibung der Änderung
**Details:**
- Bullet point 1
- Bullet point 2
**Betroffene Dokumentation:**
- [ ] API-Docs aktualisieren
- [ ] Architecture-Docs überarbeiten
- [ ] README.md anpassen
---

## Pending Changes (Noch nicht dokumentiert)

---
### 2026-02-14 - Codereview-Agent (GitHub Copilot)
**Modul/Datei:** `modules/jtl/xml_export/xml_export_service.py`
**Art der Änderung:** Bug Fix (Critical)
**Beschreibung:** Silent Data Loss durch ET.Element.append() behoben — append() VERSCHIEBT Elemente statt zu kopieren
**Details:**
- `import copy` hinzugefügt
- 3x `root.append(bestellung_elem)` → `root.append(copy.deepcopy(bestellung_elem))` in:
  - `_import_to_jtl()` (Zeile 372)
  - `_archive_order_to_docs()` (Zeile 440)
  - `_save_xml_to_db()` (Zeile 463)
- Ohne Fix: Gesamt-XML (`_save_xml_to_disk`) enthielt nur die LETZTE Bestellung, da vorherige append()-Aufrufe das Element aus dem Original-Tree entfernten
**Betroffene Dokumentation:**
- [ ] API-Docs aktualisieren
- [ ] Architecture-Docs überarbeiten
- [ ] README.md anpassen
---

---
### 2026-02-14 - Codereview-Agent (GitHub Copilot)
**Modul/Datei:** `modules/jtl/xml_export/xml_export_service.py`
**Art der Änderung:** Security + Performance + Code Quality (Prio 2)
**Beschreibung:** 8 Review-Findings aus Code-Review umgesetzt
**Details:**
- 🔴 XML Control-Character Sanitization: `_prettify_xml()` entfernt jetzt illegale Chars (0x00-0x08, 0x0B, 0x0C, 0x0E-0x1F, 0x7F) via Regex vor minidom-Parsing — verhindert Crash bei Kundendaten mit Control-Chars
- 🔴 `import traceback` von inline (2x) nach Top-Level verschoben
- 🟡 Magic Number `1.19` → Konstante `VERSAND_MWST_SATZ = 19.0` mit berechneter Formel `(1 + VERSAND_MWST_SATZ / 100)`
- 🟡 Kundennummer-Cache begrenzt auf 1000 Einträge (`_CUSTOMER_CACHE_MAXSIZE`) — verhindert unbegrenztes Memory-Wachstum
- 🟡 `str(filepath)` entfernt — Path-Objekte funktionieren direkt mit `open()` (2 Stellen)
- 🔵 Redundantes `else` nach `return` entfernt in `export_to_xml()`
**Betroffene Dokumentation:**
- [ ] API-Docs aktualisieren
- [ ] Architecture-Docs überarbeiten
- [ ] README.md anpassen
---

## Processed Changes (Bereits dokumentiert)

---
### 2026-02-13 - GitHub Copilot (Verarbeitet: 13. Feb 2026)
**Modul/Datei:** `modules/pdf_reader/`
**Art der Änderung:** Refactoring + Security + Bug Fix
**Beschreibung:** Umfassende Refactorings + kritische Security-Fixes im PDF-Reader
**Details:**
- Konsolidierte Betrags-Parsing Logik in `services/amount_utils.py` (parse_amount + find_value_after_labels)
- Zerlegt große Extraktionsfunktionen in Helper (Rechnungen + Werbung), reduzierte Verschachtelung
- `werbung_extraction_service.py` vereinfacht (Helper `_is_werbung_pdf`, `_extract_first_page`)
- Router DRY: gemeinsame Helper für Process/Result Endpoints (`_run_process_job`, `_get_result_file`)
- Security Fix: Path Traversal Schutz + PDF-Only Uploads + 50MB Größenlimit
- Bug Fixes: `extract_text()` None-safe; Async Endpoints laufen via Thread-Pool; MwSt-Calc ohne IT-Default-Fallback
- **Dokumentiert in:** CURRENT_STATUS.md, ARCHITECTURE/code_structure.md, modules/pdf_reader/README.md
---

---
### 2026-02-13 - RefactoringAgent (Verarbeitet: 13. Feb 2026)
**Modul/Datei:** `modules/temu/services/order_service.py`
**Art der Änderung:** Refactoring
**Beschreibung:** Priority 1 - God Method aufgelöst - 120-Zeilen `import_from_api_response()` in 5 fokussierte Funktionen zerlegt
**Details:**
- Extracted 4 helper functions: `_parse_shipping_data()`, `_parse_amount_data()`, `_upsert_order()`, `_upsert_order_items()`
- Main method reduziert von 120 auf ~40 Zeilen (Orchestrator Pattern)
- Error counter in return dict hinzugefügt für Fehler-Tracking
- Jede Funktion hat Single Responsibility + Docstring
- Testierbarkeit stark verbessert (Mocks für einzelne Schritte möglich)
- **Dokumentiert in:** CURRENT_STATUS.md (Priority 1 Section)
---

### 2026-02-13 - RefactoringAgent (Verarbeitet: 13. Feb 2026)
**Modul/Datei:** `modules/temu/services/order_service.py`
**Art der Änderung:** Refactoring
**Beschreibung:** Priority 2 - Neue Helper-Funktion `_load_json_responses()` für konsistentes JSON-Laden
**Details:**
- Consolidates duplicate JSON loading code (war 2x identisch implementiert)
- Zentralisierte Validation und Error-Handling
- Verwendet Constants statt Magic Strings
- DRY-Prinzip: Single Source of Truth
- **Dokumentiert in:** CURRENT_STATUS.md (Priority 2 Section)
---

### 2026-02-13 - RefactoringAgent (Verarbeitet: 13. Feb 2026)
**Modul/Datei:** `modules/temu/config/config.py`
**Art der Änderung:** Refactoring
**Beschreibung:** Priority 3 - Magic Numbers → Named Constants (15+ neue Konstanten)
**Details:**
- AMOUNT_DIVISOR = 100 (TEMU API gibt Beträge in Cents)
- TAX_RATE_DIVISOR = 1_000_000 (TEMU Tax Rate in Mikrotax)
- ORDER_STATUS_MAP = {1: 'pending', 2: 'processing', ...} (Status-Codes)
- CARRIER_MAPPING = {'dhl': 141252268, ...} (TEMU Carrier IDs)
- VALID_ORDER_STATUSES, WORKFLOW_ORDER_STATUSES (Validierungen)
- ORDER_SYNC_INTERVAL_MINUTES, INVENTORY_SYNC_INTERVAL_MINUTES (Scheduler)
- Ersetzt ~20 Hardcoded Values verteilt über 5+ Dateien
- config.py wächst von 29 auf 97 Zeilen (gut investiert)
- **Dokumentiert in:** CURRENT_STATUS.md (Priority 3 Section), ARCHITECTURE/code_structure.md (Config & Constants)
---

### 2026-02-13 - RefactoringAgent (Verarbeitet: 13. Feb 2026)
**Modul/Datei:** `modules/temu/services/base_workflow_service.py` (NEW)
**Art der Änderung:** Refactoring
**Beschreibung:** Priority 5 - Neue Basisklasse für Workflow-Services - eliminiert 55+ Zeilen Duplikation
**Details:**
- BaseWorkflowService mit shared infrastructure: connection management, credential validation, job lifecycle
- Methods: `_validate_credentials()`, `_generate_job_id()`, `_cleanup_connections()`, `_cleanup_service_caches()` (override hook)
- Lazy-loader: `_get_temu_service()`, `_get_jtl_repo()`
- OrderWorkflowService und InventoryWorkflowService jetzt Subclasses (mit @overrides für hooks)
- MRO-validiert
- OrderWorkflowService: 312 → 259 Zeilen (-17%)
- InventoryWorkflowService: 211 → 189 Zeilen (-10%)
- **Dokumentiert in:** CURRENT_STATUS.md (Priority 5 Section), ARCHITECTURE/code_structure.md (base_workflow_service.py section)
---

### 2026-02-13 - RefactoringAgent (Verarbeitet: 13. Feb 2026)
**Modul/Datei:** `modules/temu/services/tracking_service.py`
**Art der Änderung:** Refactoring
**Beschreibung:** Priority 6a - Dead Code und Dev Comments entfernt
**Details:**
- Removed unused variable `tracking_data_for_api = []` (war immer leer, kein Log-Nutzen)
- Removed dev comments `# ← Kein else-Print!` (10 Zeilen)
- Consolidated duplicate imports (traceback zu top-level)
- Removed unnecessary blank lines
- tracking_service.py: 201 → 159 Zeilen (-21%)
- **Dokumentiert in:** CURRENT_STATUS.md (Priority 6 Section)
---

### 2026-02-13 - RefactoringAgent (Verarbeitet: 13. Feb 2026)
**Modul/Datei:** `modules/temu/services/stock_sync_service.py`
**Art der Änderung:** Refactoring
**Beschreibung:** Priority 6b - Dead Code und Dev Monologue entfernt
**Details:**
- Removed empty `__init__(self): pass` (Anti-Pattern)
- Removed 10-line dev monologue explaining API signature decisions (code speaks for itself)
- Removed dead variable `payload_items` (nur `api_items` verwendet)
- stock_sync_service.py: 105 → 80 Zeilen (-24%)
- **Dokumentiert in:** CURRENT_STATUS.md (Priority 6 Section)
---

### 2026-02-13 - RefactoringAgent (Verarbeitet: 13. Feb 2026)
**Modul/Datei:** `modules/temu/services/order_service.py, order_workflow_service.py, inventory_workflow_service.py, router.py, jobs.py`
**Art der Änderung:** Refactoring
**Beschreibung:** Import-Updates für neue Constants und BaseWorkflowService
**Details:**
- order_service.py: Imports für neue Constants (AMOUNT_DIVISOR, TAX_RATE_DIVISOR, etc.)
- order_workflow_service.py: Import BaseWorkflowService, angepasste Inheritance
- inventory_workflow_service.py: Import BaseWorkflowService, angepasste Inheritance
- router.py: Imports für Status/Order Constants
- jobs.py: Imports für Interval Constants
- Alle Imports verifiziert ✅
- **Dokumentiert in:** CURRENT_STATUS.md (Testing & Verification Section)
---

### 2026-02-13 - RefactoringAgent (Verarbeitet: 13. Feb 2026)
**Modul/Datei:** `modules/temu/` (Order Workflow + Inventory Workflow)
**Art der Änderung:** Testing & Validation
**Beschreibung:** Vollständige Workflow-Tests nach Refactoring - beide erfolgreich
**Details:**
- ✅ Order Sync Workflow: SUCCESS in 0.5s (alle 5 Steps ausgeführt)
- ✅ Inventory Sync Workflow: SUCCESS in 0.1s (4-Step Process, 21 Items batch-updated)
- ✅ Alle Imports verifiziert im venv
- ✅ MRO (Method Resolution Order) korrekt für BaseWorkflowService Inheritance
- ✅ Keine Breaking Changes
- Workflows laufen über uvicorn Frontend-Button
- **Dokumentiert in:** CURRENT_STATUS.md (Testing & Verification Section)
---

### 2026-02-13 - LoggingAgent (Verarbeitet: 13. Feb 2026)
**Modul/Datei:** `.github/agents/LoggingAgent.agent.md`
**Art der Änderung:** Documentation
**Beschreibung:** Customized LoggingAgent für project-spezifische DB-basierte Logging-Architektur
**Details:**
- Replaced generic Python/FastAPI logging spec mit project-spezifischem Guide
- PROJECT LOGGING ARCHITECTURE (SQL Server DB-centric, nicht file-based)
- Structured DB fields: job_id, job_type, level, message, status, duration_seconds, error_text
- Job lifecycle: `start_job_capture()` → `log()` (n times) → `end_job_capture()`
- AUDIT-FOKUS (5-point checklist für Logging-Review)
- IMPLEMENTIERUNGS-PATTERN (Template für neue Workflow-Logging-Implementierungen)
- Agent kann jetzt Logging korrekt auditorieren
- **Dokumentiert in:** LoggingAgent.agent.md selbst (Spec updated)
---