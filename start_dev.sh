#!/bin/bash

# TEMU API starten
# Port: 8000

echo "Starte TEMU API..."
echo "Port: 8000"
echo "Auto-Reload: aktiviert"
echo ""

cd "$(dirname "$0")"

source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
