# DEPLOYMENT Architecture

Minimale Dokumentation für Remote SSH + PM2 Setup.

---

**Datum:** 5. Februar 2026

---

## 1. SSH/Remote Setup (VSCode)

### VSCode Remote SSH Extension
```bash
# Extensions Marketplace: "Remote - SSH" von Microsoft
# Dann: Cmd+Shift+P → Remote-SSH: Open Configuration File
# Beispiel ~/.ssh/config:

Host temu-server
    HostName your-server.de
    User chx
    IdentityFile ~/.ssh/id_rsa
    ServerAliveInterval 60
```

### Verbindung herstellen
```bash
# VSCode: Cmd+Shift+P → Remote-SSH: Connect to Host → temu-server
# Terminal im VSCode läuft dann direkt auf dem Server
```

### Python venv aktivieren
```bash
# Im Server-Terminal:
cd /home/chx/temu
source .venv/bin/activate

# Oder in VSCode:
# Settings → Python: Interpreter → Pfad zum venv Python wählen
# ~/.venv/bin/python
```

---

## 2. PM2 Quick Reference

### Start Anwendung
```bash
pm2 start ecosystem.config.js
```

### Logs monitoren
```bash
# Alle Jobs
pm2 logs

# Spezifischer Job
pm2 logs temu-api
pm2 logs temu-workers
```

### Job Status prüfen
```bash
pm2 status
pm2 show temu-api
```

### Restart (nach Code-Änderungen)
```bash
pm2 restart temu-api
pm2 restart temu-workers

# Alle
pm2 restart all
```

### Stoppen
```bash
pm2 stop temu-api
pm2 delete temu-api
```

### Auto-Start bei Server-Reboot
```bash
# PM2 speichert aktuellen State + startet ihn beim Boot
pm2 save
pm2 startup
```

---

## 3. Environment Variables

### .env Datei (nicht in Git!)
```env
# /home/chx/temu/.env

# Database
DB_ODBC=DRIVER={ODBC Driver 18 for SQL Server};SERVER=...;DATABASE=...
DB_USER=...
DB_PASSWORD=...

# TEMU API
TEMU_CLIENT_ID=...
TEMU_CLIENT_SECRET=...

# API Server
UVICORN_HOST=127.0.0.1
UVICORN_PORT=8000
UVICORN_WORKERS=4

# APScheduler
SCHEDULER_TIMEZONE=Europe/Berlin
```

### Laden in Python
```python
# modules/shared/config/settings.py
from dotenv import load_dotenv
import os

load_dotenv()  # Liest .env automatisch

DB_ODBC = os.getenv("DB_ODBC")
TEMU_CLIENT_ID = os.getenv("TEMU_CLIENT_ID")
```

---

## 4. Deployment Workflow

### Code-Update (via VSCode SSH)
```bash
# Im VSCode Terminal auf Server:
cd /home/chx/temu
git pull origin main
# (falls neue Dependencies)
pip install -r requirements.txt
```

### Restart nach Code-Änderungen
```bash
# Option 1: Graceful Restart
pm2 restart temu-api temu-workers

# Option 2: Zero-downtime (bei mehreren Instances)
pm2 reload temu-api
```

### Logs nach Restart prüfen
```bash
pm2 logs temu-api --err  # Nur Errors
pm2 logs temu-workers --lines 50  # Last 50 lines
```

---

## 5. Troubleshooting

### Job startet nicht
```bash
# 1. Config prüfen
pm2 show temu-api

# 2. Logs detailliert
pm2 logs temu-api --err

# 3. Manuell testen
cd /home/chx/temu
source .venv/bin/activate
python -c "import modules.temu.services.inventory_service; print('OK')"
```

### Memory/CPU spike
```bash
# Monitoring
pm2 monit

# Details für spezifischen Job
pm2 show temu-workers
```

### Alle Jobs neustarten (nuclear option)
```bash
pm2 kill
pm2 start ecosystem.config.js
pm2 save
```

---

## 6. Server Maintenance

### Backup vor größeren Änderungen
```bash
# Aktuellen PM2 State speichern
pm2 save

# Database-Backup (falls nötig)
# Abhängig von SQL Server Setup
```

### Log-Rotation (automatisch via PM2)
```bash
# ecosystem.config.js setzt bereits:
# - error_file: logs/error.log
# - out_file: logs/out.log
# PM2 rotiert automatisch
```

### Health-Check
```bash
# Alle Jobs sollten online sein
pm2 status

# Arbeitet der Scheduler?
curl http://127.0.0.1:8000/api/jobs/status
```

---

**Summe:** Mit PM2 gemanaged, SSH-Remote in VSCode, .env für Secrets, und die PM2-Kommandos kennend – fertig.
