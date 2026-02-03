# PDF Reader Module

PDF Upload, Verarbeitung und Analyse für Rechnungen und Werbung (Amazon Ads).

## Features

### Werbung (Amazon Advertising)
- ✅ PDF-Upload mit Drag & Drop
- ✅ Erste Seite extrahieren (normalisierte Dateinamen)
- ✅ Daten parsen (Rechnungsnummer, Betrag, Datum, Land)
- ✅ Excel-Export

### Rechnungen (Standard Invoices)
- ✅ PDF-Upload mit Drag & Drop
- ✅ Daten extrahieren
- ✅ Excel-Export

### UI
- ✅ Modernes, helles Apple-Style Design
- ✅ Responsive (Mobile & Desktop)
- ✅ Live-Logs
- ✅ Toast-Notifications
- ✅ Status-Übersicht

## API Endpoints

### Health & Status
- `GET /health` - Health Check
- `GET /status` - Datei-Status (Anzahl hochgeladene Dateien)

### Werbung
- `POST /werbung/upload` - Upload PDFs (optional mit `?process=true`)
- `POST /werbung/extract` - Erste Seiten extrahieren
- `POST /werbung/process` - Zu Excel verarbeiten
- `GET /werbung/result` - Excel-Datei downloaden

### Rechnungen
- `POST /rechnungen/upload` - Upload PDFs (optional mit `?process=true`)
- `POST /rechnungen/process` - Zu Excel verarbeiten
- `GET /rechnungen/result` - Excel-Datei downloaden

### Logs & Cleanup
- `GET /logs/{logfile}` - Log-Datei abrufen
- `POST /cleanup` - Alle Dateien löschen

## Verwendung

### Im Gateway (main.py)
```python
from modules.pdf_reader import get_router

app.include_router(
    get_router(),
    prefix="/api/pdf",
    tags=["PDF Processor"]
)
```

### Standalone-Test
```python
# Test-Skript
from modules.pdf_reader.router import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router, prefix="/api/pdf")

# uvicorn test:app --reload
```

### Frontend
Das Frontend liegt in `modules/pdf_reader/frontend/`:
- `pdf.html` - Haupt-UI
- `pdf.css` - Apple-Style CSS
- `pdf.js` - Funktionalität

Frontend wird über das Gateway bedient:
- HTML: `/pdf` → `modules/pdf_reader/frontend/pdf.html`
- Assets: `/static/pdf.css`, `/static/pdf.js`

## Workflow

### Werbung (3 Schritte)
1. **Upload:** PDFs hochladen
2. **Extract:** Erste Seiten extrahieren → TMP-Verzeichnis
3. **Process:** Daten parsen → Excel-Export

### Rechnungen (2 Schritte)
1. **Upload:** PDFs hochladen
2. **Process:** Daten extrahieren → Excel-Export

## Verzeichnisse

```
data/pdf_reader/
├── eingang/
│   ├── werbung/        # Upload-Verzeichnis Werbung
│   └── rechnungen/     # Upload-Verzeichnis Rechnungen
├── tmp/                # Extrahierte erste Seiten (Werbung)
└── ausgang/            # Excel-Exporte
    ├── werbung.xlsx
    └── rechnungen.xlsx
```

## Services (bestehende Logik)

Die Business Logic liegt weiterhin in `src/modules/pdf_reader/`:
- `werbung_service.py` - Werbung-Verarbeitung
- `werbung_extraction_service.py` - Seiten-Extraktion
- `rechnungen_service.py` - Rechnungs-Verarbeitung
- `document_identifier.py` - Dokumenttyp-Erkennung
- `patterns.py` - Regex-Patterns

Das Modul ist ein **Re-Export-Wrapper** - keine Änderungen an der bestehenden Logik!

## Design

**Apple-Style UI:**
- Helle Farben (#F2F2F7 Background, #FFFFFF Cards)
- San Francisco Font (-apple-system)
- Smooth Animations
- Glassmorphism-Effekte
- Responsive Grid-Layout

## Version

1.0.0 - Initial Release
