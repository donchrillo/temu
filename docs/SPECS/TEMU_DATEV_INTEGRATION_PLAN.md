# TEMU DATEV Integration Plan

**Status:** Draft / Ready for implementation handoff  
**Datum:** 12. März 2026  
**Ziel:** Importiertes `temu-datev` Modul in die bestehende Monorepo-Architektur überführen, ohne eine zweite Standalone-API oder ein zweites Standalone-Frontend beizubehalten.

---

## 1. Ausgangslage

Der aktuelle Hauptstand des Projekts arbeitet mit einem zentralen FastAPI-Gateway in `main.py` und fachlichen Routern in `modules/*`.

Das importierte Subtree-Modul `modules/temu_datev/` bringt dagegen noch eine eigene Standalone-Struktur mit:

- `modules/temu_datev/backend/main.py`
- `modules/temu_datev/backend/routers/*`
- `modules/temu_datev/backend/services/*`
- `modules/temu_datev/frontend-react/*`

Diese Struktur ist aktuell **noch nicht** in das Hauptsystem integriert.

---

## 2. Zielbild

Die Integration folgt den bestehenden Architekturregeln des Monorepos:

1. Fachlogik bleibt in `modules/temu_datev/`.
2. API-Endpunkte werden als Modul-Router in das zentrale Gateway `main.py` eingebunden.
3. Das UI wird in das bestehende React-Frontend `frontend-react/` überführt.
4. Laufzeitdaten werden über zentrale Settings und das bestehende `data/`-Konzept angebunden.
5. Logging und DB-Integration werden vorbereitet, aber nicht als Blocker für Phase 1 behandelt.

---

## 3. Architekturentscheidung

### Beibehalten

- `modules/temu_datev/convert_bestellungen.py`
- `modules/temu_datev/convert_zahlungen.py`
- `modules/temu_datev/datev_writer.py`
- `modules/temu_datev/simulate_op_buchungen.py`
- `modules/temu_datev/config.py` als Übergangsquelle für Fachkonstanten

### Auflösen oder überführen

- `modules/temu_datev/backend/main.py`
- `modules/temu_datev/backend/routers/*`
- `modules/temu_datev/backend/services/*` soweit sie nur API-Adapter oder Datei-Adapter sind
- `modules/temu_datev/frontend-react/*` als eigenständige App

### Zielstruktur

```text
modules/temu_datev/
├── __init__.py
├── router.py
├── services/
│   ├── config.py
│   ├── file_service.py
│   ├── conversion_service.py
│   └── op_service.py
├── schemas.py
├── convert_bestellungen.py
├── convert_zahlungen.py
├── datev_writer.py
└── simulate_op_buchungen.py

frontend-react/src/
├── pages/datev/
│   └── temu-datev.tsx
├── types/temu-datev.ts
└── lib/api-client.ts
```

---

## 4. Migrationsprinzipien

1. Keine zweite FastAPI-App im Monorepo beibehalten.
2. Keine zweite React-App parallel produktiv betreiben.
3. Keine hartcodierten lokalen Arbeitsverzeichnisse im Modul lassen.
4. Delta-Dateien und Exportdaten bleiben außerhalb von Git und laufen über zentrale Pfade.
5. Logging wird technisch kompatibel vorbereitet, aber erst in einer späteren Phase tief integriert.

---

## 5. Delta zu Zielstruktur

### Backend-Mapping

| Alt | Ziel | Bemerkung |
| --- | --- | --- |
| `modules/temu_datev/backend/main.py` | entfällt | Funktion wird durch `main.py` des Hauptsystems ersetzt |
| `modules/temu_datev/backend/routers/files.py` | `modules/temu_datev/router.py` + `services/file_service.py` | Router in Monorepo-Stil überführen |
| `modules/temu_datev/backend/routers/convert.py` | `modules/temu_datev/router.py` + `services/conversion_service.py` | Prefix später `/api/temu-datev/...` |
| `modules/temu_datev/backend/routers/op.py` | `modules/temu_datev/router.py` + `services/op_service.py` | OP-Analyse separat kapseln |
| `modules/temu_datev/backend/routers/exports.py` | `modules/temu_datev/router.py` + `services/file_service.py` | Exportliste, Download, Vorschau |
| `modules/temu_datev/backend/schemas.py` | `modules/temu_datev/schemas.py` | Pydantic-Modelle ans Modul anheben |
| `modules/temu_datev/backend/services/file_service.py` | `modules/temu_datev/services/file_service.py` | Sicherheits- und Encoding-Prüfung |
| `modules/temu_datev/backend/services/conversion_service.py` | `modules/temu_datev/services/conversion_service.py` | Kernlogik bleibt modulnah |

### Frontend-Mapping

| Alt | Ziel | Bemerkung |
| --- | --- | --- |
| `modules/temu_datev/frontend-react/src/pages/dashboard.tsx` | `frontend-react/src/pages/datev/temu-datev.tsx` | In bestehende App-Shell integrieren |
| `modules/temu_datev/frontend-react/src/lib/api-client.ts` | `frontend-react/src/lib/api-client.ts` | Als neuer API-Bereich ergänzen |
| `modules/temu_datev/frontend-react/src/types/*` | `frontend-react/src/types/temu-datev.ts` | Typen konsolidieren |
| `modules/temu_datev/frontend-react/src/components/*` | Bestehende Shared/UI-Komponenten prüfen | Keine doppelte Komponentenwelt |
| `modules/temu_datev/frontend-react/src/index.css` | entfällt oder partiell übernehmen | Nur falls Styles wirklich fehlen |

---

## 6. Laufzeitdaten und Dateiverzeichnisse

Die Verarbeitung benötigt Ein- und Ausgabedateien aus dem Delta-Verzeichnis. Diese dürfen nicht im Modul relativ verdrahtet bleiben.

### Ziel

Pfadkonfiguration über zentrale Settings oder modulnahe Settings mit ENV-Anbindung.

### Vorgeschlagene Zielpfade

```text
data/temu_datev/
├── bestellberichte/
├── zahlungsberichte/
├── export/
└── archive/
```

### Vorgeschlagene ENV-Keys

- `TEMU_DATEV_DELTA_ROOT`
- `TEMU_DATEV_ORDER_INPUT_DIR`
- `TEMU_DATEV_PAYMENT_INPUT_DIR`
- `TEMU_DATEV_EXPORT_DIR`
- `TEMU_DATEV_ARCHIVE_DIR`
- `TEMU_DATEV_EXPORT_STATE_FILE`

### Anmerkung

Die bestehende Datei `modules/temu_datev/config.py` sollte in Phase 1 nicht sofort komplett entfernt werden. Stattdessen:

1. Geschäftskonstanten sukzessive in modulnahe Services-Config verschieben.
2. Dateipfade zuerst auf zentrale Settings umbiegen.

---

## 7. API-Zielstruktur

### Vorgeschlagener Prefix

`/api/temu-datev`

### Endpunkte

- `GET /api/temu-datev/health`
- `GET /api/temu-datev/files/orders`
- `POST /api/temu-datev/files/orders/upload`
- `GET /api/temu-datev/files/orders/{filename}/content`
- `PUT /api/temu-datev/files/orders/{filename}/content`
- `GET /api/temu-datev/files/payments`
- `POST /api/temu-datev/files/payments/upload`
- `GET /api/temu-datev/files/payments/{filename}/content`
- `PUT /api/temu-datev/files/payments/{filename}/content`
- `POST /api/temu-datev/convert/orders`
- `POST /api/temu-datev/convert/payments`
- `POST /api/temu-datev/op/analyze`
- `GET /api/temu-datev/exports`
- `GET /api/temu-datev/exports/{filename}`
- `GET /api/temu-datev/exports/{filename}/content`

### Begründung

Die bisherige Standalone-API nutzt globale Prefixes wie `/api/files` oder `/api/convert`. Diese sind im Monorepo zu generisch und kollisionsanfällig.

---

## 8. Frontend-Zielstruktur

### UI-Integration

Das DATEV-Dashboard wird als neue Feature-Page in die bestehende React-App integriert.

### Vorgeschlagene Route

- `/temu-datev`

### Inhalte der ersten integrierten Ansicht

1. Upload Bestellberichte
2. Upload Zahlungsberichte
3. Dateiliste mit Editor für CSV-Inhalte
4. Konvertierung starten
5. OP-Analyse starten
6. Exportdateien anzeigen und herunterladen

### Frontend-Integration im Hauptprojekt

- Route in `frontend-react/src/App.tsx` ergänzen
- API-Funktionen in `frontend-react/src/lib/api-client.ts` ergänzen
- Typsicherheit in `frontend-react/src/types/temu-datev.ts` ergänzen
- Vorhandene Komponenten aus `components/ui` und `components/shared` wiederverwenden

---

## 9. Cleanup-Backlog

Diese Punkte sollen nach oder während der Integration bereinigt werden.

### Hohe Priorität

- Standalone-API unter `modules/temu_datev/backend/main.py` entkoppeln
- Router und Schemas aus `backend/` ans Modul hochziehen
- Dateipfade aus `modules/temu_datev/config.py` zentralisieren
- Doppelte API-Namensräume vermeiden

### Mittlere Priorität

- `modules/temu_datev/frontend-react/` nach erfolgreicher Übernahme entfernen oder archivieren
- Dublette `workers/router.py` gegen `workers/jobs_router.py` prüfen und bereinigen
- Nicht mehr benötigte README-Abschnitte im importierten Modul an das Monorepo anpassen

### Niedrige Priorität

- Fachkonstanten aus `config.py` weiter entkoppeln
- Logging an `modules/shared/logging/` anschließen
- Business-Events später in DB-Logging integrieren

---

## 10. Umsetzungsphasen

### Phase 1: Konfiguration und Modulgrenzen

Ziel:
Dateipfade und Services so vorbereiten, dass das Modul ohne eigene App betrieben werden kann.

Arbeitspakete:

- zentrale Pfadkonfiguration definieren
- modulnahe Services-Struktur herstellen
- Schemas in das Modul überführen
- bestehende Fachlogik unangetastet lassen

### Phase 2: API-Integration

Ziel:
DATEV-Endpunkte im Haupt-Gateway verfügbar machen.

Arbeitspakete:

- `modules/temu_datev/router.py` anlegen
- Endpunkte aus Standalone-Routern überführen
- `main.py` erweitern
- Health-Ausgabe um das Modul ergänzen

### Phase 3: Frontend-Integration

Ziel:
DATEV-Oberfläche im Hauptfrontend nutzbar machen.

Arbeitspakete:

- neue DATEV-Page anlegen
- API-Client ergänzen
- Typen ergänzen
- Route und Navigation einhängen

### Phase 4: Stabilisierungsrunde

Ziel:
Mit echten Delta-Dateien funktional verifizieren.

Arbeitspakete:

- Upload testen
- Dateibearbeitung testen
- Bestell- und Zahlungs-Konvertierung testen
- OP-Analyse testen
- Exportdateien und State-Dateien prüfen

### Phase 5: Aufräumen

Ziel:
Übergangsstruktur zurückbauen.

Arbeitspakete:

- alte Standalone-Struktur entfernen oder archivieren
- doppelte Frontend-Artefakte bereinigen
- Doku aktualisieren

---

## 11. Akzeptanzkriterien

Die Integration gilt für Phase 1 als erfolgreich, wenn alle folgenden Punkte erfüllt sind:

1. `main.py` bindet das DATEV-Modul wie andere Module per Router ein.
2. Es existiert keine produktiv genutzte zweite FastAPI-App mehr für DATEV.
3. Das Hauptfrontend kann DATEV-Dateien hochladen, anzeigen, bearbeiten und verarbeiten.
4. Alle Laufzeitdaten liegen außerhalb von Git in konfigurierbaren Verzeichnissen.
5. Die Kernlogik bleibt in `modules/temu_datev/` und ist nicht in Frontend oder Gateway verstreut.

---

## 12. Offene Entscheidungen

Diese Punkte sollen vor oder während der Umsetzung bewusst entschieden werden:

1. Soll der Zielpfad unter `data/temu_datev/` oder direkt unter einem vorhandenen Delta-Pfad liegen?
2. Sollen Uploads dauerhaft über die Weboberfläche erfolgen oder primär aus vorhandenen Delta-Verzeichnissen gelesen werden?
3. Sollen Exportdateien im Modul-Kontext verbleiben oder zusätzlich in ein Archiv verschoben werden?
4. Wann wird das DATEV-Logging an das bestehende DB-Logging angeschlossen?

---

## 13. Handoff für die nächste Session

Empfohlener Startpunkt für den nächsten Agenten:

1. `modules/temu_datev/backend/` gegen Zielstruktur mappen
2. zentrale Settings für DATEV-Dateipfade definieren
3. `modules/temu_datev/router.py` und `modules/temu_datev/schemas.py` anlegen
4. API zuerst integrieren, Frontend danach

Empfohlene erste operative Aufgabe:

`Phase 1 umsetzen: DATEV-Dateipfade zentralisieren und Backend-Services aus der Standalone-Struktur in das Modul überführen.`