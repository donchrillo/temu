# TEMU zu DATEV Konverter

## Aktueller Stand (12.03.2026)

Dieses Repository ist kein reines Standalone-Projekt mehr.
Der aktuelle Stand ist eine lauffaehige FastAPI-Backend + React-Frontend Loesung,
die die bestehende TEMU->DATEV Fachlogik nutzt.

Kurzstatus:
- Backend-API ist produktiv nutzbar
- Frontend-Dashboard ist produktiv nutzbar
- Fachlogik (Konvertierung, Tracking, OP-Analyse) ist aktiv eingebunden
- Naechstes Ziel: Integration in dein bestehendes Hauptsystem (FastAPI + React)

## Architektur

```text
React Dashboard -> FastAPI Router -> Service Layer -> Kernlogik-Module -> DATEV Exporte
```

Wichtig:
- Die Router enthalten nicht die gesamte Fachlogik.
- Die Kernlogik lebt weiterhin in:
  - `convert_bestellungen.py`
  - `convert_zahlungen.py`
  - `datev_writer.py`
  - `simulate_op_buchungen.py`
- Das API-Backend verwendet diese Module direkt ueber `backend/services/conversion_service.py`.

## Projektstruktur

```text
TEmuAuszahlung/
├── backend/
│   ├── main.py
│   ├── schemas.py
│   ├── routers/
│   │   ├── files.py
│   │   ├── convert.py
│   │   ├── op.py
│   │   └── exports.py
│   └── services/
│       ├── file_service.py
│       └── conversion_service.py
├── frontend-react/
│   └── src/
├── convert_bestellungen.py
├── convert_zahlungen.py
├── datev_writer.py
├── simulate_op_buchungen.py
├── temu_to_datev_all.py
├── config.py
└── export/
```

## API Endpunkte

- `GET /api/health`
- `GET /api/files/orders`
- `POST /api/files/orders/upload`
- `GET /api/files/orders/{filename}/content`
- `PUT /api/files/orders/{filename}/content`
- `GET /api/files/payments`
- `POST /api/files/payments/upload`
- `GET /api/files/payments/{filename}/content`
- `PUT /api/files/payments/{filename}/content`
- `POST /api/convert/orders`
- `POST /api/convert/payments`
- `POST /api/op/analyze`
- `GET /api/exports`
- `GET /api/exports/{filename}`
- `GET /api/exports/{filename}/content`

## Frontend Features

- Upload von Bestell- und Zahlungsberichten
- Auswahl und Start von Konvertierungen
- Detaillierte Ergebnisanzeige inkl. skipped/ignored
- Tabelle fuer ignorierte Zeilen
- OP-Analyse (Summary + Details)
- Exportliste mit Oeffnen (Vorschau) + Download
- CSV-Dateien oeffnen, bearbeiten und speichern

## Betrieb und Daten

- Arbeitsordner fuer Daten:
  - `bestellberichte/`
  - `zahlungsberichte/`
  - `export/`
- Diese Ordner sind in Git ignoriert und sollen nicht als Betriebsdaten versioniert werden.
- Tracking liegt in `export/.datev_export_state.json`.
- DATEV-Exportdateien werden vor Ueberschreiben in `export/.history/` archiviert.

## Start lokal (Testbetrieb)

Backend:

```bash
cd /home/chx/temu-datev/TEmuAuszahlung
source /home/chx/temu-datev/.venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

Frontend:

```bash
cd /home/chx/temu-datev/TEmuAuszahlung/frontend-react
npm install
VITE_API_URL=http://127.0.0.1:8001 npm run dev -- --port 3001 --host 127.0.0.1
```

## Integration in dein Hauptsystem (Zielbild)

Empfohlener Weg:
1. Dieses Modul als Codepaket in dein Hauptrepo uebernehmen (z. B. per `git subtree`).
2. Backend unter eigenem Prefix einhaengen, z. B. `/api/temu-datev`.
3. Pfade fuer Input/Output per ENV/Settings zentral konfigurierbar machen.
4. Bestehende Auth und Logging deines Hauptsystems vor die Endpunkte haengen.
5. Frontend als Feature-Route in deine bestehende React-App integrieren.

## Refactoring-Strategie

- Kein erzwungenes Refactoring mehr in diesem Repo notwendig.
- Das grosse Aufraeumen (Modulstruktur angleichen, evtl. Core/Adapter-Split) ist sinnvoller direkt im Zielsystem.
- So vermeidest du doppelte Umbauten.

## Dokumentation

- Diese `README.md` ist die zentrale und aktuelle Hauptdokumentation.
- `TEmuAuszahlung/ARBEITSSTAND.md` ist die operative Arbeitsgrundlage fuer Weiterentwicklung und Integration.
- Historische Migrationsdokumente liegen in `TEmuAuszahlung/MD_Archive/`.
- `TEmuAuszahlung/SESSION_NOTES.md` und `TEmuAuszahlung/UPDATE.md` verweisen auf den konsolidierten Arbeitsstand.
