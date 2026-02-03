# CSV-Verarbeiter Migration Plan

**Datum:** 3. Februar 2026
**Ziel:** Migration von Streamlit zu FastAPI + HTML/CSS/JS Frontend
**Analog zu:** PDF Reader Migration (erfolgreich abgeschlossen)

---

## Projektübersicht

### Original-Tool (Streamlit)
**Name:** JTL2DATEV CSV-Verarbeiter
**Repository:** https://github.com/donchrillo/csv_verarbeiter.git
**Location:** `migration_archive/csv_verarbeiter_original/`

**Zweck:**
- Amazon/DATEV-kompatible CSV-Dateien verarbeiten
- Amazon Order-IDs → SQL-Kundennummern ersetzen
- Kritische Gegenkonten (0-20) erkennen
- Excel-Protokolle erstellen
- ZIP-Export mit Reports

**Technologien:**
- **Frontend:** Streamlit
- **Backend:** Python (pandas, pyodbc, openpyxl)
- **Datenbank:** SQL Server (JTL-Datenbank)

---

## Ziel-Architektur

### Neue Struktur (FastAPI + HTML/CSS/JS)

```
modules/csv_verarbeiter/
├── __init__.py
├── README.md
├── router.py                    # FastAPI Router
├── frontend/
│   ├── csv.html                 # HTML UI (Design: helles Apple-Design wie index-new.html)
│   ├── csv.css                  # Styling (Basis: dashboard.css)
│   └── csv.js                   # Frontend Logic (WebSocket-Updates)
└── services/
    ├── __init__.py
    ├── config.py                # Konfiguration
    ├── logger.py                # Logging
    ├── csv_processor.py         # Kernlogik (aus verarbeitung.py)
    ├── csv_io.py                # CSV I/O (aus verarbeitung_io.py)
    ├── csv_logic.py             # Datenlogik (aus verarbeitung_logik.py)
    ├── csv_validation.py        # Validierung (aus verarbeitung_validation.py)
    ├── sql_service.py           # SQL-Abfragen (aus sql.py, nutzt shared/database)
    ├── report_service.py        # Excel-Reports (aus report_collector.py)
    └── zip_service.py           # ZIP-Handling (aus zip_handler.py)

data/csv_verarbeiter/            # Zentrale Datenablage
├── eingang/                     # Upload-Verzeichnis
├── ausgang/                     # Output-Verzeichnis (verarbeitete CSVs)
└── reports/                     # Excel-Reports (Protokolle)

logs/csv_verarbeiter/            # Log-Dateien (analog zu anderen Modulen)
└── csv_verarbeiter.log          # Haupt-Logfile
```

**Wichtige Änderungen:**
- ✅ Daten-Verzeichnis: `data/csv_verarbeiter/` (zentral, nicht im Modul)
- ✅ Logs-Verzeichnis: `logs/csv_verarbeiter/` (konsistent mit PDF Reader, TEMU, etc.)
- ✅ Design: Helles Apple-Design (Basis: `frontend/index-new.html` + `dashboard.css`)
- ✅ WebSocket: Live-Updates während Verarbeitung
- ✅ SQL: Nutzt `modules/shared/database` für Connection Pooling

**Integration in Hauptsystem:**
- Router: `main.py` → `app.include_router(csv_router, prefix="/api/csv")`
- Frontend: `main.py` → `@app.get("/csv")` → serviert `csv.html`
- Datenbank: Nutzt `modules/shared/database` (bereits vorhanden)
- Logging: Nutzt `modules/shared/logging` (bereits vorhanden)

---

## Migrations-Phasen

### Phase 1: Setup & Analyse ✅

**Status:** ✅ Abgeschlossen

**Schritte:**
1. ✅ Feature-Branch erstellt: `feature/csv-verarbeiter-migration`
2. ✅ Original-Code geclont: `migration_archive/csv_verarbeiter_original/`
3. ✅ README analysiert
4. ✅ Code-Struktur analysiert (13 Module)
5. ✅ Dependencies identifiziert

---

### Phase 2: Backend-Migration (Streamlit → FastAPI)

**Ziel:** Python-Backend zu FastAPI Services migrieren

#### 2.1 Modul-Struktur erstellen

```bash
mkdir -p modules/csv_verarbeiter/{services,frontend,data/{eingang,ausgang,log}}
touch modules/csv_verarbeiter/__init__.py
touch modules/csv_verarbeiter/router.py
touch modules/csv_verarbeiter/README.md
```

#### 2.2 Services migrieren

**Mapping: Original → Neu**

| Original | Neu | Beschreibung |
|----------|-----|--------------|
| `config.py` | `services/config.py` | Pfade, Konstanten (DATEV-Spalten) |
| `verarbeitung.py` | `services/csv_processor.py` | Hauptlogik: `process_csv()` |
| `verarbeitung_io.py` | `services/csv_io.py` | CSV lesen/schreiben |
| `verarbeitung_logik.py` | `services/csv_logic.py` | Order-ID Ersetzung |
| `verarbeitung_validation.py` | `services/csv_validation.py` | Validierung |
| `sql.py` | `services/sql_service.py` | SQL-Abfragen → nutzt `shared/database` |
| `report_collector.py` | `services/report_service.py` | Excel-Protokolle |
| `zip_handler.py` | `services/zip_service.py` | ZIP-Handling |
| `log_helper.py` | `services/logger.py` | Logging → nutzt `shared/logging` |
| `backend.py` | `router.py` | Koordination → FastAPI Endpoints |
| `gui.py` | `frontend/csv.js` | GUI-Logik → JavaScript |
| `gui_utils.py` | `frontend/csv.js` | GUI-Helfer → JavaScript |

#### 2.3 FastAPI Router erstellen

**Endpoints:**

```python
# router.py
from fastapi import APIRouter, UploadFile, File
from typing import List

router = APIRouter()

@router.get("/status")
async def get_status():
    """Status: Dateien in eingang/ausgang/log"""
    pass

@router.post("/upload")
async def upload_files(files: List[UploadFile]):
    """CSV/ZIP-Dateien hochladen → eingang/"""
    pass

@router.post("/process")
async def process_files(filenames: List[str]):
    """Verarbeitung starten: CSV → OrderID-Ersetzung → ausgang/"""
    pass

@router.get("/reports")
async def list_reports():
    """Liste aller Excel-Reports in log/"""
    pass

@router.get("/reports/{filename}")
async def download_report(filename: str):
    """Excel-Report herunterladen"""
    pass

@router.get("/download/{filename}")
async def download_csv(filename: str):
    """Verarbeitete CSV herunterladen"""
    pass

@router.post("/cleanup")
async def cleanup():
    """Alle Dateien löschen (eingang/ausgang/log)"""
    pass

@router.get("/logs/{filename}")
async def get_log(filename: str):
    """Log-Datei abrufen"""
    pass
```

#### 2.4 SQL-Integration

**Wichtig:** SQL-Service nutzt `shared/database` für Connection Pooling

```python
# services/sql_service.py
from modules.shared.database import get_db_connection

def get_customer_number(order_id: str) -> str | None:
    """
    Holt Kundennummer zu Amazon Order-ID aus JTL-Datenbank.

    Original: sql.py → get_kundennummer()
    Neu: Nutzt shared database connection
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # SQL-Abfrage aus original sql.py
        query = "SELECT cKundennr FROM tbestellung WHERE cBestellNr = ?"
        cursor.execute(query, (order_id,))
        result = cursor.fetchone()
        return result[0] if result else None
```

---

### Phase 3: Frontend-Migration (Streamlit → HTML/CSS/JS)

**Ziel:** Streamlit-GUI durch modernes Web-Frontend ersetzen

#### 3.1 HTML-Struktur (`csv.html`)

**Sections:**
1. **Upload-Bereich**
   - Drag & Drop Zone
   - Dateiliste (CSV/ZIP)
   - Upload-Button

2. **Verarbeitung**
   - Dateiauswahl (aus eingang/)
   - Verarbeiten-Button
   - Progress-Anzeige

3. **Status-Übersicht**
   - Eingang: X Dateien
   - Ausgang: Y Dateien
   - Reports: Z Dateien

4. **Reports & Downloads**
   - Liste aller Excel-Reports
   - Download-Buttons
   - Verarbeitete CSVs zum Download

5. **Logs**
   - Tabs: Verarbeitung, Validierung, Fehler
   - Log-Anzeige

6. **Cleanup**
   - Button zum Löschen aller Dateien

#### 3.2 Styling (`csv.css`)

**Design:**
- Analog zu PDF Reader: Modern, responsive, dunkles Theme
- Cards für Upload, Verarbeitung, Reports
- Tabellen für Dateilisten
- Progress-Bar für Verarbeitung

#### 3.3 Frontend-Logik (`csv.js`)

**Funktionen:**
```javascript
// Upload
async function uploadFiles() { ... }

// Verarbeitung
async function processFiles() { ... }
function showProgress(text) { ... }
function updateProgress(percent) { ... }

// Status
async function loadStatus() { ... }

// Reports
async function loadReports() { ... }
async function downloadReport(filename) { ... }

// Download
async function downloadCSV(filename) { ... }

// Cleanup
async function cleanup() { ... }

// Logs
async function showLog(type) { ... }
```

---

### Phase 4: Integration in Hauptsystem

#### 4.1 Router in main.py einbinden

```python
# main.py
from modules.csv_verarbeiter import get_router as get_csv_router

app.include_router(
    get_csv_router(),
    prefix="/api/csv",
    tags=["CSV Verarbeiter"]
)

@app.get("/csv")
async def csv_ui():
    """CSV-Verarbeiter UI"""
    csv_html = Path(__file__).parent / "modules" / "csv_verarbeiter" / "frontend" / "csv.html"
    return FileResponse(str(csv_html))
```

#### 4.2 Service Worker aktualisieren

```javascript
// frontend/service-worker.js
const ASSETS = [
  // ...
  '/static/csv.css?v=20260203',
  '/static/csv.js?v=20260203'
];
```

#### 4.3 Dashboard-Link hinzufügen

```html
<!-- frontend/index-new.html -->
<a href="/csv" class="module-card csv-card">
    <div class="module-icon">📊</div>
    <div class="module-content">
        <h2>CSV Verarbeiter</h2>
        <p class="module-desc">JTL2DATEV CSV-Verarbeitung</p>
        <div class="module-features">
            <span class="feature-tag">Order-ID Ersetzung</span>
            <span class="feature-tag">Excel Reports</span>
            <span class="feature-tag">ZIP Export</span>
        </div>
    </div>
    <div class="module-arrow">→</div>
</a>
```

---

### Phase 5: Testing & Validierung

#### 5.1 Funktionale Tests

**Test-Szenarien:**
1. ✅ CSV-Upload (einzelne Datei)
2. ✅ ZIP-Upload (mehrere CSVs)
3. ✅ Order-ID Ersetzung (SQL-Lookup)
4. ✅ Kritische Konten-Erkennung (0-20)
5. ✅ Excel-Report-Generierung
6. ✅ ZIP-Export
7. ✅ Fehlerhafte Dateien (Protokollierung)
8. ✅ Cleanup (alle Dateien löschen)

#### 5.2 Integration Tests

1. ✅ `/api/csv/status` → Status korrekt
2. ✅ `/api/csv/upload` → Dateien im eingang/
3. ✅ `/api/csv/process` → Verarbeitung läuft
4. ✅ `/api/csv/reports` → Reports abrufbar
5. ✅ `/csv` → Frontend lädt
6. ✅ Datenbank-Connection über shared/database

#### 5.3 Performance Tests

- 100 CSVs gleichzeitig verarbeiten
- Große CSV-Dateien (>10MB)
- SQL-Connection Pooling

---

### Phase 6: Dokumentation

#### 6.1 README.md (Modul)

```markdown
# CSV Verarbeiter Modul

JTL2DATEV CSV-Verarbeitung für Amazon-Händler.

## Features
- Amazon Order-ID → Kundennummer Ersetzung
- Kritische Konten-Erkennung
- Excel-Protokolle
- ZIP-Export

## Endpoints
- POST /api/csv/upload
- POST /api/csv/process
- GET /api/csv/reports
- GET /api/csv/download/{filename}

## Frontend
- /csv → CSV-Verarbeiter UI

## Verzeichnisse
- modules/csv_verarbeiter/data/eingang/
- modules/csv_verarbeiter/data/ausgang/
- modules/csv_verarbeiter/data/log/
```

#### 6.2 CLAUDE.md aktualisieren

```markdown
## Module Structure (Monorepo Architecture)

**modules/csv_verarbeiter/** - CSV/DATEV-Verarbeitung
- `router.py`: FastAPI routes (`/api/csv/*`)
- `frontend/`: HTML/CSS/JS UI
- `services/`: CSV processing, SQL lookups, Excel reports
- `data/`: eingang/, ausgang/, log/
```

---

### Phase 7: Cleanup & PR

#### 7.1 Original-Code archivieren

```bash
# Original bleibt in migration_archive/ zur Referenz
# (wird nicht gelöscht, kann später für Vergleiche genutzt werden)
```

#### 7.2 Git Commit

```bash
git add modules/csv_verarbeiter/
git add main.py
git add frontend/index-new.html
git add frontend/service-worker.js
git add CLAUDE.md
git commit -m "feat(csv-verarbeiter): Migrate Streamlit tool to FastAPI module

- Backend: Streamlit → FastAPI Router + Services
- Frontend: Streamlit GUI → HTML/CSS/JS
- Integration: Router in main.py, Dashboard-Link
- Services: CSV processing, SQL lookups, Excel reports, ZIP handling
- Data directories: eingang/, ausgang/, log/

Analog to PDF Reader migration (completed successfully)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

#### 7.3 Pull Request

**Title:** `feat(csv-verarbeiter): Migrate Streamlit tool to FastAPI module`

**Description:**
- Migration analog zu PDF Reader
- Streamlit → FastAPI + HTML/CSS/JS
- Vollständige Funktionalität erhalten
- Integrations-Tests erfolgreich

---

## Technische Details

### CSV-Verarbeitungs-Pipeline

**Original-Flow (Streamlit):**
```
gui.py → backend.py → verarbeitung.py → verarbeitung_io.py
                    → verarbeitung_logik.py (SQL via sql.py)
                    → verarbeitung_validation.py
                    → report_collector.py (Excel)
                    → zip_handler.py
```

**Neuer Flow (FastAPI):**
```
csv.js → POST /api/csv/process → router.py
                                → csv_processor.py
                                → csv_io.py (lesen)
                                → csv_logic.py (SQL via sql_service.py)
                                → csv_validation.py
                                → report_service.py (Excel)
                                → zip_service.py
                                → csv_io.py (schreiben)
                                → Response (JSON)
csv.js ← JSON Response ← router.py
```

### DATEV-Spalten (aus config.py)

**Wichtige Konstanten:**
```python
# Original: config.py
SPALTEN_DATEV = [
    "Sollkonto", "Habenkonto", "Betrag", "Buchungstext",
    "Gegenkonto", "Datum", "Währung", "Beleg1", "Beleg2"
]

# OrderID-Spalte
ORDER_ID_SPALTE = "Beleg2"  # Hier steht die Amazon Order-ID

# Kritische Konten
KRITISCHE_KONTEN_RANGE = range(0, 21)  # 0-20
```

### SQL-Abfragen

**Original (sql.py):**
```python
def get_kundennummer(order_id: str) -> str | None:
    query = """
        SELECT cKundennr
        FROM tbestellung
        WHERE cBestellNr = ?
    """
```

**Neu (services/sql_service.py):**
```python
from modules.shared.database import get_db_connection

def get_customer_number(order_id: str) -> str | None:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT cKundennr FROM tbestellung WHERE cBestellNr = ?"
        cursor.execute(query, (order_id,))
        result = cursor.fetchone()
        return result[0] if result else None
```

### Excel-Report-Struktur

**Original (report_collector.py):**
```python
# Spalten:
# - OrderID (Original)
# - Kundennummer (Ersetzt)
# - Status (Gefunden / Nicht gefunden / Fehler)
# - Gegenkonto (für kritische Konten)
# - Warnung (bei kritischen Konten)
```

**Neu (services/report_service.py):**
- Gleiche Struktur beibehalten
- Nutzt openpyxl (bereits in requirements.txt)

---

## Migrations-Priorität

### Must-Have (Phase 2-4)
- ✅ Backend-Services funktionsfähig
- ✅ CSV-Upload
- ✅ Order-ID Ersetzung via SQL
- ✅ Excel-Report-Generierung
- ✅ Download verarbeiteter CSVs

### Should-Have (Phase 5)
- ✅ ZIP-Upload/Export
- ✅ Kritische Konten-Erkennung
- ✅ Log-Anzeige im Frontend
- ✅ Progress-Bar

### Nice-to-Have (Future)
- E-Mail-Benachrichtigung bei kritischen Fällen
- eBay-Format-Unterstützung
- SQL-Parameter über GUI konfigurierbar
- Fehler-Dashboard mit Drilldown

---

## Lessons Learned (aus PDF Reader Migration)

### Was gut funktioniert hat:
1. **Modulare Services:** Backend-Logik in separate Services aufteilen
2. **Shared Database:** Connection Pooling aus `modules/shared/database` nutzen
3. **Logging:** Zentrale Logging-Konfiguration aus `modules/shared/logging`
4. **Frontend-Struktur:** HTML/CSS/JS analog zu PDF Reader
5. **Schrittweise Migration:** Erst Backend, dann Frontend, dann Integration

### Was zu beachten ist:
1. **Query-Parameter:** Cache-Busting mit `?v=20260203`
2. **Service Worker:** Neue Assets hinzufügen
3. **Caddy Cache:** API-Routes dürfen NICHT gecacht werden
4. **Error Handling:** try/except in allen Router-Endpoints
5. **File Uploads:** FormData in JavaScript, UploadFile in FastAPI

---

## Zeitplan (geschätzt)

| Phase | Aufwand | Status |
|-------|---------|--------|
| Phase 1: Setup & Analyse | 0.5h | ✅ Abgeschlossen |
| Phase 2: Backend-Migration | 4-6h | Geplant |
| Phase 3: Frontend-Migration | 3-4h | Geplant |
| Phase 4: Integration | 1-2h | Geplant |
| Phase 5: Testing | 2-3h | Geplant |
| Phase 6: Dokumentation | 1h | Geplant |
| Phase 7: Cleanup & PR | 0.5h | Geplant |
| **Gesamt** | **12-17h** | |

---

## Risiken & Mitigations

### Risiko 1: SQL-Kompatibilität
**Problem:** JTL-Datenbank-Schema könnte sich unterscheiden
**Mitigation:** Original SQL-Queries 1:1 übernehmen, dann testen

### Risiko 2: Performance bei großen Dateien
**Problem:** Mehrere große CSVs gleichzeitig verarbeiten
**Mitigation:** Async Processing, Connection Pooling nutzen

### Risiko 3: Excel-Export-Kompatibilität
**Problem:** openpyxl-Version oder Format-Unterschiede
**Mitigation:** Original report_collector.py Logik exakt übernehmen

### Risiko 4: Frontend-Usability
**Problem:** Streamlit ist sehr benutzerfreundlich, HTML könnte komplexer sein
**Mitigation:** UI/UX analog zu PDF Reader, Progress-Feedback, klare Fehlermeldungen

---

## Success Criteria

✅ **Migration erfolgreich, wenn:**
1. Alle 13 Original-Module erfolgreich migriert
2. CSV-Upload und Verarbeitung funktioniert
3. Order-ID Ersetzung via SQL funktioniert
4. Excel-Reports werden korrekt generiert
5. Frontend ist intuitiv bedienbar
6. Alle Tests (Unit, Integration, Performance) bestanden
7. Dokumentation vollständig
8. Code reviewed und gemerged

---

**Nächster Schritt:** Phase 2 starten (Backend-Migration)
