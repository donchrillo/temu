# 🤖 AI Project Guide: TEMU ERP System

**Datum der letzten Aktualisierung:** 13. Februar 2026  
**Zweck:** Dieser umfassende Leitfaden bietet der AI einen vollständigen Überblick über das TEMU ERP-Projekt, die Architektur, das Setup und die Arbeitsprinzipien. Er sollte zu Beginn jeder Arbeitssitzung gelesen werden.

---

## 1. Projekt-Übersicht

Das **TEMU ERP System** ist eine modulare Integrations-Plattform zur Synchronisation von Daten zwischen dem **TEMU Marketplace** und einem **JTL ERP**-System (Microsoft SQL Server). Das Projekt wurde zu einer **Monorepo-Struktur** migriert, um Modularität und Wartbarkeit zu verbessern.

### Kernfunktionalitäten
- **Order Sync:** Abrufen von Bestellungen aus TEMU, Import in die lokale Datenbank und Vorbereitung für JTL (XML-Export)
- **Inventory Sync:** Synchronisation der Lagerbestände von JTL zu TEMU (4-Schritt-Workflow)
- **PDF Processing:** Datenextraktion aus Rechnungen und Werbematerialien (Amazon/TEMU) mit Excel-Export
- **CSV Processing:** Konvertierung von JTL CSV-Exporten ins DATEV-Format (in Entwicklung)
- **Job Scheduling:** Automatisierte Hintergrund-Tasks via APScheduler
- **Frontend:** Progressive Web App (PWA) mit Echtzeit-Dashboards (WebSocket)

---

## 2. Wichtigste Dokumentations-Einstiegspunkte

Um den aktuellen Projektkontext zu verstehen, solltest du immer mit diesen Dokumenten beginnen:

- **[docs/README.md](docs/README.md):** Der zentrale Index für alle Dokumentationen
- **[docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md):** Aktueller Projektstatus, abgeschlossene Meilensteine und Fortschritt der Migration
- **[docs/TODO_LIST.md](docs/TODO_LIST.md):** Konsolidierte Liste aller ausstehenden Aufgaben und bekannten Probleme
- **[docs/FIXES/OVERVIEW.md](docs/FIXES/OVERVIEW.md):** Behobene Fehler und daraus abgeleitete Best Practices

### Architektur-Dokumentation
- **[docs/ARCHITECTURE/](docs/ARCHITECTURE/):** Code-Struktur, Module, Datenflüsse
- **[docs/FRONTEND/](docs/FRONTEND/):** PWA, WebSocket, Caching, CSS-Architektur, zentrale Navigation
- **[docs/DATABASE/](docs/DATABASE/):** Datenbank-Layer, Connections, Repositories
- **[docs/API/](docs/API/):** FastAPI Server, REST Endpoints, WebSocket
- **[docs/WORKFLOWS/](docs/WORKFLOWS/):** Job Orchestrierung, Scheduler, PM2
- **[docs/DEPLOYMENT/](docs/DEPLOYMENT/):** Remote Setup, PM2 Commands
- **[docs/PERFORMANCE/](docs/PERFORMANCE/):** Benchmarks, Optimierung

---

## 3. Technologie-Stack

- **Sprache:** Python 3.12+
- **Framework:** FastAPI (Async/Await)
- **Datenbank:** MSSQL (pyodbc + SQLAlchemy)
- **Job Scheduling:** APScheduler
- **Datenverarbeitung:** Pandas, PDFPlumber, OpenPyXL
- **Process Management:** PM2 (Node.js)
- **Frontend:** Vanilla JS, CSS (Apple-style, zentralisiert in `master.css`), HTML5, PWA

---

## 4. Architektur & Verzeichnisstruktur

Folgt einem **Monorepo**-Pattern mit strikter Separation of Concerns.

### Top-Level Verzeichnisse
```
├── modules/                    # Alle Application-Logik
│   ├── shared/                 # Gemeinsame Infrastruktur
│   │   ├── config/             # Settings, Environment Variables
│   │   ├── database/           # DB-Layer, Repositories
│   │   ├── logging/            # Logging Services
│   │   └── connectors/         # API Connectors
│   ├── temu/                   # TEMU Marketplace Logik
│   │   ├── services/           # TEMU Services
│   │   ├── frontend/           # TEMU Frontend
│   │   └── router.py           # FastAPI Router
│   ├── pdf_reader/             # PDF Extraction Logik
│   │   ├── services/           # PDF Services
│   │   ├── frontend/           # PDF Frontend
│   │   └── router.py           # FastAPI Router
│   ├── csv_verarbeiter/        # CSV Processing (JTL→DATEV) ✅ Abgeschlossen
│   │   ├── services/           # CSV Services
│   │   ├── frontend/           # CSV Frontend
│   │   └── router.py           # FastAPI Router
│   └── jtl/                    # JTL-spezifische Logik (XML-Export)
├── workers/                    # APScheduler Jobs & Konfiguration
│   ├── job_models.py           # Job Modelle
│   ├── worker_service.py       # Worker Service
│   ├── workers_config.py       # Job Konfiguration
│   └── config/workers_config.json  # JSON Config
├── data/                       # Runtime Storage (von .gitignore ausgeschlossen)
│   ├── pdf_reader/
│   ├── csv_verarbeiter/
│   └── temu/
├── logs/                       # Log-Dateien (von .gitignore ausgeschlossen)
│   ├── app/
│   ├── pdf_reader/
│   ├── temu/
│   └── csv_verarbeiter/
├── frontend/                   # Shared Frontend Assets & PWA Entry Point
│   ├── index-new.html          # Main PWA Entry
│   ├── master.css              # Zentralisierte Styles
│   ├── components/
│   │   ├── nav-loader.js       # Zentrale Navigation
│   │   ├── navigation.html
│   │   └── progress-helper.js
│   └── icons/
├── docs/                       # Comprehensive Dokumentation
├── main.py                     # Central FastAPI Gateway
├── requirements.txt            # Python Dependencies
├── ecosystem.config.js         # PM2 Configuration
└── start_dev.sh               # Development Start Script
```

---

## 5. Grundlegende Arbeitsprinzipien für die AI

Um sichere, effiziente und nachvollziehbare Entwicklung zu gewährleisten, halte dich strikt an folgende Prinzipien:

### 5.1 Dokumentation ist Teil des Codes – halte sie AKTUELL
- **Jede Code-Änderung, die Architektur, Funktionalität oder Verständnis des Systems beeinflusst, MUSS in den relevanten Dokumentationsdateien (im `docs/`-Verzeichnis) widergespiegelt werden.**
- Dies gilt insbesondere für Architektur-Dokumente, Status-Updates und die TODO-Liste
- **Aktualisiere das Datum:** Bei jeder Änderung einer Dokumentationsdatei MUSS das im Header angegebene Datum auf den aktuellen Tag aktualisiert werden

### 5.2 Commit-Verpflichtung
- **Nach JEDER erfolgreichen Implementierung oder einem Satz logisch zusammenhängender Änderungen MUSS ein Git Commit durchgeführt werden**
- Die Commit-Nachricht sollte klar, prägnant und aussagekräftig sein und dem Conventional Commits-Standard folgen: `<type>(<scope>): <subject>`

### 5.3 Konsistenz und Konventionen
- Analysiere stets den umgebenden Code, Tests und Konfigurationen, um bestehende Projektkonventionen zu übernehmen
- Verwende keine neuen Bibliotheken oder Frameworks, es sei denn, deren Nutzung ist im Projekt bereits etabliert oder wurde explizit genehmigt

### 5.4 Verifizierung ist entscheidend
- Nach Code-Änderungen (Fixes, Features) MÜSSEN Tests durchgeführt werden, um Korrektheit zu verifizieren
- Führe projektspezifische Build-, Linting- und Type-Checking-Befehle aus (z.B. `black`, `flake8`, `mypy`)

### 5.5 Frage bei Unsicherheit
- Nimm keine signifikanten Aktionen über den klaren Umfang der Anfrage hinaus vor, ohne dies mit dem Benutzer zu bestätigen

---

## 6. Development Conventions & Code Principles

### Code Style & Principles
- **Modular Monorepo:** Alle Geschäftslogik muss in `modules/<domain>/` untergebracht sein. Shared Code gehört in `modules/shared/`
- **Dependency Injection:** Services injizieren Repositories und andere Services. Globaler State wird vermieden
- **Transactional Safety:** Verwende `with db_connect(DB_NAME) as conn:` Context Manager für DB-Operationen
- **Logging:**
  - **Business Logic:** Verwende `modules.shared.log_service` (schreibt in SQL DB für Frontend-Anzeige)
  - **Technical Errors:** Verwende `modules.shared.app_logger` (schreibt in `logs/` Dateien zum Debuggen)
- **Configuration:** Alle Config via `.env` Dateien, geladen in `modules/shared/config/settings.py`
- **Frontend CSS:** Verwende `master.css` für Shared Styles, module-spezifische CSS nur für Unique Components
- **Central Navigation:** Alle Seiten verwenden `nav-loader.js` für dynamisches Menu Loading

### Database Interaction
- Verwende **Repositories** (`modules/shared/database/repositories/`) für ALLE DB-Zugriffe
- **SQLAlchemy Core** wird gegenüber ORM bevorzugt (bessere Performance und explizite Kontrolle)
- **Batch Operations:** Verwende Batch Inserts/Updates für große Datenmengen

### Documentation Rules
- **Live Docs:** Dokumentation in `docs/` wird wie Code behandelt. Aktualisiere sie unmittelbar bei Logik-Änderungen
- **Key Docs:**
  - `docs/CURRENT_STATUS.md`: Projektfortschritt und aktive Tasks
  - `docs/TODO_LIST.md`: Backlog und bekannte Issues
  - `docs/FIXES/OVERVIEW.md`: Lösungen für komplexe Bugs

---

## 7. Entwicklungsumgebung Setup

Die Entwicklungsumgebung läuft **parallel** zum produktiven System und ermöglicht sichere Entwicklung ohne Einfluss auf das Live-System.

### 7.1 Schnellstart
```bash
cd /pfad/zu/deinem/entwicklungsordner
./start_dev.sh
```

Server läuft dann auf: **http://localhost:8888**  
API-Dokumentation: **http://localhost:8888/docs**

### 7.2 Konfiguration

#### Port-Trennung
- **Produktion (PM2):** Port 8000 (Produktionssystem)
- **Development:** Port 8888 (geklonter Entwicklungsordner)

#### Datenbank
✅ **Shared Database** – Nutzt dieselbe SQL Server Datenbank wie Produktion
- Keine Konflikte da status-basierte Verarbeitung
- Test-Aufträge können mit eigenen Status-Flags markiert werden

#### APScheduler Jobs
🚫 **Deaktiviert in Development** (verhindert doppelte API Calls und Race Conditions)
- `sync_orders` – Deaktiviert
- `sync_inventory` – Deaktiviert

Konfiguration: `workers/config/workers_config.json` (beide Jobs: `"enabled": false`)

#### Environment Variablen
📁 Kopiert von Produktion: `modules/shared/config/.env`
- SQL Server Connection (shared)
- TEMU API Credentials (shared)
- JTL Configuration (shared)

---

## 8. Building & Running

### 8.1 Development Environment

Das Projekt nutzt eine Python Virtual Environment (`.venv`).

```bash
# 1. Virtuelle Umgebung aktivieren
source .venv/bin/activate

# 2. Dependencies installieren
pip install -r requirements.txt

# 3. Development Server starten (mit Auto-Reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8888
```

### 8.2 Production Deployment

Production wird von PM2 verwaltet.

```bash
# Start/Restart Applikation
pm2 start ecosystem.config.js
# ODER
pm2 restart temu-api

# Logs einsehen
pm2 logs temu-api
```

### 8.3 Manuelle Steuerung

#### Server starten (manuell)
```bash
cd /pfad/zu/deinem/entwicklungsordner
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8888
```

#### Dependencies aktualisieren
```bash
cd /pfad/zu/deinem/entwicklungsordner
source .venv/bin/activate
pip install -r requirements.txt
```

#### Python-Version prüfen
```bash
cd /pfad/zu/deinem/entwicklungsordner
source .venv/bin/activate
python --version  # Sollte Python 3.12+ zeigen
```

---

## 9. Git Workflow & Skip-Worktree

### 9.1 Standard Git Workflow

```bash
# Aktuellen Branch prüfen
git branch

# Neue Features entwickeln
git checkout -b feature/mein-feature

# Änderungen committen
git add .
git commit -m "feat: Beschreibung"

# Zurück zu main
git checkout main
git pull

# Feature-Branch mergen
git merge feature/mein-feature
```

**Aktueller Branch:** `feature/csv-bestellnummer`

### 9.2 Git Skip-Worktree (Dev-spezifische Konfiguration)

Folgende Dateien haben **lokale Änderungen** für die Entwicklungsumgebung, die **nicht** committed werden:
- `main.py` – Port 8888 statt 8000
- `workers/config/workers_config.json` – Jobs deaktiviert

Diese Dateien sind mit `git update-index --skip-worktree` markiert.

**Was bedeutet das?**
- ✅ Git ignoriert lokale Änderungen an diesen Dateien
- ✅ `git status` zeigt sie nicht als "modified"
- ✅ `git add .` fügt sie nicht hinzu
- ✅ Pull/Merge überschreibt die lokalen Änderungen NICHT

#### Skip-Worktree Dateien auflisten
```bash
git ls-files -v | grep ^S
```

#### Falls Änderungen doch committed werden sollen
```bash
# Skip-worktree temporär deaktivieren
git update-index --no-skip-worktree main.py workers/config/workers_config.json

# Änderungen committen
git add main.py workers/config/workers_config.json
git commit -m "fix: wichtige Änderung"

# Skip-worktree wieder aktivieren
git update-index --skip-worktree main.py workers/config/workers_config.json
```

#### Nach Git Clone neu einrichten
Falls du das Repo woanders klonst, musst du Skip-Worktree neu setzen:

```bash
# 1. Port und Jobs anpassen
# main.py → port=8888
# workers_config.json → enabled=false

# 2. Skip-Worktree aktivieren
git update-index --skip-worktree main.py workers/config/workers_config.json
```

---

## 10. Verifizierung

### 10.1 Beide Systeme parallel testen
```bash
# Produktion Status
pm2 status
# → temu-api sollte "online" sein

# Port-Nutzung prüfen
ss -tuln | grep -E '8000|8888'
# → 8000 LISTEN (Produktion)
# → 8888 LISTEN (Development, wenn gestartet)
```

### 10.2 Browser-Tests
- **Produktion:** http://192.168.178.x:8000/docs
- **Development:** http://localhost:8888/docs

### 10.3 API Health Check
```bash
# Produktion
curl http://localhost:8000/

# Development
curl http://localhost:8888/
```

---

## 11. Troubleshooting

### Port bereits belegt
```bash
# Prüfe welcher Prozess Port 8888 nutzt
sudo lsof -i :8888

# Prozess beenden falls nötig
kill -9 <PID>
```

### Datenbank-Verbindungsprobleme
```bash
# .env Datei prüfen
cat modules/shared/config/.env

# SQL Server Connection testen
python -c "from modules.shared.database import DatabaseManager; db = DatabaseManager(); print('✅ DB OK')"
```

### Module nicht gefunden
```bash
# PYTHONPATH auf aktuelles Verzeichnis setzen
export PYTHONPATH=$(pwd)

# Oder in start_dev.sh ergänzen
```

---

## 12. Current Status (13. Februar 2026)

### Stabil & Abgeschlossen
- ✅ TEMU Order/Inventory Sync
- ✅ PDF Reader (inkl. Refactoring + Security Fixes)
- ✅ CSV Verarbeiter (JTL→DATEV) – vollständig migriert und in Produktion
- ✅ Frontend Architecture (CSS Consolidation, Central Navigation)
- ✅ JTL XML-Export (Refactoring + Critical Bug Fix)

### Kürzliche Achievements (13. Feb 2026)
- ✅ TEMU Module Refactoring (6 Prioritäten, God Methods aufgelöst, BaseWorkflowService, 15+ Constants)
- ✅ Shared Module Refactoring (DRY, Dead Code, Security Fixes, Log Rotation, SQL Injection Fix)
- ✅ JTL XML-Export Refactoring (Silent Data Loss behoben, Control-Char Sanitization)
- ✅ PDF Reader Refactoring (Security Fixes, MwSt-Extraktion, Shipping Services Format)
- ✅ CSS Consolidation eliminierte 1,537 Zeilen Duplikate (44% Reduktion)
- ✅ Zentrale Navigation für alle Module implementiert

---

## 13. Wie dieser Leitfaden verwendet werden soll

Zu Beginn jeder neuen Entwicklungssitzung sollte die AI angewiesen werden, diesen `AI_GUIDE.md` zu lesen. Dies stellt sicher, dass die AI über den aktuellsten Projektkontext und die geltenden Arbeitsprinzipien informiert ist.

**Beispiel-Prompt:**
> "Lies dir die Datei `AI_GUIDE.md` durch und befolge die dort enthaltenen Anweisungen, um dich mit dem Projekt vertraut zu machen."

---

**Ende des AI Project Guide**
