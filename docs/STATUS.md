# 📊 Project Status – 3. Februar 2026

## ⚠️ CRITICAL UPDATE - Monorepo Migration in Progress

**Current Status:** 🔄 MONOREPO MIGRATION ACTIVE (70% complete)

**Branch:** `feature/monorepo-restructure` (NOT feature/streamlit-integration!)

**Migration Tracking:** See [MIGRATION_STATUS.md](../MIGRATION_STATUS.md) for detailed progress

**What's Happening:**
- Full restructure to monorepo architecture (Option A)
- Moving all code from `src/`, `api/`, `config/` → `modules/`
- Services already copied to `modules/temu/services/` and `modules/pdf_reader/services/`
- Import paths need complete overhaul
- Expected completion: 3. Februar 2026

**⚠️ Documentation Status:**
- `MIGRATION_STATUS.md` - ✅ Current and authoritative
- `CLAUDE.md` - ⚠️ Describes OLD structure (will be updated after migration)
- `docs/ARCHITECTURE/code_structure.md` - ⚠️ Describes OLD structure (will be updated after migration)
- This file (`docs/STATUS.md`) - ✅ Updated with migration info

**Next Steps:** See MIGRATION_STATUS.md Phase 1-7

---

## 🔄 Previous State (28. Januar 2026)

### Git Status (OUTDATED - see above)
- **Active Branch:** `feature/streamlit-integration` (tracking `origin/feature/streamlit-integration`)
- **Latest Commit:** (pending) – log filtering improvements
- **Main Production:** `main` at `4577c1e` (stable, last merge 26.01.)

### Untracked Files
- Keine

---

## ✅ Completed (28. Januar – Log Filtering System)

### 28. Januar – Log Filter Frontend Umstellung (FESTE Filter-Optionen)
- ✅ **Problem:** Log-Filter zeigte dynamisch alle job_id Präfixe, aber Sub-Jobs (order_workflow, tracking_service) waren nicht sichtbar
- ✅ **Analyse:** Erkannt, dass Sub-Jobs die GLEICHE job_id wie Master-Job haben (z.B. `temu_orders_1769614356` für order_service UND tracking_service)
- ✅ **Solution:** 
  - Frontend: Wechsel von dynamischen zu FESTEN Filter-Optionen mit Beschreibungen
  - Filter-Optionen mit LIKE-Patterns:
    - "TEMU Bestellungen (Auftragsverarbeitung)" → `temu_orders%`
    - "TEMU Lagerbestand (Inventar)" → `temu_inventory%`
    - "Synchronisiere neue Temu Aufträge" → `sync_orders%`
    - "Synchronisiere Temu Lagerbestand" → `sync_inventory%`
  - Backend: Anpassung von `LogRepository.get_logs()` um bereits mit `%` versehene Patterns zu akzeptieren
- ✅ **Result:** LIKE-Filter zeigt nun alle Sub-Jobs einer Master-Job-ID (z.B. `temu_orders%` zeigt `order_service`, `order_workflow`, `tracking_service` etc.)
- 📄 **Dokumentation:** [docs/FRONTEND/architecture.md](docs/FRONTEND/architecture.md#6-log-filtering-system) – Abschnitt "Log Filtering System"
- 📄 **Code-Änderungen:**
  - [frontend/app.js](frontend/app.js#L168-L185) - `updateJobFilter()` mit festen Optionen
  - [frontend/app.js](frontend/app.js#L117-L135) - `loadAllLogs()` mit LIKE-Pattern Handling
  - [src/db/repositories/common/log_repository.py](src/db/repositories/common/log_repository.py#L73-L108) - `get_logs()` mit flexiblem Pattern-Handling

### 28. Januar – Logger Handler Fix & Error Logging
- ✅ **Problem:** Nach PDF Cleanup wurden Logfiles erstellt, aber nicht gefüllt (Logger-Handler zeigten auf alte, gelöschte Datei-Handles)
- ✅ **Solution 1:** Cleanup mit `file.write()` statt `logger.info()` - Dateien neu erstellt ✅
- ✅ **Solution 2:** Neue `reinitialize_loggers()` Funktion in [src/modules/pdf_reader/logger.py](../src/modules/pdf_reader/logger.py) - schließt alte Handler und erstellt neue ✅
- ✅ **Result:** Nach Cleanup sind Logfiles leer aber funktional (neue Logs werden geschrieben)

### 28. Januar – Error Detection für falsche Dokumenttypen
- ✅ **Problem:** Wenn Werbe-Rechnung als normale Rechnung hochgeladen wird → kein spezifischer Fehler in Logs
- ✅ **Solution:** 
  - [src/modules/pdf_reader/rechnungen_service.py](../src/modules/pdf_reader/rechnungen_service.py) - ERROR wenn `document_type == "werbung"` erkannt
  - [src/modules/pdf_reader/werbung_service.py](../src/modules/pdf_reader/werbung_service.py) - ERROR wenn `document_type in ["rechnung", "gutschrift"]` erkannt
- ✅ **Result:** Klarere Fehlermeldungen mit Hinweis auf richtige Sektion
  - Logs: `logs/pdf_reader/rechnung_read.log` und `logs/pdf_reader/werbung_read.log`
- ✅ **Neue Logger-Architektur:** Modul-spezifische Logger (`temu_logger`, `pdf_reader_logger`) über gemeinsame Factory ([src/services/logger.py](../src/services/logger.py)); `app_logger` bleibt für API/Worker.
- ✅ **Log-Pfade:** `logs/temu/temu.log`, `logs/pdf_reader/pdf_reader.log`, `logs/app/app.log`, PM2: `logs/pm2-out.log`, `logs/pm2-error.log`.
- ✅ **PDF Reader PWA:** Upload/Extract/Process/Download integriert, Service Worker Cache-Fix, HTTPS-Cache-Header über Caddy konfiguriert.
- ✅ **Datenstruktur:** `data/temu/{api_responses,xml,export}` und `data/pdf_reader/{eingang,ausgang,tmp}` fixiert; alle Importe angepasst.
- ✅ **Marktplatz-Connector:** nutzt `TEMU_API_RESPONSES_DIR` statt globalem `DATA_DIR`.

### 27. Januar – XML Export Connection Fix
- ✅ **Problem:** XML-Export Step 3 verwendete Repos/Services aus Step 2; deren DB-Verbindung war nach Commit geschlossen → `ResourceClosedError: This Connection is closed` in `find_by_status`
- ✅ **Fix:** Caches nach Step 2 leeren und vor Step 3 frische Repos/Services erzeugen. Siehe [src/modules/temu/order_workflow_service.py#L90-L104](../src/modules/temu/order_workflow_service.py#L90-L104) und Reset-Helper [src/modules/temu/order_workflow_service.py#L162-L179](../src/modules/temu/order_workflow_service.py#L162-L179)
- ✅ **Ergebnis:** Bestellung `PO-076-03049808781431692` erfolgreich exportiert, Einträge in `temu_xml_export` und `tXMLBestellImport`, `xml_erstellt=1`

### 26. Januar – Transaction Isolation Bug Fix
- ✅ **Root Cause Identified:** SQLAlchemy Transaction Isolation verhinderte Read von uncommitted Items
- ✅ **Solution:** Separate Transaktionen für Step 2 (JSON→DB) und Step 3 (DB→XML)
- ✅ **12 betroffene Orders** erfolgreich re-exportiert mit allen Artikel-Positionen
- ✅ **Failsafe implementiert:** `OrderItemRepository.find_by_bestell_id()` als Fallback
- ✅ **Debug-Logging:** XML-Export zeigt jetzt Item-Counts
- 📄 **Dokumentation:** `docs/FIXES/transaction_isolation_fix_2026-01-26.md`

### 23. Januar – WebSocket Disconnect Cleanup
- ✅ **Problem:** Normal Disconnects (`ConnectionClosedOK`) loggen als ERROR
- ✅ **Solution:** Ignoriere normale WebSocket-Disconnects in Exception Handler
- ✅ **Files:** `api/server.py` - WebSocket Exception Handling
- ✅ **PM2 Restart:** Logs sind seitdem sauber

### Frühere Sessions (Jan. 2026)
- ✅ BaseRepository Pattern implementiert (alle 7+ Repositories unified)
- ✅ Stock Sync Logic Fix (`needs_sync = CASE WHEN s.jtl_stock > 0`)
- ✅ OrderWorkflowService Transaction Splitting (BLOCK 1 & BLOCK 2)
- ✅ StockSyncService mit Batch Updates
- ✅ All 21 Articles erfolgreich synchronized (vorher nur 7)

---

## 🚀 In Progress / Recent Work

### Branch Status
- `feature/streamlit-integration` enthält: PDF Reader PWA, Datenpfad-Refactor, Logger-Trennung mit Handler-Fix, TEMU Import-Fixes. Noch nicht nach `main` gemerged.

### Foreign Key Constraint Bug (laufend)
**Problem:** INSERT in `temu_order_items` schlägt sporadisch fehl mit FK-Violation (Order ID = 0)
- ✅ Validation in `order_service.py`: Prüfe `order_db_id > 0` vor Item-Insert
- ✅ Logging erweitert: `order_repository.py` und `order_item_repository.py` zeigen IDs bei Fehlern
- 🔍 Nächster Schritt: Ursache für `order_repo.save()` → 0 weiter untersuchen (DB Constraints, Input-Data prüfen)

### Tests
- 🔜 End-to-end Test der TEMU Workflows nach Logger-/Pfad-Refactor
- 🔜 PDF Reader End-to-end Test (Upload → Extract → Process → Download) nach Deploy

---

## 📋 Next TODO / Known Issues

### Planned Development
- [ ] Merge `feature/streamlit-integration` → `main` nach E2E-Tests
- [ ] Integration Tests für Order- und Inventory-Workflow
- [ ] PDF Reader PWA Regression-Test nach Deploy
- [ ] Performance Monitoring für Stock Sync

### Known Issues
- ⚠️ Offene Analyse: `order_repo.save()` → 0 (FK-Violation Risiko)
- ℹ️ Debug-Scripts aus `FIXES/` nicht committen

### Quality Checklist
- [x] BaseRepository Pattern unified (7+ repos)
- [x] Transaction Isolation fixed
- [x] WebSocket Disconnects silent
- [x] Stock Sync für alle Artikel aktiv
- [x] Logger nach Modulen getrennt
- [x] Datenpfade in `data/temu` und `data/pdf_reader`
- [ ] Integration Tests vollständig dokumentiert
- [ ] Performance Baselines gemessen

---

## 🔧 Working Environment

### Deployment & Runtime
- **API Server:** PM2 managed (`temu-api`)
- **Database:** MSSQL (Toci + JTL)
- **Frontend:** PWA (Offline-capable)
- **Scheduler:** APScheduler (Cron Jobs)

### Recent Env Changes
- Python 3.12 (venv active)
- All dependencies stable
- No breaking changes pending

---

## 📚 Documentation Updated
- ✅ `docs/FIXES/transaction_isolation_fix_2026-01-26.md` – Komplett
- ✅ `docs/README.md` – Central Index
- ✅ `docs/ARCHITECTURE/code_structure.md` – Structure
- ✅ `docs/DATABASE/architecture.md` – DB Layer
- ✅ `docs/API/architecture.md` – API Layer
- ✅ `docs/WORKFLOWS/architecture.md` – Workflow Layer
- ✅ `docs/DEPLOYMENT/architecture.md` – Deployment Basics
- ✅ `docs/PERFORMANCE/architecture.md` – Performance Guide
- ✅ `docs/FRONTEND/architecture.md` – PWA Architecture

---

## 💡 How to Use This File

**Vor jeder neuen Development-Session:**
1. Diesen Stand lesen
2. `git log -5 --oneline` kurz überflogen
3. Relevante Docs aus `docs/FIXES/` oder anderen Ordnern checken
4. **Dann:** Copilot hat aktuellen Kontext

**Nach einer Session:**
- Diese Datei updaten mit neuen Commits/Fixes
- Commit in Git zusammen mit anderen Changes
- Nächste Session kann davon lesen

---

**Last Updated:** 28. Januar 2026, 13:30  
**Next Review:** Nach E2E-Tests & Merge-Plan
