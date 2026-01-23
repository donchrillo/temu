# FRONTEND Architecture

PWA (Progressive Web App) für Worker Dashboard mit WebSocket Live-Updates, HTTPS/WSS, und mobiler Installation.

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
  index.html           # Hauptseite
  app.js              # Hauptlogik (API URL, WebSocket, DOM Updates)
  navbar.js           # Navigationskomponente
  styles.css          # Styling
  manifest.json       # PWA Manifest
  service-worker.js   # Offline-Caching & Lifecycle
  test_websocket.html # Debug-Tool für WS-Verbindung
  pwa-debug.html      # PWA-Validierungs-Check
  icons/
    icon-192.png      # App-Icon (192x192)
    icon-512.png      # App-Icon (512x512)
```

---

## 3. Automatische Protokoll-Erkennung

### Problem (vorher)
```javascript
// ❌ Hardcodiert – funktioniert nicht über HTTPS
const API_URL = `http://192.168.178.4:8000/api`;
const WS_URL = `ws://192.168.178.4:8000/ws/logs`;
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
// Browser navigiert zu: http://localhost:8000
//   → API_URL = "http://localhost:8000/api"
//   → WS_URL = "ws://localhost:8000/ws/logs"
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
192.168.178.4 {
    reverse_proxy localhost:8000 {
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
  '/index.html',
  '/app.js',
  '/navbar.js',
  '/styles.css',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png'
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
# api/server.py
from fastapi.staticfiles import StaticFiles
from pathlib import Path

frontend_dir = Path(__file__).parent.parent / "frontend"

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

## 12. Deployment Checklist

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
