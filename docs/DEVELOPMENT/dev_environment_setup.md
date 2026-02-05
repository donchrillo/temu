# Development Environment Setup

> **Created:** 5. Februar 2026
> **Purpose:** Separate Development und Production Environment auf einem Server
> **Target:** Linux Server (SSH-basierte Entwicklung)

---

## 1. Übersicht

### Problem
- Development direkt im Live-System (`/home/chx/temu`) ist riskant
- PM2-Restart nach jedem Change ist langsam
- Keine Auto-Reload während Development
- Caddy/SSL nicht nötig für Development

### Lösung: Zwei parallele Environments

| Environment | Pfad | Port | Server | Zweck |
|-------------|------|------|--------|-------|
| **Production** | `/home/chx/temu` | 8000 | PM2 + Caddy | Live-System |
| **Development** | `/home/chx/temu-dev` | 8001 | uvicorn | Entwicklung |

### Workflow
```
Development (temu-dev) → Git Commit → GitHub → Git Pull → Production (temu)
```

---

## 2. Automatisches Setup

### Quick Start

```bash
# 1. SSH zum Server
ssh chx@192.168.178.4

# 2. Setup-Script ausführen
cd /home/chx/temu
./scripts/setup_dev_environment.sh

# 3. Development starten
cd /home/chx/temu-dev
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# 4. Browser öffnen
# http://192.168.178.4:8001
```

Das Script erstellt automatisch:
- ✅ `/home/chx/temu-dev` (Repository-Kopie)
- ✅ Virtual Environment mit allen Dependencies
- ✅ Angepasste `.env` Datei (Port 8001)
- ✅ Bash-Aliases für schnellen Zugriff
- ✅ Screen-Session Template

---

## 3. Manuelles Setup (falls Script nicht funktioniert)

### Schritt 1: Repository klonen

```bash
cd /home/chx

# Option A: Lokale Kopie (schneller)
git clone /home/chx/temu temu-dev

# Option B: Von GitHub (falls lokale Kopie Probleme hat)
git clone https://github.com/donchrillo/temu.git temu-dev

cd temu-dev
```

### Schritt 2: Virtual Environment

```bash
# Python venv erstellen
python3 -m venv .venv

# Aktivieren
source .venv/bin/activate

# Verify
which python
# Sollte zeigen: /home/chx/temu-dev/.venv/bin/python

# Dependencies installieren
pip install --upgrade pip
pip install -r requirements.txt
```

### Schritt 3: Environment Configuration

```bash
# .env Datei kopieren
cd /home/chx/temu-dev
cp modules/shared/config/.env modules/shared/config/.env.backup

# .env bearbeiten
nano modules/shared/config/.env
```

**Wichtige Änderungen in .env:**

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8001  # ← WICHTIG: Anderer Port als Production!

# Environment Flag (optional, für Debugging)
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Database: Kann gleich bleiben (shared mit Production)
SQL_SERVER=192.168.178.4
SQL_USERNAME=sa
SQL_PASSWORD=<dein-passwort>
SQL_DATABASE=toci

# TEMU API: Gleiche Credentials wie Production
TEMU_APP_KEY=<dein-key>
TEMU_APP_SECRET=<dein-secret>
TEMU_ACCESS_TOKEN=<dein-token>
```

**Optional: Separate Dev-Datenbank**

Falls du komplett isolierte Daten willst:

```bash
# Auf SQL Server: Dev-Datenbank erstellen
# Name: toci_dev

# In .env:
SQL_DATABASE=toci_dev
```

### Schritt 4: Git Branch erstellen

```bash
cd /home/chx/temu-dev

# Feature Branch für deine Entwicklung
git checkout -b feature/mein-neues-feature

# Verify
git branch
# * feature/mein-neues-feature
```

### Schritt 5: Test-Start

```bash
# In temu-dev mit aktivierter venv
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Sollte starten mit:
# INFO:     Uvicorn running on http://0.0.0.0:8001
# INFO:     Application startup complete.
```

**Test im Browser:**
- `http://192.168.178.4:8001` (von anderem Gerät)
- `http://localhost:8001` (lokal auf Server)

**Test API:**
```bash
curl http://localhost:8001/api/health
# Expected: {"status":"ok",...}
```

**Wenn alles funktioniert: Ctrl+C zum Stoppen**

---

## 4. Bash-Aliases (Empfohlen)

### Aliases hinzufügen

```bash
# .bashrc bearbeiten
nano ~/.bashrc

# Am Ende hinzufügen:
# ==================== TEMU Development Aliases ====================

# Quick navigation
alias temu-dev='cd /home/chx/temu-dev && source .venv/bin/activate'
alias temu-live='cd /home/chx/temu'

# Start development server
alias temu-start='cd /home/chx/temu-dev && source .venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8001'

# Quick status checks
alias temu-dev-status='curl -s http://localhost:8001/api/health | jq'
alias temu-live-status='curl -s http://localhost:8000/api/health | jq'

# Git shortcuts
alias temu-dev-branch='cd /home/chx/temu-dev && git branch'
alias temu-dev-status-git='cd /home/chx/temu-dev && git status'

# Logs
alias temu-dev-logs='tail -f /home/chx/temu-dev/logs/pdf_reader/pdf_reader.log'
alias temu-live-logs='pm2 logs temu-api --lines 50'

# ==================================================================

# Reload
source ~/.bashrc
```

### Verwendung

```bash
# Schnell zu Dev wechseln (mit aktivierter venv)
temu-dev

# Dev-Server starten
temu-start

# Status checken
temu-dev-status
temu-live-status

# Git Status
temu-dev-branch
temu-dev-status-git

# Logs anschauen
temu-dev-logs
temu-live-logs
```

---

## 5. Screen/Tmux für persistente Sessions

### Problem
SSH-Verbindung abbricht → uvicorn stoppt

### Lösung: Screen verwenden

#### Screen installieren (falls nicht vorhanden)

```bash
sudo apt update
sudo apt install screen -y
```

#### Screen Basic Usage

```bash
# Neue Screen-Session starten
screen -S temu-dev

# Darin: Development-Server starten
cd /home/chx/temu-dev
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Screen verlassen (Server läuft weiter!)
# Tastenkombination: Ctrl+A, dann D

# Screen-Sessions anzeigen
screen -ls

# Screen wieder anhängen
screen -r temu-dev

# Screen beenden (von innen)
# Ctrl+C (stoppt uvicorn), dann: exit
```

#### Screen mit Alias

```bash
# In ~/.bashrc hinzufügen:
alias temu-screen='screen -S temu-dev'
alias temu-attach='screen -r temu-dev'
alias temu-screens='screen -ls'

# Verwendung:
temu-screen     # Startet neue Screen-Session
temu-attach     # Hängt an laufende Session an
temu-screens    # Zeigt alle Sessions
```

#### Tmux Alternative

```bash
# Tmux installieren
sudo apt install tmux -y

# Session starten
tmux new -s temu-dev

# Session verlassen: Ctrl+B, dann D
# Session anhängen: tmux attach -t temu-dev
```

---

## 6. Daily Development Workflow

### Morning Routine

```bash
# 1. SSH zum Server
ssh chx@192.168.178.4

# 2. Screen-Session starten (oder anhängen)
screen -S temu-dev
# ODER falls schon läuft:
screen -r temu-dev

# 3. Zu Dev-Environment wechseln
cd /home/chx/temu-dev
source .venv/bin/activate

# 4. Neueste Änderungen holen (falls von anderem Gerät)
git pull origin feature/mein-feature

# 5. Development-Server starten
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# 6. Screen verlassen (Ctrl+A, dann D)
# Server läuft weiter im Hintergrund

# 7. In neuem Terminal/SSH: Entwickeln
ssh chx@192.168.178.4
cd /home/chx/temu-dev
# ... Code editieren ...
```

### Während Entwicklung

```bash
# Files editieren (nano, vim, VS Code Remote SSH)
nano modules/pdf_reader/services/werbung_service.py

# Bei Änderung: uvicorn reload automatisch (wegen --reload flag)
# Im Browser: http://192.168.178.4:8001 → F5 (Refresh)

# Regelmäßig committen
git add modules/pdf_reader/services/werbung_service.py
git commit -m "feat(pdf): Add new feature XYZ"

# Optional: Push zu GitHub (als Backup)
git push origin feature/mein-feature
```

### Testing während Development

```bash
# API Tests
curl http://localhost:8001/api/health
curl http://localhost:8001/api/pdf/health

# Frontend Tests
# Browser: http://192.168.178.4:8001

# Logs anschauen (in separatem Terminal)
tail -f /home/chx/temu-dev/logs/pdf_reader/pdf_reader.log
```

### Abend-Routine (Feature fertig)

```bash
# 1. Letzte Änderungen committen
cd /home/chx/temu-dev
git add .
git commit -m "feat(mein-feature): Complete implementation"

# 2. Push zu GitHub
git push origin feature/mein-feature

# 3. Development-Server stoppen
screen -r temu-dev
# Darin: Ctrl+C
exit  # Screen beenden

# 4. Optional: Feature sofort deployen (siehe nächster Abschnitt)
```

---

## 7. Deployment: Dev → Production

### Vollständiger Deployment-Workflow

```bash
# ============================================================
# SCHRITT 1: In Development - Letzter Check
# ============================================================
cd /home/chx/temu-dev

# Alle Änderungen committen
git add .
git commit -m "feat(mein-feature): Final implementation"

# Push zu GitHub
git push origin feature/mein-feature

# Server stoppen (falls noch läuft)
# screen -r temu-dev → Ctrl+C → exit

# ============================================================
# SCHRITT 2: Wechsel zu Production
# ============================================================
cd /home/chx/temu

# Aktuellen Status prüfen
git status
git branch

# Falls auf main: Feature Branch holen
git fetch origin
git checkout feature/mein-feature

# ODER: Direkt in main mergen
git checkout main
git merge feature/mein-feature

# ============================================================
# SCHRITT 3: Production neu starten
# ============================================================

# PM2 neustarten
pm2 restart temu-api

# Logs beobachten (ca. 30 Sekunden)
pm2 logs temu-api --lines 50

# Sollte zeigen:
# - Keine Errors
# - "Application startup complete"

# ============================================================
# SCHRITT 4: Production testen
# ============================================================

# API Test
curl https://192.168.178.4/api/health
curl https://192.168.178.4/api/pdf/health

# Frontend Test
# Browser: https://192.168.178.4
# Alle Features testen!

# ============================================================
# SCHRITT 5: Cleanup (wenn alles funktioniert)
# ============================================================

# Feature Branch in main mergen (falls noch nicht)
git checkout main
git merge feature/mein-feature
git push origin main

# Feature Branch löschen (optional)
git branch -d feature/mein-feature
git push origin --delete feature/mein-feature

# ============================================================
# SCHRITT 6: Dev-Environment synchronisieren
# ============================================================

cd /home/chx/temu-dev
git checkout main
git pull origin main

# Neuen Feature Branch für nächstes Feature
git checkout -b feature/naechstes-feature
```

---

## 8. Git Best Practices

### Branch-Strategie

```bash
# Main Branch: Production-ready Code
main

# Feature Branches: Pro Feature ein Branch
feature/pdf-reader-enhancement
feature/csv-verarbeiter-phase2
feature/new-module

# Bugfix Branches: Für kritische Fixes
bugfix/pdf-reader-crash
hotfix/security-issue
```

### Commit Messages

**Format:** `<type>(<scope>): <subject>`

**Types:**
- `feat`: Neues Feature
- `fix`: Bug Fix
- `docs`: Dokumentation
- `refactor`: Code-Refactoring
- `test`: Tests
- `chore`: Maintenance

**Beispiele:**
```bash
git commit -m "feat(pdf): Add currency detection for invoices"
git commit -m "fix(csv): Handle empty OrderID columns"
git commit -m "docs(dev): Add development environment guide"
git commit -m "refactor(temu): Extract order validation logic"
```

### Commit-Workflow

```bash
# Häufig committen (kleine Commits)
git add modules/pdf_reader/services/werbung_service.py
git commit -m "feat(pdf): Add parse_amount function"

# Regelmäßig pushen (Backup)
git push origin feature/mein-feature

# Vor größeren Changes: Branch aktualisieren
git fetch origin main
git rebase origin/main  # Oder: git merge origin/main
```

---

## 9. Troubleshooting

### Problem 1: Port 8001 bereits belegt

```bash
# Error: Address already in use

# Lösung: Laufenden Prozess finden
lsof -i :8001
# Oder:
netstat -tulpn | grep 8001

# Prozess killen
kill -9 <PID>

# Oder: Anderen Port verwenden
uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

### Problem 2: Module Not Found

```bash
# Error: ModuleNotFoundError: No module named 'fastapi'

# Lösung 1: Virtual Environment aktivieren
cd /home/chx/temu-dev
source .venv/bin/activate

# Verify
which python
# Sollte zeigen: /home/chx/temu-dev/.venv/bin/python

# Lösung 2: Dependencies neu installieren
pip install -r requirements.txt
```

### Problem 3: Database Connection Failed

```bash
# Error: Cannot connect to SQL Server

# Lösung: .env prüfen
cat modules/shared/config/.env | grep SQL_

# Credentials testen
python -c "
from modules.shared.database.connection import get_engine
engine = get_engine()
with engine.connect() as conn:
    print('✓ Connection OK')
"
```

### Problem 4: Import Error nach Merge

```bash
# Error: ImportError: cannot import name 'xyz'

# Lösung: Dependencies aktualisieren
cd /home/chx/temu-dev
source .venv/bin/activate
pip install -r requirements.txt --upgrade

# Python-Cache löschen
find . -type d -name __pycache__ -exec rm -rf {} +
```

### Problem 5: Git Merge Conflicts

```bash
# Conflict beim merge/rebase

# Lösung:
git status  # Zeigt konfliktende Dateien

# File öffnen, Conflicts manuell lösen (<<<<<<< ======= >>>>>>>)
nano <file-with-conflict>

# Nach Lösung:
git add <file-with-conflict>
git commit -m "Resolve merge conflict in <file>"
```

### Problem 6: Screen Session lost

```bash
# Screen-Session versehentlich geschlossen

# Lösung: Sessions anzeigen
screen -ls

# Falls noch da: Wieder anhängen
screen -r temu-dev

# Falls weg: Neue Session starten
screen -S temu-dev
cd /home/chx/temu-dev
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

---

## 10. Nützliche Commands Cheat Sheet

### Development Shortcuts

```bash
# Start Development
cd /home/chx/temu-dev && source .venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Start in Screen
screen -S temu-dev
cd /home/chx/temu-dev && source .venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Check if running
curl http://localhost:8001/api/health

# View logs
tail -f logs/pdf_reader/pdf_reader.log
```

### Git Commands

```bash
# Status
git status
git branch

# Create feature branch
git checkout -b feature/my-feature

# Commit
git add .
git commit -m "feat(module): Description"

# Push
git push origin feature/my-feature

# Update from main
git fetch origin main
git merge origin/main

# Switch branches
git checkout main
git checkout feature/my-feature
```

### PM2 Commands (Production)

```bash
# Status
pm2 status
pm2 list

# Restart
pm2 restart temu-api

# Logs
pm2 logs temu-api
pm2 logs temu-api --lines 100

# Stop/Start
pm2 stop temu-api
pm2 start ecosystem.config.js
```

### System Commands

```bash
# Check ports
lsof -i :8000
lsof -i :8001
netstat -tulpn | grep 800

# Check processes
ps aux | grep uvicorn
ps aux | grep python

# Disk space
df -h
du -sh /home/chx/temu*

# Memory
free -h
```

---

## 11. VS Code Remote SSH (Optional)

### Setup

Falls du mit VS Code entwickeln willst:

1. **VS Code Extension installieren:**
   - "Remote - SSH" Extension

2. **SSH Config:**
   ```
   # In ~/.ssh/config auf deinem lokalen PC:
   Host temu-server
       HostName 192.168.178.4
       User chx
       IdentityFile ~/.ssh/id_rsa
   ```

3. **Verbinden:**
   - VS Code: `Ctrl+Shift+P` → "Remote-SSH: Connect to Host"
   - Select: `temu-server`
   - Folder öffnen: `/home/chx/temu-dev`

4. **Extensions auf Server installieren:**
   - Python
   - Pylance
   - GitLens

5. **Python Interpreter auswählen:**
   - `Ctrl+Shift+P` → "Python: Select Interpreter"
   - Select: `/home/chx/temu-dev/.venv/bin/python`

6. **Entwickeln:**
   - Files editieren in VS Code
   - Terminal in VS Code: uvicorn starten
   - Git in VS Code integriert

---

## 12. Best Practices Summary

### DO ✅

- ✅ Immer in `temu-dev` entwickeln, nie in `temu`
- ✅ Screen/tmux für persistente Sessions verwenden
- ✅ Häufig committen (kleine Commits)
- ✅ Regelmäßig zu GitHub pushen (Backup)
- ✅ Feature Branches für jedes Feature
- ✅ Production testen nach jedem Deployment
- ✅ Auto-Reload nutzen (uvicorn --reload)
- ✅ Separate .env Dateien (verschiedene Ports)

### DON'T ❌

- ❌ Nicht direkt in `temu` (Production) entwickeln
- ❌ Nicht ohne Screen/tmux arbeiten (SSH dropout!)
- ❌ Nicht auf main Branch direkt committen
- ❌ Nicht Production ohne Test deployen
- ❌ Nicht ohne Backup/Git arbeiten
- ❌ Nicht beide Server auf gleichem Port starten
- ❌ Nicht .env in Git committen

---

## 13. Quick Reference

### File Locations

```
Production:
/home/chx/temu              - Production codebase
/home/chx/temu/logs/        - Production logs
Port: 8000 (PM2 + Caddy)

Development:
/home/chx/temu-dev          - Development codebase
/home/chx/temu-dev/logs/    - Development logs
Port: 8001 (uvicorn)

Configuration:
~/.bashrc                   - Bash aliases
~/.ssh/config              - SSH config (for VS Code)
```

### URLs

```
Production:
https://192.168.178.4       - Frontend (SSL via Caddy)
http://localhost:8000       - API (lokal)

Development:
http://192.168.178.4:8001   - Frontend (kein SSL)
http://localhost:8001       - API (lokal)
```

### Key Commands

```bash
# Start Development
temu-start

# Check Status
temu-dev-status
temu-live-status

# Git Status
git status
git branch

# Deploy to Production
cd /home/chx/temu
git pull origin main
pm2 restart temu-api
```

---

## 14. Setup-Script Verwendung

### Script ausführen

```bash
cd /home/chx/temu
./scripts/setup_dev_environment.sh
```

### Was das Script macht

1. ✅ Prüft ob `/home/chx/temu-dev` existiert
2. ✅ Klont Repository nach `temu-dev`
3. ✅ Erstellt Virtual Environment
4. ✅ Installiert Dependencies
5. ✅ Kopiert und passt `.env` an (Port 8001)
6. ✅ Erstellt Bash-Aliases
7. ✅ Gibt Next Steps aus

### Nach Script-Ausführung

```bash
# Bash neu laden (für Aliases)
source ~/.bashrc

# Development starten
temu-start

# Oder mit Screen
screen -S temu-dev
temu-start
# Ctrl+A, dann D (detach)
```

---

## Summary: Development Workflow

```
┌──────────────────────────────────────────────────────────┐
│ 1. SETUP (einmalig)                                      │
│    ./scripts/setup_dev_environment.sh                    │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│ 2. DEVELOP (täglich)                                     │
│    - screen -S temu-dev                                  │
│    - temu-start                                          │
│    - http://192.168.178.4:8001                          │
│    - Code editieren → Auto-Reload                        │
│    - git commit + push                                   │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│ 3. DEPLOY (wenn fertig)                                  │
│    - cd /home/chx/temu                                   │
│    - git pull origin feature/xyz                         │
│    - pm2 restart temu-api                                │
│    - Test: https://192.168.178.4                         │
└──────────────────────────────────────────────────────────┘
```

---

**Alles klar? Dann kann's losgehen!** 🚀

Bei Fragen: Diese Dokumentation lesen oder in GitHub Issues posten.
