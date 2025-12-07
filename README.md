# TEMU Order Processing System

Automatisiertes System zur Verarbeitung von TEMU-Bestellungen mit JTL-Integration.

## 📋 Übersicht

Das System verarbeitet TEMU-Bestellungen in 4 Schritten:
1. **CSV Import** → Bestellungen aus TEMU-Export in Datenbank importieren
2. **XML Erstellung** → Bestellungen als XML exportieren und in JTL importieren
3. **Tracking Update** → Trackingnummern aus JTL holen
4. **Excel Export** → Tracking-Datei für TEMU-Upload erstellen

## 🚀 Schnellstart

### Kompletter Workflow (empfohlen)
```bash
python workflow.py
```

### Einzelne Schritte
```bash
# 1. Nur CSV Import
python import_orders.py

# 2. Nur XML Erstellung
python create_xml_from_db.py

# 3. Nur Tracking Update
python update_tracking.py

# 4. Nur Excel Export
python export_tracking.py
```

## ⚙️ Installation

```bash
# 1. Virtual Environment erstellen
python -m venv .venv

# 2. Environment aktivieren
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 3. Dependencies installieren
pip install -r requirements.txt

# 4. .env konfigurieren
# SQL Server Zugangsdaten eintragen
```

## 📁 Dateistruktur

📁 Dateistruktur

temu/
├── workflow.py              # Hauptworkflow (alle Schritte)
├── import_orders.py         # Schritt 1: CSV → DB
├── create_xml_from_db.py    # Schritt 2: DB → XML → JTL
├── update_tracking.py       # Schritt 3: JTL → DB
├── export_tracking.py       # Schritt 4: DB → Excel
├── .env                     # Konfiguration
├── requirements.txt         # Python Dependencies
├── db_schema.sql           # Datenbank Schema
└── README.md               # Diese Datei

🗃️ Datenbank

Tabellen in toci Datenbank:
    temu_orders - Bestellungen (Header)
    temu_order_items - Bestellpositionen (Artikel)
    temu_xml_export - XML Backup/Audit-Log
JTL Datenbank eazybusiness:
    tXMLBestellImport - XML Import für JTL Worker
    lvLieferschein / lvLieferscheinpaket - Tracking-Daten

📊 Status-Flow
importiert → xml_erstellt → versendet → (temu_gemeldet)

🔄 Automatisierung
Windows Task Scheduler
# Täglich um 10:00 Uhr
    schtasks /create /tn "TEMU Processing" /tr "C:\path\to\.venv\Scripts\python.exe C:\path\to\workflow.py" /sc daily /st 10:00

Cron (Linux)
# Täglich um 10:00 Uhr
    0 10 * * * cd /path/to/temu && /path/to/.venv/bin/python workflow.py >> temu_workflow.log 2>&1

🔧 Konfiguration (.env)
    # SQL Server (für alle Datenbanken)
    SQL_SERVER=192.168.178.2,50000
    SQL_USERNAME=tociuser
    SQL_PASSWORD=YourPassword

    # Dateipfade
    CSV_INPUT_PATH=order_export.csv
    XML_OUTPUT_PATH=jtl_temu_bestellungen.xml
    TRACKING_EXPORT_PATH=temu_tracking_export.xlsx

📝 Logs & Debugging
Alle Scripts geben detaillierte Ausgaben in der Console:

✓ = Erfolg
⚠ = Warnung
✗ = Fehler

🆘 Troubleshooting
Problem: "Kein ODBC-Treiber gefunden"
Lösung: ODBC Driver 18 for SQL Server installieren
https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

Problem: "Connection failed"
Lösung:

SQL Server erreichbar? ping 192.168.178.2
Port 50000 offen?
Zugangsdaten korrekt in .env?
Problem: "Keine Bestellungen gefunden"
Lösung:

CSV-Datei vorhanden und korrekt?
Bestellungen bereits importiert? (Duplikate werden übersprungen)
📞 Support
Bei Fragen oder Problemen: Christian Blass


**Verwendung:**

```bash
# Kompletten Workflow ausführen
python workflow.py

# Ausgabe wird etwa so aussehen:
# ======================================================================
#   TEMU ORDER PROCESSING WORKFLOW
# ======================================================================
# Start: 02.12.2025 14:30:00
# 
# [Schritt 1/4] CSV Import → Datenbank
# ----------------------------------------------------------------------
# ✓ CSV erfolgreich eingelesen: 14 Zeilen
# ✓ SQL Server Verbindung hergestellt
# ✓ Import erfolgreich abgeschlossen!
#   Neue Bestellungen: 3
#   Aktualisierte Bestellungen: 0
# 
# [Schritt 2/4] XML Erstellung → JTL Import
# ...

Die workflow.py ist robust und läuft alle Schritte durch, auch wenn einzelne fehlschlagen. Am Ende gibt es eine Zusammenfassung mit allen Ergebnissen! 🎯