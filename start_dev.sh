#!/bin/bash

# Entwicklungsumgebung für TEMU API starten
# Port: 8888 (Produktion läuft auf 8000)
# APScheduler-Jobs sind deaktiviert (siehe workers/config/workers_config.json)

echo "🚀 Starte TEMU API Entwicklungsumgebung..."
echo "📍 Port: 8888"
echo "🔄 Auto-Reload: aktiviert"
echo "📦 Jobs: deaktiviert"
echo ""

# Ins Skript-Verzeichnis wechseln (wo auch immer das Repo geklont wurde)
cd "$(dirname "$0")"

# Virtuelle Umgebung aktivieren und uvicorn starten
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8888
