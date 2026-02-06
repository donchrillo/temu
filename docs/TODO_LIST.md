# Project TODO List

**Datum:** 6. Februar 2026
**Zweck:** Auflistung aller ausstehenden Aufgaben, nächsten Schritte, bekannten Probleme und zukünftigen Erweiterungen für das TEMU-Integrationsprojekt.

---

## 1. CSV-Verarbeiter Migration (IN BEARBEITUNG 🔄)

Die folgenden Phasen der CSV-Verarbeiter-Migration stehen noch aus:

### ✅ Phase 2: Core Services (ABGESCHLOSSEN)
- [x] Create `modules/csv_verarbeiter/services/csv_io_service.py`
  - Read CSV files (encoding detection, pandas integration)
  - Write processed CSV files to output directory
  - ZIP file extraction and creation
- [x] Create `modules/csv_verarbeiter/services/validation_service.py`
  - OrderID pattern validation
  - Critical account detection (0-20)
  - Data integrity checks
- [x] Create `modules/csv_verarbeiter/services/replacement_service.py`
  - Query customer numbers from SQL database
  - Replace OrderIDs with customer numbers
  - Track replacement success/failure
- [x] Create `modules/csv_verarbeiter/services/report_service.py`
  - Generate Excel reports with validation results
  - Track errors and warnings
  - Summary statistics
- [x] Create `modules/csv_verarbeiter/services/config.py`
  - Path configuration and constants

### ⏳ Phase 3: API Endpoints (Geschätzt: 2-3 Stunden)
- [ ] Implement `modules/csv_verarbeiter/router.py` with endpoints:
  - `POST /api/csv/upload` - Upload CSV/ZIP files
  - `POST /api/csv/process` - Process uploaded files
  - `GET /api/csv/status/{job_id}` - Get processing status
  - `GET /api/csv/download/{file_id}` - Download processed files
  - `GET /api/csv/reports` - List available reports
- [ ] Integrate with shared log service for job tracking
- [ ] Implement file upload handling (multipart/form-data)
- [ ] Add proper error responses (400, 404, 500)

### ⏳ Phase 4: Frontend Development (Geschätzt: 3-4 Stunden)
- [ ] Create `modules/csv_verarbeiter/frontend/csv.html`
  - Light Apple-design (consistent with `index-new.html`)
  - File upload interface (drag & drop + file picker)
  - Processing status display
  - Download links for results
- [ ] Create `modules/csv_verarbeiter/frontend/static/csv.css`
  - Light theme styling
  - Responsive design
  - Loading states and animations
- [ ] Create `modules/csv_verarbeiter/frontend/static/csv.js`
  - File upload with progress tracking
  - WebSocket integration for live updates
  - Download handlers
  - Error display

### ⏳ Phase 5: Integration & Testing (Geschätzt: 2-3 Stunden)
- [ ] Mount router in `main.py` gateway
- [ ] Add frontend route to serve `csv.html`
- [ ] Update Service Worker with CSV assets
- [ ] Update navigation in `index-new.html`
- [ ] End-to-end testing with real CSV files
- [ ] Test error scenarios (invalid files, database errors)

### ⏳ Phase 6: Documentation (Geschätzt: 1-2 Stunden)
- [ ] Create `modules/csv_verarbeiter/README.md`
  - Module overview, CSV format requirements, API documentation, Troubleshooting guide
- [ ] Update `CLAUDE.md` with final implementation details (Diese Information wird in die `docs/CURRENT_STATUS.md` und `docs/TODO_LIST.md` integriert werden)
- [ ] Document database schema changes (if any)
- [ ] Add usage examples

### ⏳ Phase 7: Deployment (Geschätzt: 1 Stunde)
- [ ] Merge feature branch to `dev`
- [ ] Test in development environment
- [ ] Create Pull Request to `main`
- [ ] Update PM2 configuration (if needed)
- [ ] Deploy to production
- [ ] Verify in production environment

---

## 2. Nächste Schritte & Offene Punkte

### Unmittelbare Aufgaben:
*   **CSV-Verarbeiter Phase 3 starten** - Implementierung der API Endpoints (router.py).
*   **Unit Testing** - Erstellung von Tests für die Core Services.
*   **Dokumentation** - `modules/csv_verarbeiter/README.md` erstellen.

### Kurzfristige Aufgaben:
*   Abschluss der Phasen 2-5 (Core Services → Integration) für CSV-Verarbeiter.
*   End-to-end-Tests mit realen CSV-Dateien.
*   Merge des CSV-Verarbeiter-Feature-Branches in `dev` für Integrationstests.

### Mittelfristige Aufgaben:
*   Abschluss der Phase 6 (Dokumentation) und Phase 7 (Produktions-Deployment) für CSV-Verarbeiter.
*   User Acceptance Testing.

---

## 3. Bekannte Probleme & Technische Schulden

*   ⚠️ **Offene Analyse:** `order_repo.save()` → 0 (Foreign Key Violation Risiko bei `temu_order_items` INSERT). Die Ursache für `order_db_id = 0` muss weiter untersucht werden.
*   ℹ️ **Hinweis:** Debug-Scripts aus `FIXES/` sollten nicht in das Repository committet werden (dies wurde bereits mit dem Löschen der Fix-Dateien behoben).

---

## 4. Test-TODOs (CSV-Verarbeiter)

*   ⏳ Unit Tests für die Services des CSV-Verarbeiters.
*   ⏳ Integration Tests für die Workflows des CSV-Verarbeiters.
*   ⏳ End-to-end Tests mit realen CSV-Dateien für den CSV-Verarbeiter.
*   ⏳ Testen von Fehler-Szenarien für den CSV-Verarbeiter (ungültige Dateien, Datenbankfehler).

---

## 5. Zukünftige Erweiterungen (Optional)

### CSV-Verarbeiter Spezifisch:
*   Automatisierte E-Mail-Benachrichtigungen für kritische Fehler.
*   Unterstützung für zusätzliche Marktplatz-Formate (eBay, etc.).
*   GUI-Konfiguration für SQL-Parameter.
*   Integriertes Fehler-Dashboard mit Drill-down-Funktionalität.
*   Batch-Verarbeitungsoptimierung.

### Allgemein:
*   JTL Direct API Connector (derzeit nur XML-Export).
*   Verbessertes Monitoring und Alerting.
*   Performance-Optimierung für große Datensätze.
