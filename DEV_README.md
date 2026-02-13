# TEMU API - Entwicklungsumgebung

Diese Entwicklungsumgebung läuft parallel zum produktiven System und ermöglicht sichere Entwicklung ohne Einfluss auf das Live-System.

## 🚀 Schnellstart

```bash
cd /pfad/zu/deinem/entwicklungsordner
./start_dev.sh
```

Der Server läuft dann auf: **http://localhost:8888**

API-Dokumentation: **http://localhost:8888/docs**

## 📋 Konfiguration

### Port-Trennung
- **Produktion (PM2):** Port 8000 - läuft auf Produktionssystem
- **Development:** Port 8888 - läuft in geklontem Entwicklungsordner

### Datenbank
✅ **Shared Database** - Nutzt dieselbe SQL Server Datenbank wie Produktion
- Keine Konflikte da status-basierte Verarbeitung
- Test-Aufträge können mit eigenen Status-Flags markiert werden

### APScheduler Jobs
🚫 **Deaktiviert in Development**
- `sync_orders` - Deaktiviert (verhindert doppelte TEMU API Calls)
- `sync_inventory` - Deaktiviert (verhindert Race Conditions)

Konfiguration: `workers/config/workers_config.json` (beide Jobs: `"enabled": false`)

### Environment Variablen
📁 **Kopiert von Produktion:** `modules/shared/config/.env`
- SQL Server Connection (shared)
- TEMU API Credentials (shared)
- JTL Configuration (shared)

## 🔄 Git Workflow

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

### 🔒 Git Skip-Worktree (Dev-spezifische Konfiguration)

Die folgenden Dateien haben **lokale Änderungen** für die Entwicklungsumgebung, die **nicht** committed werden:

- `main.py` - Port 8888 statt 8000
- `workers/config/workers_config.json` - Jobs deaktiviert

Diese Dateien sind mit `git update-index --skip-worktree` markiert.

**Was bedeutet das?**
- ✅ Git ignoriert lokale Änderungen an diesen Dateien
- ✅ `git status` zeigt sie nicht als "modified"
- ✅ `git add .` fügt sie nicht hinzu
- ✅ Pull/Merge überschreibt die lokalen Änderungen NICHT

**Skip-Worktree Dateien auflisten:**
```bash
git ls-files -v | grep ^S
```

**Falls du doch Änderungen an diesen Dateien committen musst:**
```bash
# Skip-worktree temporär deaktivieren
git update-index --no-skip-worktree main.py workers/config/workers_config.json

# Änderungen committen
git add main.py workers/config/workers_config.json
git commit -m "fix: wichtige Änderung"

# Skip-worktree wieder aktivieren
git update-index --skip-worktree main.py workers/config/workers_config.json
```

**Nach Git Clone neu einrichten:**

Falls du das Repo woanders nochmal klonst, musst du Skip-Worktree neu setzen:

```bash
# 1. Port und Jobs anpassen
# main.py → port=8888
# workers_config.json → enabled=false

# 2. Skip-Worktree aktivieren
git update-index --skip-worktree main.py workers/config/workers_config.json
```

## 📂 Verzeichnisstruktur

```
entwicklungsordner/           # Repo-Root (wo auch immer geklont)
├── .venv/                    # Virtuelle Python-Umgebung
├── data/                     # Daten (von .gitignore ausgeschlossen)
│   ├── pdf_reader/
│   │   ├── eingang/rechnungen/
│   │   ├── eingang/werbung/
│   │   ├── ausgang/
│   │   └── tmp/
│   ├── csv_verarbeiter/
│   │   ├── eingang/
│   │   ├── ausgang/
│   │   └── tmp/
│   └── temu/
│       ├── export/
│       └── xml/
├── logs/                     # Logs (von .gitignore ausgeschlossen)
│   ├── app/
│   ├── pdf_reader/
│   ├── temu/
│   └── csv_verarbeiter/
└── start_dev.sh             # Start-Skript
```

## 🛠️ Manuelle Steuerung

### Server starten (manuell)
```bash
cd /pfad/zu/deinem/entwicklungsordner
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8888
```

### Dependencies aktualisieren
```bash
cd /pfad/zu/deinem/entwicklungsordner
source .venv/bin/activate
pip install -r requirements.txt
```

### Python-Version prüfen
```bash
cd /pfad/zu/deinem/entwicklungsordner
source .venv/bin/activate
python --version  # Sollte Python 3.11+ zeigen
```

## ✅ Verifizierung

### Beide Systeme parallel testen
```bash
# Produktion Status
pm2 status
# → temu-api sollte "online" sein

# Port-Nutzung prüfen
ss -tuln | grep -E '8000|8888'
# → 8000 LISTEN (Produktion)
# → 8888 LISTEN (Development, wenn gestartet)
```

### Browser-Tests
- **Produktion:** http://192.168.178.x:8000/docs
- **Development:** http://localhost:8888/docs

### API Health Check
```bash
# Produktion
curl http://localhost:8000/

# Development
curl http://localhost:8888/
```

## 🔍 Troubleshooting

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

## 📚 Weitere Dokumentation

- **Projektübersicht:** [AI_GUIDE.md](AI_GUIDE.md)
- **Aktuelle TODOs:** [docs/TODO_LIST.md](docs/TODO_LIST.md)
- **CSV Verarbeiter:** [modules/csv_verarbeiter/FUNKTIONALITAET_AKTUELL.md](modules/csv_verarbeiter/FUNKTIONALITAET_AKTUELL.md)
- **Deployment:** [docs/DEPLOYMENT/architecture.md](docs/DEPLOYMENT/architecture.md)

## ⚠️ Wichtige Hinweise

1. **Nie direkt im Produktionsverzeichnis entwickeln** - Immer separaten Entwicklungsordner nutzen
2. **Jobs in Development deaktiviert lassen** - Sonst doppelte API-Calls
3. **Git-Änderungen nur von Development committen** - Produktion ist stabil
4. **PM2 nicht aus versehen stoppen** - Produktion läuft 24/7
5. **Skip-Worktree für main.py und workers_config.json** - Lokale Änderungen werden nicht committed

---

**Stand:** 13. Februar 2026
**Python:** 3.12.3
**Branch:** feature/csv-bestellnummer
