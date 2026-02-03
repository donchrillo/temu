# 🚀 Monorepo Migration - Status & Plan

**Branch:** `feature/monorepo-restructure`
**Letzte Aktualisierung:** 3. Februar 2026 11:30
**Status:** 70% abgeschlossen - In Bearbeitung

---

## 📍 AKTUELLER STAND (Wo sind wir?)

### ✅ Was bereits funktioniert:

1. **PM2 läuft mit main.py** ✅
   - `ecosystem.config.js` nutzt bereits `uvicorn main:app`
   - Gateway ist funktional

2. **Module-Struktur existiert:**
   ```
   modules/
   ├── shared/           ✅ Existiert (aber nur Re-Export Layer)
   ├── pdf_reader/       ✅ Router + Frontend + Services (migriert)
   └── temu/             ✅ Router + Jobs + Frontend + Services (migriert)
   ```

3. **Services sind kopiert:**
   - `modules/temu/services/` - Alle TEMU Services ✅
   - `modules/pdf_reader/services/` - Alle PDF Services ✅

### ⚠️ PROBLEM - Was noch nicht passt:

1. **DUPLIKATE existieren:**
   ```
   modules/temu/services/        ← NEU (kopiert am 2. Feb)
   src/modules/temu/             ← ALT (Original)

   modules/pdf_reader/services/  ← NEU (kopiert am 2. Feb)
   src/modules/pdf_reader/       ← ALT (Original)
   ```

2. **modules/shared/ ist nur Re-Export Layer:**
   - Importiert von `src/db/`, `src/services/`, `config/`
   - Die echten Dateien sind nicht migriert

3. **Alte Struktur existiert noch:**
   - `src/` (komplett)
   - `api/` (mit altem server.py)
   - `config/` (nicht migriert)

4. **Imports zeigen noch auf alte Struktur:**
   - Alle Services importieren von `src.*`
   - Müssen auf `modules.*` umgestellt werden

---

## 🎯 ZIEL-Struktur (Wo wollen wir hin?)

```
/home/chx/temu/
├── main.py                      # Unified Gateway ✅
├── ecosystem.config.js          # PM2 Config ✅
├── requirements.txt             # Dependencies ✅
├── db_schema.sql                # Schema ✅
│
├── modules/                     # ALLE Module hier
│   ├── shared/                 # Gemeinsame Infrastruktur
│   │   ├── __init__.py
│   │   ├── database/          # Von src/db/
│   │   │   ├── __init__.py
│   │   │   ├── connection.py
│   │   │   └── repositories/
│   │   ├── connectors/        # Von src/marketplace_connectors/
│   │   │   └── temu/
│   │   ├── logging/           # Von src/services/
│   │   │   ├── __init__.py
│   │   │   ├── logger.py
│   │   │   └── log_service.py
│   │   └── config/            # Von config/
│   │       ├── __init__.py
│   │       └── settings.py
│   │
│   ├── pdf_reader/            # PDF Modul
│   │   ├── __init__.py
│   │   ├── router.py          ✅
│   │   ├── frontend/          ✅
│   │   └── services/          ✅ (Imports müssen angepasst werden)
│   │
│   └── temu/                  # TEMU Modul
│       ├── __init__.py
│       ├── router.py          ✅
│       ├── jobs.py            ✅
│       ├── frontend/          ✅
│       └── services/          ✅ (Imports müssen angepasst werden)
│
├── workers/                   # Job Scheduler ✅
├── data/                      # Runtime Data ✅
├── logs/                      # Logs ✅
└── docs/                      # Documentation ✅

❌ GELÖSCHT (nach Migration):
├── api/                       # Komplett weg
├── src/                       # Komplett weg
└── config/                    # → modules/shared/config/
```

---

## 📋 MIGRATIONS-PLAN (Schritt für Schritt)

### ✅ Phase 0: Vorbereitung (FERTIG)

- [x] Migrations-Status-Dokument erstellt
- [x] Todo-Liste angelegt
- [x] Aktuellen Stand analysiert

---

### 🔄 Phase 1: Shared-Module komplett migrieren

**Ziel:** modules/shared/ wird zu echtem Modul (nicht Re-Export)

**Schritte:**

#### 1.1 Database migrieren
```bash
# Erstelle Zielverzeichnis
mkdir -p modules/shared/database/repositories

# Kopiere Database Layer
cp -r src/db/* modules/shared/database/

# Prüfe, dass alles kopiert wurde
ls -la modules/shared/database/
```

**Checkpoint:** Database-Dateien in modules/shared/database/ ✅

#### 1.2 Connectors migrieren
```bash
# Erstelle Zielverzeichnis
mkdir -p modules/shared/connectors

# Kopiere Marketplace Connectors
cp -r src/marketplace_connectors/* modules/shared/connectors/

# Prüfe
ls -la modules/shared/connectors/
```

**Checkpoint:** Connectors in modules/shared/connectors/ ✅

#### 1.3 Logging migrieren
```bash
# Erstelle Zielverzeichnis
mkdir -p modules/shared/logging

# Kopiere Services
cp -r src/services/* modules/shared/logging/

# Prüfe
ls -la modules/shared/logging/
```

**Checkpoint:** Logging in modules/shared/logging/ ✅

#### 1.4 Config migrieren
```bash
# Erstelle Zielverzeichnis
mkdir -p modules/shared/config

# Kopiere Config
cp -r config/* modules/shared/config/

# Erstelle Symlink für Rückwärtskompatibilität (temporär)
ln -s modules/shared/config config_backup
```

**Checkpoint:** Config in modules/shared/config/ ✅

#### 1.5 modules/shared/__init__.py neu schreiben
```python
# Jetzt echte Imports statt Re-Exports
from .database.connection import get_engine, db_connect
from .database.repositories.base import BaseRepository
from .logging.log_service import log_service
from .logging.logger import create_module_logger
# etc.
```

**Checkpoint:** modules/shared/__init__.py aktualisiert ✅

**Commit nach Phase 1:**
```bash
git add modules/shared/
git commit -m "feat(monorepo): Migrate shared modules (database, connectors, logging, config)"
```

---

### 🔄 Phase 2: Imports in modules/temu anpassen

**Ziel:** Alle Imports in modules/temu/services/ zeigen auf modules/

**Schritte:**

#### 2.1 Alle Imports finden
```bash
# Liste alle src.* Imports
grep -r "from src\." modules/temu/services/
grep -r "import src\." modules/temu/services/
```

#### 2.2 Imports anpassen
Für jede Datei in `modules/temu/services/`:

**Alt:**
```python
from src.db.repositories.temu.order_repository import OrderRepository
from src.modules.temu.order_service import import_orders
from src.services.log_service import log_service
from src.marketplace_connectors.temu.service import TemuService
```

**Neu:**
```python
from modules.shared.database.repositories.temu.order_repository import OrderRepository
from .order_service import import_orders  # Relative Import innerhalb Modul
from modules.shared.logging.log_service import log_service
from modules.shared.connectors.temu.service import TemuService
```

#### 2.3 Testen
```bash
# Syntax-Check
python -m py_compile modules/temu/services/*.py

# Import-Test
python -c "from modules.temu.services.order_service import OrderService"
```

**Checkpoint:** Alle Imports in modules/temu/ angepasst ✅

**Commit nach Phase 2:**
```bash
git add modules/temu/
git commit -m "refactor(temu): Update imports to use modules/ structure"
```

---

### 🔄 Phase 3: Imports in modules/pdf_reader anpassen

**Ziel:** Alle Imports in modules/pdf_reader/services/ zeigen auf modules/

**Schritte:** (analog zu Phase 2)

#### 3.1 Imports finden und anpassen
```bash
# Finde alte Imports
grep -r "from src\." modules/pdf_reader/services/

# Passe an (siehe Phase 2 für Beispiele)
```

#### 3.2 Testen
```bash
python -m py_compile modules/pdf_reader/services/*.py
python -c "from modules.pdf_reader.services.werbung_service import process_ad_pdfs"
```

**Checkpoint:** Alle Imports in modules/pdf_reader/ angepasst ✅

**Commit nach Phase 3:**
```bash
git add modules/pdf_reader/
git commit -m "refactor(pdf_reader): Update imports to use modules/ structure"
```

---

### 🔄 Phase 4: Imports in workers/ anpassen

**Ziel:** workers/ nutzt modules/ statt src/

**Schritte:**

#### 4.1 workers/worker_service.py anpassen
**Alt:**
```python
from src.modules.temu.order_workflow_service import run_order_workflow
```

**Neu:**
```python
from modules.temu.services.order_workflow_service import run_order_workflow
```

#### 4.2 Testen
```bash
python -m py_compile workers/*.py
```

**Checkpoint:** workers/ nutzt modules/ ✅

**Commit nach Phase 4:**
```bash
git add workers/
git commit -m "refactor(workers): Update imports to use modules/ structure"
```

---

### 🔄 Phase 5: Imports in main.py anpassen

**Ziel:** main.py nutzt modules/ statt src/

**Schritte:**

#### 5.1 main.py anpassen
Prüfe alle Imports und passe an.

#### 5.2 Test lokal
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8001
curl http://127.0.0.1:8001/api/health
curl http://127.0.0.1:8001/api/temu/stats
curl http://127.0.0.1:8001/api/pdf/health
```

**Checkpoint:** main.py funktioniert mit modules/ ✅

**Commit nach Phase 5:**
```bash
git add main.py
git commit -m "refactor(main): Update imports to use modules/ structure"
```

---

### 🔄 Phase 6: Alte Struktur löschen

**⚠️ NUR WENN ALLES FUNKTIONIERT!**

**Schritte:**

#### 6.1 Backup erstellen
```bash
# Tar-Archive als Backup
tar -czf backup_src_$(date +%Y%m%d).tar.gz src/
tar -czf backup_api_$(date +%Y%m%d).tar.gz api/
tar -czf backup_config_$(date +%Y%m%d).tar.gz config/

# Backups in sicheren Ort verschieben
mv backup_*.tar.gz ~/backups/
```

#### 6.2 Alte Verzeichnisse löschen
```bash
# VORSICHT: Nur wenn Phase 1-5 erfolgreich!
rm -rf src/
rm -rf api/
rm -rf config/  # Nur wenn Symlink nicht mehr nötig
```

**Checkpoint:** Alte Struktur entfernt ✅

**Commit nach Phase 6:**
```bash
git add -A
git commit -m "chore(monorepo): Remove old src/, api/, config/ structure"
```

---

### 🔄 Phase 7: Tests und Deployment

**Schritte:**

#### 7.1 Alle Tests lokal
```bash
# Python Syntax
find modules/ -name "*.py" -exec python -m py_compile {} \;

# Unit Tests (falls vorhanden)
pytest

# API Tests
python -m uvicorn main:app --host 127.0.0.1 --port 8001 &
sleep 5
curl http://127.0.0.1:8001/api/health
curl http://127.0.0.1:8001/api/temu/stats
kill %1
```

#### 7.2 PM2 Restart auf Server
```bash
# Auf Server
pm2 restart temu-api
pm2 logs temu-api --lines 50

# Prüfe Endpoints
curl http://192.168.178.4:8000/api/health
```

#### 7.3 Frontend-Test
```
Browser öffnen:
- http://192.168.178.4:8000/
- http://192.168.178.4:8000/temu
- http://192.168.178.4:8000/pdf

Teste:
- [ ] Dashboard lädt
- [ ] TEMU Jobs werden angezeigt
- [ ] PDF Upload funktioniert
- [ ] WebSocket zeigt Live-Updates
```

**Checkpoint:** Alles funktioniert in Produktion ✅

**Final Commit:**
```bash
git add -A
git commit -m "feat(monorepo): Complete monorepo migration - all modules in modules/"
git push origin feature/monorepo-restructure
```

---

## 🆘 Rollback-Plan (Falls etwas schiefgeht)

### Nach Phase 1-5 (Imports angepasst, src/ noch da):
```bash
# Einfach zum letzten funktionierenden Commit zurück
git log --oneline -10
git reset --hard <commit-hash>
```

### Nach Phase 6 (src/ gelöscht, aber Fehler):
```bash
# Backup wiederherstellen
cd ~
tar -xzf backups/backup_src_*.tar.gz -C /home/chx/temu/
tar -xzf backups/backup_api_*.tar.gz -C /home/chx/temu/
tar -xzf backups/backup_config_*.tar.gz -C /home/chx/temu/

# Git zurücksetzen
git reset --hard <commit-vor-phase-6>
```

---

## 📝 Fortschritt-Tracking

Nach jedem Schritt:
1. ✅ Checkpoint markieren
2. 💾 Git Commit
3. 📋 Dieses Dokument aktualisieren
4. 🧪 Kurzer Test

**Aktueller Fortschritt:**
- [x] Phase 0: Vorbereitung ✅
- [ ] Phase 1: Shared-Module migrieren
- [ ] Phase 2: Imports modules/temu
- [ ] Phase 3: Imports modules/pdf_reader
- [ ] Phase 4: Imports workers/
- [ ] Phase 5: Imports main.py
- [ ] Phase 6: Alte Struktur löschen
- [ ] Phase 7: Tests & Deployment

---

## 💡 Wichtige Hinweise

### Bei Session-Abbruch:
1. Lies dieses Dokument von oben
2. Prüfe "Aktueller Fortschritt"
3. Schau dir den letzten Commit an: `git log -1`
4. Mache beim nächsten nicht-erledigten Schritt weiter

### Import-Pfade nach Migration:
```python
# ✅ NEU (nach Migration):
from modules.shared import db_connect, log_service, get_engine
from modules.shared.database.repositories.temu.order_repository import OrderRepository
from modules.shared.connectors.temu.service import TemuService
from modules.temu.services.order_service import OrderService

# Innerhalb Module: relative Imports
from .order_service import import_orders
from ..shared import log_service
```

### Testen während Migration:
```bash
# Nach jedem Import-Change:
python -m py_compile <geänderte-datei>.py

# Nach jeder Phase:
python -m uvicorn main:app --host 127.0.0.1 --port 8001
# → Dann curl-Tests
```

---

**Nächster Schritt:** Phase 1.1 - Database migrieren
**Bereit zum Starten?** Ja! 🚀
