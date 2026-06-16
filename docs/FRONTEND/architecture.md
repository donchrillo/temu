# FRONTEND Architecture

PWA (Progressive Web App) für Worker Dashboard mit WebSocket Live-Updates, HTTPS/WSS, und mobiler Installation.

---

**Datum:** 13. Februar 2026

---

## 1. PWA Übersicht

### Was ist eine PWA?
- **Progressive Web App** – App-ähnliche Erfahrung im Browser
- **Offline-Funktionalität** – Service Worker cacht Ressourcen
- **Installation** – Auf Android/iOS installierbar wie native App
- **Push-Notifications** – Optional (hier nicht implementiert)
- **Live Updates** – WebSocket für Echtzeit-Job-Status

### TOCI Dashboard Features
- Live Job-Status (Inventory Sync, Order Sync)
- WebSocket-Verbindung für Echtzeit-Updates
- Works over HTTPS (Caddy Reverse Proxy)
- Installierbar auf Android Chrome, iOS (begrenzt)
- Service Worker für Offline-Unterstützung

---

## 2. Projektstruktur

```
frontend/
  dashboard.css          # CSS für Root Dashboard
  icons/                 # PWA Icons
    icon-192.png
    icon-512.png
  index-new.html         # Root Dashboard (aktiv)
  manifest.json          # PWA Manifest
  service-worker.js      # Service Worker

modules/
├── pdf_reader/
│   └── frontend/
│       ├── pdf.html       # PDF Reader UI
│       ├── pdf.css        # Modul-spezifisches CSS
│       └── pdf.js         # Modul-spezifisches JavaScript
└── temu/
    └── frontend/
        ├── temu.html      # TEMU Dashboard UI
        ├── temu.css       # Modul-spezifisches CSS
        └── temu.js        # Modul-spezifisches JavaScript
```

---

## 3. Automatische Protokoll-Erkennung

### Problem (vorher)
```javascript
// ❌ Hardcodiert – funktioniert nicht über HTTPS
const API_URL = `http://192.168.178.4:8401/api`;
const WS_URL = `ws://192.168.178.4:8401/ws/logs`;
```

Wenn Nutzer über `https://192.168.178.4` zugreift, lädt Browser die App über HTTPS, aber versucht dann `http://` zu laden → **Mixed Content** Error.

### Lösung (nachher)
```javascript
// ✅ Automatische Erkennung basierend auf aktueller Page
const PROTOCOL = window.location.protocol === 'https:' ? 'https:' : 'http:';
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const HOST = window.location.hostname;
const PORT = window.location.port ? `:${window.location.port}` : '';

const API_URL = `${PROTOCOL}//${HOST}${PORT}/api`;
const WS_URL = `${WS_PROTOCOL}//${HOST}${PORT}/ws/logs`;

// Beispiele:
// Browser navigiert zu: https://192.168.178.4
//   → API_URL = "https://192.168.178.4/api"
//   → WS_URL = "wss://192.168.178.4/ws/logs"
//
// Browser navigiert zu: http://localhost:8401
//   → API_URL = "http://localhost:8401/api"
//   → WS_URL = "ws://localhost:8401/ws/logs"
```

### Praktische Effekte
- ✅ Funktioniert über HTTP (Entwicklung)
- ✅ Funktioniert über HTTPS (Produktion)
- ✅ Funktioniert mit Custom Port
- ✅ Kein hardcodierter Hostname nötig

---

## 4. WebSocket Integration

### Connection Setup (app.js)
```javascript
function initWebSocket() {
  ws = new WebSocket(WS_URL);
  
  ws.onopen = () => {
    console.log('WebSocket connected:', WS_URL);
    // Subscribe to job updates
    ws.send(JSON.stringify({ type: "subscribe", channel: "jobs" }));
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Update UI mit neuen Job-Daten
    updateJobStatus(data);
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    updateUI("❌ WebSocket Verbindungsfehler");
  };
  
  ws.onclose = () => {
    console.log('WebSocket disconnected');
    // Retry nach 3 Sekunden
    setTimeout(initWebSocket, 3000);
  };
}
```

### Message Format
```json
{
  "job_id": "temu_inventory_sync",
  "status": "success",
  "last_run": "2025-01-23T10:45:32Z",
  "duration_seconds": 12.5,
  "error": null
}
```

### Caddy Reverse Proxy – WebSocket Support
```caddyfile
your-server.de {
    reverse_proxy localhost:8401 {
        # ✅ WebSocket Upgrade Headers
        header_up Upgrade {http.request.header.Upgrade}
        header_up Connection {http.request.header.Connection}
    }
    tls internal
    log {
        output file /var/log/caddy/access.log
        level INFO
    }
}
```

**Wichtig:** Ohne diese Headers blockiert Caddy das WebSocket-Upgrade!

---

## 5. manifest.json – PWA Metadaten

```json
{
  "name": "Toci JTL Tools",
  "short_name": "Toci",
  "description": "Worker Dashboard für JTL und Temu Verwaltung",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "orientation": "portrait-primary",
  "background_color": "#ffffff",
  "theme_color": "#0f172a",
  "categories": ["productivity"],
  "prefer_related_applications": false,
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "maskable"
    }
  ]
}
```

### Wichtige Felder
- **`start_url`** – Welche Seite nach Installation geladen wird
- **`scope`** – Welche URLs unter der PWA-Kontrolle sind (`/` = alles)
- **`display: "standalone"`** – Versteckt Browser-UI, sieht wie native App aus
- **`theme_color`** – Farbe der Status-Bar (Android)
- **`icons`** – App-Icons in verschiedenen Größen
- **`purpose: "maskable"`** – Icon für adaptive Android-Icons (neue Androiden schneiden Icon zu)

---

## 6. Service Worker – Offline & Caching

### Basis-Struktur (service-worker.js)
```javascript
const CACHE_NAME = 'toci-v1';
const STATIC_ASSETS = [
  '/',
  '/index-new.html',
  '/dashboard.css',
  '/manifest.json',
  '/service-worker.js',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/static/pdf.html',
  '/static/pdf.css',
  '/static/pdf.js',
  '/static/temu.html',
  '/static/temu.css',
  '/static/temu.js'
];

// Installation: Cache statische Assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Aktivation: Cleanup alte Caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Fetch: Cache-First für Assets, Network-First für APIs
self.addEventListener('fetch', event => {
  const { request } = event;
  
  // API Calls → Network-First (immer aktuell)
  if (request.url.includes('/api/')) {
    return event.respondWith(
      fetch(request)
        .catch(() => caches.match('/index.html'))
    );
  }
  
  // Static Assets → Cache-First
  event.respondWith(
    caches.match(request)
      .then(response => response || fetch(request))
      .catch(() => caches.match('/index.html'))
  );
});
```

### Caching-Strategien
- **Cache-First** – Statische Assets (schneller, aber alt)
- **Network-First** – API-Calls (aktuell, aber langsamer wenn offline)
- **Stale-While-Revalidate** – Optimal (cache sofort, dann update im Hintergrund)

---

## 7. App Icons erstellen

### ImageMagick Kommandos
```bash
# 192x192 Icon
convert -size 192x192 xc:'#0f172a' \
  -fill '#3b82f6' -stroke '#1e40af' -strokewidth 3 \
  -draw "rectangle 30,30 162,162" \
  -fill white -pointsize 40 -gravity center \
  -annotate +0+0 "TOCI" icon-192.png

# 512x512 Icon
convert -size 512x512 xc:'#0f172a' \
  -fill '#3b82f6' -stroke '#1e40af' -strokewidth 8 \
  -draw "rectangle 80,80 432,432" \
  -fill white -pointsize 100 -gravity center \
  -annotate +0+0 "TOCI" icon-512.png
```

### Icon-Anforderungen
- **Quadratisch** (1:1 Verhältnis)
- **PNG Format** (transparenter Hintergrund optional)
- **Größen:** 192x192 (Mindest), 512x512 (Full Size), ggf. 96x96, 128x128, 256x256
- **Farbraum:** RGB oder RGBA
- **Maskable Icon:** Sicherheitsrand von 45px (Icon muss in inneren 110x110 Pixel passen)

---

## 8. Backend: Icon-Route

```python
# main.py
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from starlette.responses import FileResponse

# frontend_dir ist jetzt das Haupt-frontend Verzeichnis
frontend_dir = Path(__file__).parent / "frontend"

@app.get("/icons/{filename}")
async def serve_icons(filename: str):
    """Serve Icons aus frontend/icons/"""
    file_path = frontend_dir / "icons" / filename
    allowed_extensions = {'.png', '.svg', '.ico'}
    
    if file_path.exists() and file_path.suffix.lower() in allowed_extensions:
        return FileResponse(str(file_path))
    
    return {"error": "Icon not found", "requested": filename}
```

---

## 9. Installation auf Geräten

### Android (Chrome)
1. Öffne Chrome auf dem Phone
2. Navigiere zu `https://192.168.178.4`
3. Chrome zeigt "Installieren" in der Adressleiste
4. Tippe auf "Installieren" oder Menü → "App installieren"
5. App erscheint auf Homescreen mit Icon
6. App läuft im Standalone-Modus (keine Browser-UI)

### iOS (Safari / PWA-Unterstützung begrenzt)
- iOS PWA-Support: Limitiert
- Nutzer müssen "Zum Homescreen" manuell wählen
- Keine volle App-Funktionalität wie Android
- WebSocket funktioniert aber über HTTPS

### Desktop (Chrome/Firefox)
- Adressleiste zeigt "Installieren" Icon
- Nach Installation: App aus Menü startbar
- Oder über `chrome://apps`

---

## 10. Debugging & Testing

### WebSocket-Test (test_websocket.html)
```html
<!DOCTYPE html>
<html>
<head>
  <title>WebSocket Test</title>
</head>
<body>
  <h1>WebSocket Connection Test</h1>
  <div id="status">Connecting...</div>
  <div id="messages"></div>
  
  <script>
    const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/logs`;
    
    const ws = new WebSocket(WS_URL);
    const statusDiv = document.getElementById('status');
    const messagesDiv = document.getElementById('messages');
    
    ws.onopen = () => {
      statusDiv.innerHTML = '✅ Connected to ' + WS_URL;
      ws.send(JSON.stringify({ type: "subscribe" }));
    };
    
    ws.onmessage = (event) => {
      messagesDiv.innerHTML += `<p>${event.data}</p>`;
    };
    
    ws.onerror = (error) => {
      statusDiv.innerHTML = '❌ Error: ' + error;
    };
    
    ws.onclose = () => {
      statusDiv.innerHTML = '❌ Disconnected';
    };
  </script>
</body>
</html>
```

**Öffne:** `https://192.168.178.4/test_websocket.html`

### PWA-Validierungs-Check (pwa-debug.html)
```bash
curl -k https://192.168.178.4/pwa-debug.html
```

Prüft:
- ✅ manifest.json erreichbar?
- ✅ Icons geladen?
- ✅ Service Worker registriert?
- ✅ HTTPS aktiv?

---

## 11. Häufige Probleme

### Problem: "Installieren" Button erscheint nicht
```
Ursachen:
- Keine HTTPS (Chrome braucht HTTPS oder localhost)
- manifest.json nicht gefunden (404)
- Icons nicht erreichbar
- Service Worker nicht registriert

Lösung:
1. In DevTools (F12) prüfen: Manifest lädlich? Icons OK?
2. test_websocket.html öffnen – WebSocket OK?
3. pwa-debug.html öffnen – Validator-Check
4. Browser Cache löschen: Ctrl+Shift+Del
```

### Problem: WebSocket verbindet nicht
```
Ursachen (HTTPS):
- Caddy Headers nicht gesetzt (header_up Upgrade, Connection)
- WSS:// Protocol nicht unterstützt vom Server
- Firewall blockiert Port 443

Ursachen (HTTP):
- WS:// statt HTTP:// (false positive – sollte WS sein)
- Falsche Port-Nummer

Debugging:
1. Chrome DevTools → Network → WS
2. Prüfe ob WebSocket-Handshake erfolgreich
3. PM2 logs: pm2 logs temu-api | grep -i websocket
```

### Problem: Icons laden nicht
```
Ursachen:
- /icons/ Route nicht in backend definiert
- Icons nicht im frontend/icons/ Ordner
- Falsche Pfade in manifest.json

Debugging:
curl -k https://192.168.178.4/icons/icon-192.png
# Sollte PNG Binary Response liefern, nicht 404
```

---

## 12. Log Filtering System (28. Januar 2026)

### Problem & Lösung
**Problem:** Log-Filter zeigte dynamisch alle job_id Präfixe, aber Sub-Jobs (order_workflow, tracking_service) waren nicht sichtbar

**Root Cause:** Sub-Jobs teilen die GLEICHE job_id wie Master-Job:
```
temu_orders_1769614356
├── job_type: order_service     (part of same job_id)
├── job_type: order_workflow    (part of same job_id)
├── job_type: tracking_service  (part of same job_id)
└── job_type: temu_service      (part of same job_id)
```

### Lösung: FESTE Filter-Optionen mit LIKE-Pattern Matching

**Frontend (in den relevanten Modul-JS-Dateien, z.B. `/modules/temu/frontend/temu.js` oder `/modules/pdf_reader/frontend/pdf.js`):**
```javascript
function updateJobFilter() {
    const select = document.getElementById('filter-job');
    
    // Feste Filter-Optionen mit LIKE-Patterns
    const filterOptions = [
        { value: '', label: '— Alle Jobs —' },
        { value: 'temu_orders%', label: 'TEMU Bestellungen (Auftragsverarbeitung)' },
        { value: 'temu_inventory%', label: 'TEMU Lagerbestand (Inventar)' },
        { value: 'sync_orders%', label: 'Synchronisiere neue Temu Aufträge' },
        { value: 'sync_inventory%', label: 'Synchronisiere Temu Lagerbestand' }
    ];
    
    filterOptions.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt.value;  // z.B. "temu_orders%"
        option.textContent = opt.label;
        select.appendChild(option);
    });
}

async function loadAllLogs() {
    const jobIdPattern = document.getElementById('filter-job').value; // "temu_orders%"
    const url = `${API_URL}/logs?job_id=${jobIdPattern}`;
    // Sendet "temu_orders%" an Backend
}
```

**Backend (modules/shared/database/repositories/common/log_repository.py):**
```python
def get_logs(self, job_id: str = None, ...):
    if job_id:
        # job_id kommt bereits als LIKE-Pattern z.B. "temu_orders%"
        if '%' in job_id:
            where_clauses.append("job_id LIKE :job_id_pattern")
            params["job_id_pattern"] = job_id  # Nutze direkt ohne % hinzuzufügen
        else:
            where_clauses.append("job_id LIKE :job_id_pattern")
            params["job_id_pattern"] = f"{job_id}%"  # Füge % hinzu wenn nicht vorhanden
```

### Effekt
| Filter | Zeigt Logs von | Beispiel job_types |
|--------|-----------------|------------------|
| `temu_orders%` | Alle Aufträge verarbeitung | order_service, order_workflow, tracking_service, temu_service |
| `temu_inventory%` | Alle Lagerbestand Operationen | inventory_workflow, inventory_to_api, jtl_to_inventory |
| `sync_orders%` | Manuelle Auftrags-Sync | sync_orders |
| `sync_inventory%` | Manuelle Lagerbestand-Sync | sync_inventory |

### Zukünftige Filter hinzufügen
Einfach neue Optionen in `filterOptions` Array (frontend/app.js) hinzufügen:
```javascript
{ value: 'pdf_upload%', label: 'PDF Upload & Verarbeitung' }
```

---

## 13. Deployment Checklist

- [x] manifest.json mit korrektem Icons-Pfad
- [x] Icons in frontend/icons/ vorhanden (PNG, 192x192 + 512x512)
- [x] Backend hat /icons/{filename} Route
- [x] Service Worker registriert in index.html
- [x] app.js nutzt automatische Protokoll-Erkennung
- [x] Caddy Header-Konfiguration (WebSocket)
- [x] HTTPS aktiviert (Caddy tls internal)
- [x] PM2 restart nach Changes
- [x] Browser Cache gelöscht (Ctrl+Shift+Del)
- [x] Test auf mobilem Gerät

---

**Summe:** PWA funktioniert über HTTPS mit WebSocket, Icons, und ist auf Android/iOS installierbar. Service Worker für Offline-Support. Debugging-Tools für schnelle Fehlersuche.

---

## 14. CSS Architecture & Consolidation

### Übersicht
Das Projekt verwendet ein **zentralisiertes CSS-System** mit `master.css` für gemeinsame Styles und modulspezifischen CSS-Dateien für individuelle Komponenten.

### Master CSS (`frontend/master.css`)
**700 Zeilen gemeinsame Styles** - eliminiert 1,537 Zeilen Duplikate

**Enthält:**
- **CSS Variables** (:root) - Farben, Spacing, Radius, Fonts
- **Base Reset** - *, body, container, header
- **Shared Components** - Cards, Buttons, Tabs, Upload Zones  
- **Burger Menu** - Komplette mobile Navigation
- **Toast Notifications** - Erfolgs-/Fehlermeldungen
- **Progress Overlay** - Loading-Anzeige mit Animationen
- **Common Animations** - keyframes (slideIn, spin, pulse)

### Module CSS Files
Jedes Modul hat nur noch **modul-spezifische** Styles:

- **dashboard.css** (155 Zeilen) - Module grid, module cards, status overview
- **pdf.css** (161 Zeilen) - File lists, log display, cleanup section
- **temu.css** (272 Zeilen) - Status grid, trigger grid, jobs list, modal dialogs
- **csv.css** (545 Zeilen) - Metrics, reports, export section, CSV-specific components

### Integration
Alle HTML-Dateien laden master.css **VOR** ihrem modul-spezifischen CSS:

```html
<link rel="stylesheet" href="/static/master.css?v=20260206b">
<link rel="stylesheet" href="/static/module.css?v=20260206">
```

### Code-Reduktion
- **Vorher:** ~3,500 Zeilen CSS (über alle Module)
- **Nachher:** 700 (master.css) + ~1,163 (Module) = 1,863 Zeilen
- **Gespart:** 1,537 Zeilen eliminierter Duplikate (44% Reduktion)

### Wartbarkeit
✅ **Zentral:** Änderungen an Buttons/Navigation nur an 1 Stelle  
✅ **Konsistent:** Gleiches Look & Feel über alle Module  
✅ **Skalierbar:** Neue Module erben automatisch alle Basis-Styles  
✅ **Performant:** Weniger CSS-Downloads, besseres Caching

---

## 15. Shared UI Components System

### Übersicht
Das Frontend nutzt ein **zentralisiertes UI-Components System** zur Eliminierung von Duplikaten und konsistenter Benutzerinterktion.

### Komponenten

#### 1. `progress-helper.js` – Progress-Anzeige (Refactored ✅)
**Datei:** `frontend/components/progress-helper.js`

Animierte Progress-Anzeige mit zwei Modi:

**A. Auto-Increment Modus** (TEMU, PDF):
```javascript
// Automatische Inkrementierung (Prozent steigt kontinuierlich)
showProgress('Processing...', 'auto');  
// ProgressOverlay zeigt: 0% → 5% → 15% → 30% → ...
updateProgressText('Importing data...');
hideProgress();
```

**B. Simple Modus** (CSV):
```javascript
// Manuelle Kontrolle (0-100%)
showProgress('Processing...', 0);
updateProgress(25);   // 25%
updateProgress(50);   // 50%
updateProgress(100);  // 100%
hideProgress();
```

**Features:**
- ✅ `ProgressOverlay` Module Pattern mit gecachten DOM-Referenzen  
- ✅ `DEFAULT_PROGRESS_STEPS` Konstante für Auto-Increment Intervalle
- ✅ Rückwärtskompatible API (alte Aufrufe funktionieren noch)
- ✅ Eliminiert ~55 Zeilen duplizierter Code aus temu.js + pdf.js

#### 2. `ui-helpers.js` – Shared Toast & Log Formatting (NEW ✅)
**Datei:** `frontend/components/ui-helpers.js`

Zentrale Utilities für Toast-Notifications und Log-Formatting:

```javascript
// Toast Notifications
showToast(message, type, duration);
// Type: 'success' (grün), 'error' (rot), 'info' (blau)
// Beispiel: showToast('✅ CSV uploaded', 'success', 3000);

// Log Entry Formatting
formatLogEntry(jobId, jobType, message, level);
// Gibt HTML-String zurück für Log-Anzeige
```

**Features:**
- ✅ Einheitliche Look & Feel über alle Module
- ✅ Eliminiert ~75 Zeilen duplizierter Code aus temu.js + pdf.js  
- ✅ Auto-Clearing nach Duration
- ✅ Styled Toasts mit Icons und Animationen

#### 3. `nav-loader.js` – Central Navigation (Refactored ✅)
**Datei:** `frontend/components/nav-loader.js`

Dynamisch geladene Navigation mit Burger-Menü:

**Funktionen:**
```javascript
loadNavigation(pageKey, title);      // Navigation laden & aktualisieren
toggleMenu();                         // Menü öffnen/schließen
setActiveMenuItem(pageKey);           // Aktives Menü markieren
setNavTitle(title);                   // Header-Titel setzen
closeMenu();                          // Menü schließen (Helper-Funktion)
initMenuBehavior();                   // Menü-Event-Listener setupen
```

**Features:**
- ✅ Zentrale Menu-Close-Logik (3× Duplikat → 1× Funktion)
- ✅ `NAV_CONFIG` Konstante (Magic Strings entfernt)
- ✅ JSDoc für alle Funktionen
- ✅ Lazy-Laden der Navigation Template

**Datei:** `frontend/components/navigation.html`
- Zentrale Definition aller Menüpunkte
- Burger-Menü mit Links zu allen Modulen
- Einmalige Pflege für alle Seiten

### Integration in neue Seiten

```html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Meine Seite</title>
    <link rel="stylesheet" href="/static/master.css">
    <link rel="stylesheet" href="/static/meine-seite.css">
</head>
<body>
    <!-- Shared Components: Navigation, Toast, Logging -->
    <script src="/components/nav-loader.js"></script>
    <script src="/components/progress-helper.js"></script>
    <script src="/components/ui-helpers.js"></script>
    <script>loadNavigation('page-key', '🎯 Titel der Seite');</script>

    <div class="container">
        <!-- Dein Content -->
    </div>

    <script src="/static/meine-seite.js"></script>
</body>
</html>
```

### Neue Seite zum Menü hinzufügen

1. **Navigation HTML bearbeiten** (`frontend/components/navigation.html`):
   ```html
   <a href="/neue-seite" class="menu-item" data-page="neue-seite">
       🎯 Neue Seite
   </a>
   ```

2. **Route in main.py:**
   ```python
   @app.get("/neue-seite")
   async def neue_seite_ui():
       html = Path(__file__).parent / "modules" / "neue_seite" / "frontend" / "index.html"
       return FileResponse(str(html))
   ```

3. **HTML Integration:**
   ```html
   <script>loadNavigation('neue-seite', '🎯 Neue Seite');</script>
   ```

### Vorteile

✅ **Zentral:** Ein Menü für alle Seiten  
✅ **Einfach:** Neue Seiten in 1 Datei hinzufügen  
✅ **Konsistent:** Gleiches Look & Feel überall  
✅ **Wartbar:** Änderungen nur an einer Stelle  
✅ **Modern:** Burger-Menü auf allen Geräten  
✅ **Animiert:** Progress-Overlay für bessere UX

---

## 16. Module Frontend Refactoring (13. Februar 2026) ✅

### TEMU Frontend (`modules/temu/frontend/`)
**Refactoring Status:** ✅ Abgeschlossen

**Verbesserungen:**

1. **Security – XSS in `renderJob()` behoben:**
   ```javascript
   // ❌ VORHER: innerHTML mit API-Daten (XSS)
   jobElement.innerHTML = `<p>${job.name}</p>`;
   
   // ✅ NACHHER: DOM-Erstellung mit textContent
   const nameEl = document.createElement('p');
   nameEl.textContent = job.name;  // Automatisch escaped
   jobElement.appendChild(nameEl);
   ```

2. **DRY – triggerJob() Helper (2× dupliziertes Pattern):**
   ```javascript
   // Generischer Helper für Job-Auslösung
   triggerJob(jobId, jobType, onProgress, onSuccess)
   // Ersetzt ~40 Zeilen duplicated trigger code
   ```

3. **DRY – showModal() Helper (2× Dialog mit inline Styles):**
   ```javascript
   // Modal-Dialog + Inline-Styles → CSS-Klassen + DOM-Erstellung
   showModal(title, formFields, onSubmit)
   // Eliminiert ~120 Zeilen Duplikat HTML
   ```

4. **Performance – DOM-Caching via `getProgressElements()`:**
   ```javascript
   // ❌ VORHER: 4× getElementById() pro Progress-Update
   document.getElementById('progress');
   document.getElementById('progress-bar');
   // → Performance-Hit bei schnellen Updates
   
   // ✅ NACHHER: Lazy-Init Caching
   getProgressElements() → { container, bar, text, ... }
   ```

5. **Code Quality:**
   - Magic Strings → `TEMU_CONFIG` Konstante (Endpoints, Selectors, Timings)
   - `formatLogEntry()` als eigene Funktion extrahiert
   - `createVerboseCheckbox()` Helper extrahiert (war 2× dupliziert)
   - CSS-Duplikate aus `master.css` entfernt
   - Neue CSS-Klassen hinzugefügt (`.modal-form-grid`, `.modal-field-hint`, `.job-actions`)

**Impact:** Low  
**Breaking Changes:** None

### PDF Frontend (`modules/pdf_reader/frontend/`)
**Refactoring Status:** ✅ Abgeschlossen

**Verbesserungen:**

1. **DRY – performAction() Helper (6× identisches try/catch/progress Pattern):**
   ```javascript
   // ❌ VORHER: 6× Copy-Paste try/catch/progress/toast Code
   // extract_rechnungen() { try { progress(); ... toast(); } catch {} }
   // extract_werbung() { try { progress(); ... toast(); } catch {} }
   
   // ✅ NACHHER: Generischer Helper
   performAction(endpoint, actionName, fileList, onSuccess)
   // Alle 6 Actions nutzen jetzt gleiche Logik
   ```

2. **DRY – fileState Map statt separate Arrays:**
   ```javascript
   // ❌ VORHER: Separate Arrays
   const werbungFiles = [];
   const rechnungenFiles = [];
   if (type === 'werbung') werbungFiles.push(file);
   else rechnungenFiles.push(file);
   
   // ✅ NACHHER: Einheitliche Map-Struktur
   const fileState = {
       werbung: { files: [], status: 'idle' },
       rechnungen: { files: [], status: 'idle' }
   };
   // Bessere Struktur, weniger if/else
   ```

3. **Security – XSS in `renderFileList()` behoben:**
   ```javascript
   // ❌ VORHER: innerHTML mit file.name
   list.innerHTML = `<li>${file.name}</li>`;
   
   // ✅ NACHHER: DOM mit textContent
   const li = document.createElement('li');
   li.textContent = file.name;  // Safe
   ```

4. **Performance – DOM-Caching:**
   ```javascript
   // ❌ VORHER: 4× getElementById() pro Progress-Aufruf
   // ✅ NACHHER: Gecachte `getProgressElements()`
   ```

5. **Code Quality:**
   - Magic Strings → `PDF_CONFIG` Konstante
   - Log-Formatierung → `formatLogEntry()` Funktion
   - CSS-Duplikate entfernt (`.log-controls` aus master)
   - `.status-info-grid` Klasse für Dynamisches Status-Grid

**Impact:** Low  
**Breaking Changes:** None

---

## 17. Service Worker & Dashboard Refactoring (13. Februar 2026) ✅

### Service Worker (`frontend/service-worker.js`)
**Verbesserungen:**

1. **Modernisierung – Callbacks → async/await:**
   ```javascript
   // ❌ VORHER: .then() Callbacks
   self.addEventListener('activate', event => {
       event.waitUntil(
           caches.keys().then(keys => {
               return Promise.all(
                   keys.map(key => caches.delete(key))
               );
           })
       );
   });
   
   // ✅ NACHHER: async/await
   async function cleanOldCaches() {
       const keys = await caches.keys();
       await Promise.all(keys.map(key => caches.delete(key)));
   }
   ```

2. **Naming – `ASSETS` → `PRECACHE_ASSETS`:**
   - Beschreiblicher Name
   - CLI Grep-Freundlichkeit

3. **Version Bumping:**
   - Cache-Version erhöht für neue Assets
   - Service Worker Update triggert Client-Refresh

### Dashboard (`frontend/index-new.html` + `dashboard.js`)
**Verbesserungen:**

1. **Cleanup – Inline Scripts → externe `dashboard.js`:**
   ```html
   <!-- ❌ VORHER: 30 Zeilen inline Script -->
   <script>
       // Status laden
       // Offline rendering
       // SW registrieren
   </script>
   
   <!-- ✅ NACHHER: Externe Datei -->
   <script src="/static/dashboard.js"></script>
   ```

2. **Neue dashboard.js Funktionen:**
   ```javascript
   // Config in DASHBOARD_CONFIG
   // loadStatus() – API Status fetchen
   // renderOfflineStatus() – Fallback UI
   // registerServiceWorker() – PWA Registration
   ```

### Docs (`frontend/docs.html`)
**Verbesserungen:**

1. **CSS Reorganization – Inline Styles → master.css:**
   ```html
   <!-- ❌ VORHER: Inline <style> Tags -->
   <style>
       .docs-page { color: #333; }
       .swagger-container { padding: 20px; }
   </style>
   
   <!-- ✅ NACHHER: In dashboard.css verschoben -->
   ```

2. **Cache-Busting:**
   - CSS Version hinzugefügt (`?v=20260213`)

---

**Zuletzt aktualisiert:** 13. Februar 2026  
**Status:** ✅ Voll funktionsfähig (PWA, WebSocket, HTTPS, CSS Consolidation, Shared Components, Module Refactoring)
