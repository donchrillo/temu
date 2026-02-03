# 🚀 Vollständige Monorepo-Migration - Der ECHTE Plan

**Status**: Nur 40% fertig! Viel mehr zu tun als gedacht.
**Datum**: 2. Februar 2026
**Branch**: `feature/monorepo-restructure`

---

## 🎯 ZIEL-Struktur (das wolltet ihr erreichen):

```
/home/chx/temu/
├── main.py                      # Unified Gateway
├── modules/                     # ALLE Module hier
│   ├── shared/                 # Gemeinsame Infrastruktur
│   │   ├── database/          # Alles aus src/db/
│   │   ├── repositories/      # Alles aus src/db/repositories/
│   │   ├── logging/           # Alles aus src/services/
│   │   ├── config/            # Alles aus config/
│   │   └── connectors/        # Alles aus src/marketplace_connectors/
│   │
│   ├── pdf_reader/            # PDF Modul (KOMPLETT)
│   │   ├── __init__.py
│   │   ├── router.py          ✅ DA
│   │   ├── frontend/          ✅ DA
│   │   └── services/          ❌ FEHLT!
│   │       ├── config.py
│   │       ├── rechnungen_service.py
│   │       ├── werbung_service.py
│   │       ├── werbung_extraction_service.py
│   │       ├── document_identifier.py
│   │       ├── patterns.py
│   │       └── logger.py
│   │
│   └── temu/                  # TEMU Modul (KOMPLETT)
│       ├── __init__.py
│       ├── router.py          ✅ DA
│       ├── jobs.py            ✅ DA
│       ├── frontend/          ✅ DA
│       └── services/          ❌ FEHLT!
│           ├── config.py
│           ├── order_service.py
│           ├── inventory_service.py
│           ├── tracking_service.py
│           ├── stock_sync_service.py
│           ├── order_workflow_service.py
│           └── inventory_workflow_service.py
│
├── workers/                   # Job Scheduler (bleibt)
├── data/                      # Runtime Data (bleibt)
├── logs/                      # Logs (bleibt)
└── docs/                      # Documentation (bleibt)

❌ GELÖSCHT:
├── api/                       # Komplett weg
├── src/                       # Komplett weg
└── workflows/                 # Optional: Zu modules/temu/cli/ migrieren
```

---

## 📊 IST-Zustand vs. SOLL-Zustand

### Was schon migriert ist (40%):

✅ **Shared-Modul** (als Re-Export Layer):
- `modules/shared/` existiert
- Re-exportiert src/db, src/services, config
- Aber: Ist nur ein Wrapper, nicht die echten Dateien!

✅ **PDF-Modul** (Router-Schicht):
- `modules/pdf_reader/router.py` ✅
- `modules/pdf_reader/frontend/` ✅
- Aber: Services fehlen!

✅ **TEMU-Modul** (Router-Schicht):
- `modules/temu/router.py` ✅
- `modules/temu/jobs.py` ✅
- `modules/temu/frontend/` ✅
- Aber: Services fehlen!

✅ **Unified Gateway**:
- `main.py` existiert und funktioniert
- Bindet Module als Router ein

### Was FEHLT (60%):

❌ **PDF Services nicht migriert**:
```
src/modules/pdf_reader/          → modules/pdf_reader/services/
├── config.py                    → services/config.py
├── rechnungen_service.py        → services/rechnungen_service.py
├── werbung_service.py           → services/werbung_service.py
├── werbung_extraction_service.py → services/werbung_extraction_service.py
├── document_identifier.py       → services/document_identifier.py
├── patterns.py                  → services/patterns.py
└── logger.py                    → services/logger.py
```

❌ **TEMU Services nicht migriert**:
```
src/modules/temu/               → modules/temu/services/
├── config.py                   → services/config.py
├── order_service.py            → services/order_service.py
├── inventory_service.py        → services/inventory_service.py
├── tracking_service.py         → services/tracking_service.py
├── stock_sync_service.py       → services/stock_sync_service.py
├── order_workflow_service.py   → services/order_workflow_service.py
└── inventory_workflow_service.py → services/inventory_workflow_service.py
```

❌ **Shared-Module nicht komplett migriert**:
```
src/db/                         → modules/shared/database/
src/services/                   → modules/shared/logging/
src/marketplace_connectors/     → modules/shared/connectors/
config/                         → modules/shared/config/
```

❌ **PM2 läuft noch mit altem Server**:
```
ecosystem.config.js → script: "api.server:app"  ❌
Sollte: script: "main:app"  ✅
```

---

## 🗺️ Vollständiger Migrationsplan

### Phase 1: PDF Services migrieren 📄

**Schritt 1.1**: Verzeichnis erstellen
```bash
mkdir -p modules/pdf_reader/services
touch modules/pdf_reader/services/__init__.py
```

**Schritt 1.2**: Services kopieren und Imports anpassen
```bash
# Kopiere alle Service-Dateien
cp src/modules/pdf_reader/*.py modules/pdf_reader/services/

# Imports in allen Dateien anpassen:
# Alt: from src.modules.pdf_reader.config import ...
# Neu: from modules.pdf_reader.services.config import ...

# Alt: from src.services.log_service import ...
# Neu: from modules.shared import log_service
```

**Schritt 1.3**: Router anpassen
```python
# modules/pdf_reader/router.py
# Alt:
from src.modules.pdf_reader.werbung_service import process_ad_pdfs

# Neu:
from .services.werbung_service import process_ad_pdfs
```

**Schritt 1.4**: Testen
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8001
curl http://127.0.0.1:8001/api/pdf/health
```

---

### Phase 2: TEMU Services migrieren 🚀

**Schritt 2.1**: Verzeichnis erstellen
```bash
mkdir -p modules/temu/services
touch modules/temu/services/__init__.py
```

**Schritt 2.2**: Services kopieren und Imports anpassen
```bash
# Kopiere alle Service-Dateien
cp src/modules/temu/*.py modules/temu/services/

# Imports anpassen in allen Dateien
# Alt: from src.modules.temu.order_service import ...
# Neu: from modules.temu.services.order_service import ...
```

**Schritt 2.3**: Router & Jobs anpassen
```python
# modules/temu/router.py & jobs.py
# Alt:
from src.modules.temu.order_workflow_service import run_order_workflow

# Neu:
from .services.order_workflow_service import run_order_workflow
```

**Schritt 2.4**: Testen
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8001
curl http://127.0.0.1:8001/api/temu/stats
```

---

### Phase 3: Shared-Module komplett migrieren 🔧

**Schritt 3.1**: Database migrieren
```bash
# modules/shared/database/ wird echtes Modul statt Re-Export
mv src/db/* modules/shared/database/
rm -rf src/db/
```

**Schritt 3.2**: Logging migrieren
```bash
mv src/services/* modules/shared/logging/
rm -rf src/services/
```

**Schritt 3.3**: Connectors migrieren
```bash
mkdir -p modules/shared/connectors
mv src/marketplace_connectors/* modules/shared/connectors/
rm -rf src/marketplace_connectors/
```

**Schritt 3.4**: Config migrieren
```bash
mv config/* modules/shared/config/
# Symlink erstellen für Rückwärtskompatibilität
ln -s modules/shared/config config
```

**Schritt 3.5**: modules/shared/__init__.py aktualisieren
```python
# Jetzt echte Imports statt Re-Exports
from .database.connection import get_engine, db_connect
from .repositories.base import BaseRepository
from .logging.log_service import log_service
# etc.
```

---

### Phase 4: Alte Struktur löschen 🗑️

**Erst wenn ALLES migriert und getestet ist!**

```bash
# src/ komplett löschen
rm -rf src/

# api/ löschen (nach PM2-Umstellung)
rm -rf api/

# Optional: workflows/ migrieren oder löschen
# mv workflows/ modules/temu/cli/
```

---

### Phase 5: PM2 umstellen ⚡

**Erst NACH Phase 1-4!**

```bash
# Neue Config erstellen
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: "temu-api",
    script: "/home/chx/temu/.venv/bin/python3",
    args: "-m uvicorn main:app --host 0.0.0.0 --port 8000",
    cwd: "/home/chx/temu",
    env: {
      PYTHONPATH: "/home/chx/temu"
    }
  }]
};
EOF

# PM2 neu starten
pm2 delete temu-api
pm2 start ecosystem.config.js
pm2 save
```

---

## ⚠️ WICHTIGE Hinweise:

### 1. Import-Pfade
**Alle Imports müssen geändert werden!**

```python
# ❌ ALT (wird nicht mehr funktionieren):
from src.modules.temu.order_service import ...
from src.db.repositories.temu.order_repository import ...
from src.services.log_service import ...

# ✅ NEU:
from modules.temu.services.order_service import ...
from modules.shared.database.repositories.temu.order_repository import ...
from modules.shared import log_service
```

### 2. Relative Imports innerhalb Module
```python
# In modules/temu/services/order_workflow_service.py

# ❌ ALT:
from src.modules.temu.order_service import import_orders

# ✅ NEU:
from .order_service import import_orders  # Relative Import innerhalb Modul
```

### 3. Circular Import Probleme
Beim Migrieren auf echte Module statt Re-Exports können circular imports auftreten. Lösung:
- Late imports (import innerhalb Funktion)
- Dependency Injection
- Interface-Abstraktion

---

## 📝 Checkliste für jede Phase:

Für jede Phase:
- [ ] Dateien kopiert
- [ ] Alle Imports angepasst
- [ ] Relative Imports wo möglich
- [ ] Tests laufen (pytest)
- [ ] API-Endpoints funktionieren
- [ ] Frontend funktioniert
- [ ] PM2 restart erfolgreich
- [ ] Commit mit aussagekräftiger Message

---

## 🎯 Erwartetes Endergebnis:

### Ordnerstruktur:
```bash
$ ls -la
drwxrwxr-x  modules/      # ALLE Module hier
drwxrwxr-x  workers/      # Job Scheduler
drwxrwxr-x  data/         # Runtime Data
drwxrwxr-x  logs/         # Logs
drwxrwxr-x  docs/         # Docs
-rw-rw-r--  main.py       # Unified Gateway
-rw-rw-r--  ecosystem.config.js
-rw-rw-r--  requirements.txt

# GELÖSCHT:
# api/
# src/
# config/ (symlink → modules/shared/config)
```

### Import Style:
```python
# Jeder kann Module importieren:
from modules.shared import log_service, get_engine
from modules.pdf_reader import get_router as get_pdf_router
from modules.temu import get_router as get_temu_router

# Innerhalb Module: relative Imports
from .services.order_service import import_orders
from ..shared import log_service
```

---

## 🚀 Sollen wir jetzt starten?

**Vorschlag**: Wir machen Phase für Phase:

1. **Phase 1**: PDF Services migrieren (30 Min)
2. **Testen**: Alles funktioniert? (10 Min)
3. **Phase 2**: TEMU Services migrieren (30 Min)
4. **Testen**: Alles funktioniert? (10 Min)
5. **Phase 3**: Shared komplett migrieren (45 Min)
6. **Phase 4**: Alte Struktur löschen (5 Min)
7. **Phase 5**: PM2 umstellen (10 Min)

**Gesamt**: ~2.5 Stunden

Oder wollt ihr erstmal nur **Phase 1** machen und dann schauen?
