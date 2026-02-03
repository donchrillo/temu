# Frontend-Struktur (Monorepo ohne Duplikate)

## 📁 Verzeichnisstruktur

### Module Frontends (Source of Truth)
```
/modules/
├── pdf_reader/frontend/
│   ├── pdf.html    → Serviert unter /pdf
│   ├── pdf.css     → Serviert unter /static/pdf.css
│   └── pdf.js      → Serviert unter /static/pdf.js
│
└── temu/frontend/
    ├── temu.html   → Serviert unter /temu
    ├── temu.css    → Serviert unter /static/temu.css
    └── temu.js     → Serviert unter /static/temu.js
```

### Shared Frontend (Root Dashboard)
```
/frontend/
├── index-new.html     → Serviert unter / (Root Dashboard)
├── dashboard.css      → Serviert unter /static/dashboard.css
├── manifest.json      → PWA Manifest
├── service-worker.js  → PWA Service Worker
└── icons/            → PWA Icons
```

## 🔄 Gateway Routing (main.py)

### HTML Routes
- `GET /` → `frontend/index-new.html`
- `GET /pdf` → `modules/pdf_reader/frontend/pdf.html`
- `GET /temu` → `modules/temu/frontend/temu.html`

### Static Files Route
- `GET /static/{filename}`:
  1. Wenn filename mit `pdf.` startet → `modules/pdf_reader/frontend/{filename}`
  2. Wenn filename mit `temu.` startet → `modules/temu/frontend/{filename}`
  3. Sonst → `frontend/{filename}`

## ✅ Vorteile

1. **Keine Duplikate**: Jede Datei existiert nur einmal
2. **Module Separation**: Jedes Modul hat sein eigenes Frontend
3. **Direktes Serving**: Änderungen sofort sichtbar (kein Kopieren nötig)
4. **Klare Struktur**: `modules/<module>/frontend/` ist die einzige Quelle

## 🔧 Änderungen machen

### Modul-Frontend ändern:
```bash
# Direkt in modules/<module>/frontend/ editieren
vim modules/pdf_reader/frontend/pdf.css

# PM2 restart NICHT nötig (Dateien werden direkt serviert)
# Nur Browser-Reload: Ctrl+Shift+R
```

### Root-Dashboard ändern:
```bash
# In frontend/ editieren
vim frontend/index-new.html

# Browser-Reload: Ctrl+Shift+R
```

## 📝 Hinweise

- Alle Module-Frontends haben das **helle Apple-Style Design**
- Alle Seiten haben das **Burger Menu** für Navigation
- TEMU hat **Parameter-Dialoge** für Job-Konfiguration
- Dashboard lädt Modul-Status dynamisch via `/api/health`
