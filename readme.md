# JTL2DATEV CSV-Verarbeiter

Ein flexibles, modulares Python-Tool zur Verarbeitung von Amazon-/DATEV-kompatiblen CSV-Dateien. Über eine Streamlit-Oberfläche können ZIP- oder CSV-Dateien verarbeitet, überprüft, ersetzt, protokolliert und exportiert werden. Die Anwendung wurde für kleinere Online-Händler konzipiert, die eine einfache, automatisierte Schnittstelle zwischen Marktplatzdaten und Buchhaltung benötigen.

Das Tool lädt CSV- oder ZIP-Dateien ein, liest Amazon-Bestellnummern aus und ersetzt sie durch Kundennummern aus einer SQL-Datenbank. Fehlerhafte oder nicht gefundene Einträge werden protokolliert. Kritische Gegenkonten werden erkannt und hervorgehoben. Abschließend erfolgt eine strukturierte Speicherung inklusive einer Übersichtsdatei mit Reportdaten.

---

## Features

- CSV-/ZIP-Verarbeitung über eine einfache Weboberfläche (Streamlit)
- Automatische Ersetzung von Amazon-Bestellnummern mit SQL-Kundennummern
- Erkennung kritischer Gegenkonten (0–20)
- Validierungs- und Ersetzungsprotokoll als Excel-Datei
- ZIP-Export inkl. Report, Logfile & Archivierung
- Vollständige Protokollierung aller Veränderungen und Fehler

---

## Verzeichnisstruktur

```bash
projekt-root/
|│
|├\2500 config.py                 # Globale Konstanten und Pfade
|├\2500 verarbeitung.py           # Hauptlogik zur CSV-Verarbeitung
|├\2500 backend.py               # Steuerung von Verarbeitung, ZIP-Export etc.
|├\2500 gui.py                   # Streamlit GUI
|├\2500 verarbeitung_io.py        # I/O: Lesen & Schreiben von CSV
|├\2500 verarbeitung_logik.py    # Datenlogik: Spalten, Prüfungen, Ersetzungen
|├\2500 verarbeitung_validation.py # Validierung von OrderIDs und Konten
|├\2500 sql.py                   # SQL-Verbindung & OrderID-Abfrage
|├\2500 report_collector.py      # Excel-Protokollierung der Verarbeitung
|├\2500 zip_handler.py           # Entpacken, ZIP-Erzeugung, Aufräumen
|├\2500 log_helper.py            # Logging-Konfiguration (Datei + Konsole)
|├\2500 gui_utils.py             # Zusätzliche Streamlit-Helfer
|└\2500 .env                     # Lokale SQL-Zugangsdaten
```

---

## Technologien

- **Python 3.11+**
- **pandas**, **openpyxl**, **pyodbc**
- **streamlit** – Web-GUI
- **dotenv** – .env-Konfiguration

---

## Setup

```bash
git clone https://github.com/dein-name/csv-verarbeiter.git
cd csv-verarbeiter
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Die Datei `.env` enthält deine SQL-Zugangsdaten:

```
SQL_SERVER=localhost
SQL_PORT=1433
SQL_DB=toci
SQL_USER=...
SQL_PASS=...
```

---

## Verwendung

```bash
streamlit run gui.py
```

- CSV-/ZIP-Dateien ins Verzeichnis `eingang/` legen
- In der Weboberfläche die Dateien auswählen und verarbeiten lassen
- Reports erscheinen in `log/`, neue CSV-Dateien in `ausgang/`

---

## Architektur

Das Tool ist modular aufgebaut:

- **verarbeitung.py** ist das Kernmodul zur Einzeldatei-Verarbeitung
- **verarbeitung_io.py** liest CSV-Daten und schreibt Ergebnisse
- **verarbeitung_logik.py** verarbeitet und ersetzt Order-IDs
- **report_collector.py** erzeugt Excel-Protokolle
- **backend.py** koordiniert die Batchverarbeitung & ZIP-Exports
- **gui.py** stellt die Streamlit-Oberfläche bereit
- **sql.py** fragt zugehörige Kundennummern ab (per pyodbc)

Alle Fehler, nicht gefundene IDs, kritische Konten etc. werden zentral protokolliert.

---

## Motivation & Nutzen

Viele kleine Amazon-Händler exportieren Daten nach DATEV, aber diese sind nur bedingt nutzbar:
- Order-IDs statt Kundennummern
- fehlende Spalten / Metadaten
- manuelle Nacharbeit in Excel

Dieses Tool schafft automatisierte Abhilfe – reproduzierbar und dokumentiert.

---

## Zukunft & ToDos

- Automatisierte E-Mail-Benachrichtigung bei kritischen Fällen
- Erweiterung auf andere Marktplatzformate (z. B. eBay)
- Einstellung von SQL-Parametern über die GUI
- Integriertes Fehler-Dashboard mit Drilldown
- Unit-Tests für alle Module

---


## ✍️ Dokumentation & Stil

- Alle Funktionen enthalten **ausführliche Google-Style-Docstrings**
- Code ist durchgängig **kommentiert für Einsteiger**
- Strukturierte **Hilfsfunktionen in separaten Modulen**
- Logging über Excel + Konsole
