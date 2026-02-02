# 🧹 Monorepo Migration - Cleanup & Finalisierung

**Status**: Migration zu 95% abgeschlossen, Cleanup ausstehend
**Datum**: 2. Februar 2026
**Branch**: `feature/monorepo-restructure`

---

## 📊 Analyse-Ergebnisse

### ✅ Was bereits funktioniert:

1. **Neue Modul-Struktur ist vollständig**:
   ```
   modules/shared/       → Re-Export Layer (Database, Logging, Config)
   modules/pdf_reader/   → Router + Frontend (verwendet src/modules/pdf_reader Services)
   modules/temu/         → Router + Frontend + Jobs (verwendet src/modules/temu Services)
   ```

2. **Unified Gateway (main.py) ist funktional**:
   - Bindet beide Module ein (/api/pdf, /api/temu)
   - Hat Job Management Endpoints
   - Hat WebSocket Support
   - Serviert Frontends direkt aus Modulen
   - **18 Endpoints** gesamt (11 PDF via Router, 5 TEMU via Router, 2 Gateway)

3. **Alte Business Logic wird wiederverwendet** (kein Duplicate!):
   - `src/modules/temu/` enthält Business Logic Services
   - `src/modules/pdf_reader/` enthält PDF Processing Services
   - Neue Module sind nur dünne Router-Schichten
   - **Das ist GUTES Design!**

---

## ⚠️ Was NICHT konsistent ist:

### 1. PM2 läuft noch mit altem Server

**Problem**:
```javascript
// ecosystem.config.js
script: "api.server:app"  ❌ ALT (508 Zeilen, 27 Endpoints)

// Sollte sein:
script: "main:app"        ✅ NEU (380 Zeilen, 18 Endpoints + 16 via Module-Router)
```

**Warum ist das ein Problem?**:
- Benutzer sieht neue Frontends, aber Backend läuft alte Version
- Änderungen an `main.py` haben keine Wirkung
- Verwirrung: "Welche Datei ist die Wahrheit?"

### 2. Alte api/server.py existiert noch

**Was ist drin?**:
- Alte PDF-Endpoints (direkt implementiert, nicht über Router)
- Job Management (identisch zu main.py)
- WebSocket (identisch zu main.py)
- Frontend Serving (ähnlich zu main.py)

**Kann gelöscht werden?**
- ⚠️ **Erst nach PM2-Umstellung!**
- Dann umbenennen zu `api/server.py.OLD` als Backup

---

## 🎯 Cleanup-Plan (Step by Step)

### **Phase 1: PM2 auf main.py umstellen** ⚡ KRITISCH

**Schritt 1.1**: Prüfe, ob main.py alle Features hat
```bash
# Test main.py lokal
python -m uvicorn main:app --host 127.0.0.1 --port 8001

# Test Endpoints:
curl http://127.0.0.1:8001/api/health
curl http://127.0.0.1:8001/api/pdf/health
curl http://127.0.0.1:8001/api/temu/stats
curl http://127.0.0.1:8001/

# Wenn alles funktioniert → Weiter!
```

**Schritt 1.2**: Erstelle neue PM2-Config
```bash
# Backup alte Config
cp ecosystem.config.js ecosystem.config.OLD.js

# Erstelle neue Config
cat > ecosystem-monorepo.config.js << 'EOF'
module.exports = {
  apps: [{
    name: "temu-api",
    script: "/home/chx/temu/.venv/bin/python3",
    args: "-m uvicorn main:app --host 0.0.0.0 --port 8000",
    cwd: "/home/chx/temu",
    env: {
      PYTHONPATH: "/home/chx/temu"
    },
    max_memory_restart: "500M",
    error_file: "./logs/pm2-error.log",
    out_file: "./logs/pm2-out.log",
    merge_logs: true,
    autorestart: true
  }]
};
EOF
```

**Schritt 1.3**: PM2 umstellen
```bash
# Stoppe alte App
pm2 stop temu-api

# Lösche alte App aus PM2
pm2 delete temu-api

# Starte mit neuer Config
pm2 start ecosystem-monorepo.config.js

# Prüfe Status
pm2 status
pm2 logs temu-api --lines 50

# Teste Endpoints
curl http://192.168.178.4:8000/api/health
```

**Schritt 1.4**: Wenn alles funktioniert
```bash
# Ersetze alte Config
mv ecosystem.config.js ecosystem.config.OLD.js
mv ecosystem-monorepo.config.js ecosystem.config.js

# Committe Änderung
git add ecosystem.config.js
git commit -m "chore: Switch PM2 to main.py (unified gateway)"
```

---

### **Phase 2: Alte Dateien aufräumen** 🗑️

**Was kann gelöscht werden:**

```bash
# 1. Alten API-Server als Backup behalten
mv api/server.py api/server.py.OLD
git add api/server.py.OLD
git rm api/server.py

# 2. Backup-Datei entfernen (nicht committen)
rm api/server.py.backup

# 3. Alte Frontend-Dateien (bereits erledigt)
# ✅ Schon gelöscht: frontend/pdf-new.html, temu-new.html, etc.

# 4. Alte workflow-Scripts (optional, wenn nicht mehr genutzt)
# Diese sind noch nützlich für CLI-Tests:
# - workflows/temu_orders.py
# - workflows/temu_inventory.py
# → BEHALTEN als CLI-Wrapper
```

**Was MUSS bleiben:**

```bash
# ✅ BUSINESS LOGIC - NICHT LÖSCHEN!
src/modules/temu/              # TEMU Business Logic
src/modules/pdf_reader/        # PDF Processing Logic
src/modules/xml_export/        # XML Export (noch nicht migriert)
src/marketplace_connectors/    # TEMU API Client
src/db/                        # Database Layer
src/services/                  # Shared Services

# ✅ INFRASTRUKTUR - NICHT LÖSCHEN!
workers/                       # Job Scheduler
config/                        # Configuration
data/                          # Runtime Data

# ✅ NEUE MODULE - NICHT LÖSCHEN!
modules/shared/                # Re-Export Layer
modules/pdf_reader/            # PDF Router + Frontend
modules/temu/                  # TEMU Router + Frontend + Jobs
```

---

### **Phase 3: Dokumentation aktualisieren** 📚

**Schritt 3.1**: STATUS.md aktualisieren
```bash
vim docs/STATUS.md

# Ergänze:
## 2. Februar 2026 - Monorepo Migration abgeschlossen
- ✅ Unified Gateway (main.py) ersetzt api/server.py
- ✅ Modulare Struktur: modules/pdf_reader, modules/temu
- ✅ PM2 läuft mit main:app
- ✅ Frontends ohne Duplikate (direkt aus Modulen serviert)
- ✅ Alte Business Logic in src/ bleibt bestehen (wird von Routern wiederverwendet)
```

**Schritt 3.2**: CLAUDE.md aktualisieren
```bash
vim CLAUDE.md

# Aktualisiere "Running the Application":
**Production (PM2):**
```bash
# Start with PM2
pm2 start ecosystem.config.js  # Jetzt mit main:app statt api.server:app

# Gateway läuft auf Port 8000
# Module:
# - /api/pdf   → PDF Processor
# - /api/temu  → TEMU Integration
```

**Schritt 3.3**: Neue Architektur-Diagramme
```bash
# Erstelle docs/ARCHITECTURE/monorepo.md
```

---

### **Phase 4: Optional - Weitere Bereinigungen** 🔧

**Was könnte noch migriert werden?**

1. **XML Export Modul** (in `src/modules/xml_export/`):
   - Könnte zu `modules/xml_export/` migriert werden
   - Braucht Router + Frontend?
   - Oder bleibt es reines Backend-Modul?

2. **Workflows-Verzeichnis** (`workflows/`):
   - Sind CLI-Wrapper für TEMU-Jobs
   - Könnten in `modules/temu/cli.py` migriert werden
   - Oder bleiben als standalone Scripts

3. **Test-Verzeichnis** (fehlt aktuell!):
   - `tests/` anlegen für Unit Tests
   - Integration Tests für Module

---

## 🎯 Zusammenfassung - Was ist zu tun?

### Kritisch (JETZT):
1. ✅ **PM2 auf main.py umstellen** (Phase 1)
2. ✅ **Alten api/server.py umbenennen** (Phase 2)
3. ✅ **Dokumentation aktualisieren** (Phase 3)

### Optional (SPÄTER):
4. ⏭️ XML Export Modul migrieren
5. ⏭️ Workflows zu CLI-Commands migrieren
6. ⏭️ Tests hinzufügen

---

## ✅ Erwartetes Ergebnis nach Cleanup

### Struktur VORHER (jetzt):
```
├── api/
│   └── server.py          ❌ Alt, 508 Zeilen, PM2 läuft damit
├── main.py                ✅ Neu, 380 Zeilen, nicht aktiv
├── modules/
│   ├── shared/           ✅ Re-Export Layer
│   ├── pdf_reader/       ✅ Router + Frontend
│   └── temu/             ✅ Router + Frontend
└── src/
    ├── modules/          ✅ Business Logic (wird von Routern verwendet)
    ├── db/               ✅ Database Layer
    └── services/         ✅ Shared Services
```

### Struktur NACHHER (Ziel):
```
├── main.py                ✅ Unified Gateway (PM2 läuft damit)
├── modules/
│   ├── shared/           ✅ Re-Export Layer
│   ├── pdf_reader/       ✅ Router + Frontend
│   └── temu/             ✅ Router + Frontend
├── src/
│   ├── modules/          ✅ Business Logic
│   ├── db/               ✅ Database Layer
│   └── services/         ✅ Shared Services
├── workers/              ✅ Job Scheduler (shared infrastructure)
└── api/
    └── server.py.OLD     📦 Backup (nicht in Git)
```

---

## 🚀 Nächste Schritte

**Sofort:**
```bash
# 1. Teste main.py lokal
python -m uvicorn main:app --host 127.0.0.1 --port 8001

# 2. Wenn OK: PM2 umstellen
pm2 stop temu-api
pm2 delete temu-api
pm2 start ecosystem-monorepo.config.js

# 3. Teste Produktion
curl http://192.168.178.4:8000/api/health
curl http://192.168.178.4:8000/

# 4. Wenn alles läuft: Aufräumen
mv api/server.py api/server.py.OLD
rm api/server.py.backup

# 5. Committen
git add -A
git commit -m "chore: Finalize monorepo migration - switch to main.py"
git push
```

---

**Autor**: Claude Sonnet 4.5
**Letzte Aktualisierung**: 2. Februar 2026
