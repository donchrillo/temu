# Arbeitsstand TEMU -> DATEV

Stand: 12.03.2026

## Zweck

Diese Datei fasst `SESSION_NOTES.md` (aktueller Betriebsstand) und `UPDATE.md` (fachliche und technische Aenderungen) in einer kompakten Arbeitsgrundlage zusammen.

Sie ist fuer die weitere Integration in ein bestehendes FastAPI+React Hauptsystem gedacht.

## Gemeinsamkeiten der beiden Quelldateien

- FastAPI Backend und React Frontend sind produktiv nutzbar.
- Konvertierungen laufen ueber die bestehende Python-Fachlogik (direkte Imports, kein Subprocess).
- OP-Analyse ist Bestandteil des Workflows.
- Frontend zeigt Konvertierungsdetails inkl. `skipped`/`ignored`.
- Dateioperationen (lesen/schreiben fuer Inputs, Vorschau fuer Exporte) sind umgesetzt.

## Konsolidierter Ist-Stand

### 1. API + UI Status

- Backend-Router vorhanden in `backend/routers/`:
  - `files.py`, `convert.py`, `op.py`, `exports.py`
- Service-Layer vorhanden in `backend/services/`:
  - `file_service.py`, `conversion_service.py`
- Frontend-Dashboard vorhanden in `frontend-react/src/pages/dashboard.tsx`

### 2. Wichtige Endpunkte

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

### 3. Frontend-Funktionen

- Upload und Auswahl von Bestell- und Zahlungsberichten.
- Konvertierungsdialog mit Kennzahlen:
  - Dateien, Datensaetze, Buchungen, Uebersprungen, Ignoriert.
- Tabelle fuer ignorierte Bestellzeilen inkl. Grund.
- OP-Analyse als Hybrid:
  - Inline-Bereich + Popup.
- Datei-Editor fuer Input-CSVs (oeffnen, bearbeiten, speichern).
- Exportbereich mit Vorschau (`Oeffnen`) und `Download`.

### 4. Fachliche Kernregeln (massgeblich)

- `skipped` = bereits exportiert (Tracking greift).
- `ignored` = fachlich nicht buchbar.
- OP-relevant sind nur Buchungen mit Gegenkonto `10012000` (Debitor).
- Plattformanreize in Zahlungen werden mit OP-Zuordnung auf Debitor gebucht.
- Kundenzahlung wird vor Servicegebuehr-Abzug berechnet.

### 5. Tracking und Historisierung

- Bestellungen: Tracking ueber `export/.datev_export_state.json`.
- Exportdateien werden vor Ueberschreiben in `export/.history/` archiviert.
- OP-Simulation liest aktuelle Exporte plus passende History-Snapshots.
- Duplikat-Schutz in der OP-Simulation ist implementiert.

## Aktuelles Start-Setup (lokaler Testbetrieb)

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
npm run dev -- --host 0.0.0.0 --port 3001
```

## Empfehlung fuer Weiterarbeit (Integration in Hauptsystem)

1. Dieses Modul als Feature in das Hauptrepo uebernehmen (z. B. via `git subtree`).
2. API unter eigenem Prefix einhaengen, z. B. `/api/temu-datev`.
3. Input/Output Pfade ueber zentrale ENV/Settings steuern.
4. Bestehende Auth, Logging und Deployment-Prozesse des Hauptsystems nutzen.
5. Refactoring der Modulstruktur erst im Zielsystem finalisieren.

## Quellen

- `TEmuAuszahlung/MD_Archive/SESSION_NOTES.md`
- `TEmuAuszahlung/MD_Archive/UPDATE.md`

Hinweis:

- `TEmuAuszahlung/SESSION_NOTES.md` und `TEmuAuszahlung/UPDATE.md` sind als kurze Verweisdateien erhalten.
