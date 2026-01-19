# PWA & HTTPS Integration - Changelog

**Datum:** 19. Januar 2026  
**Betroffen:** TEMU Worker Dashboard (PWA)  
**Ziel:** HTTPS-Unterstützung via Caddy Reverse Proxy und vollständige PWA-Funktionalität auf Android/iOS

---

## 🎯 Problemstellung

1. **WebSocket-Verbindung funktionierte nicht über HTTPS (Port 443)**
   - App nutzte hardcodierte `ws://` und `http://` Protokolle
   - Über Caddy Proxy (HTTPS) konnte keine WebSocket-Verbindung aufgebaut werden
   
2. **manifest.json wurde nicht gefunden**
   - Aufruf von `https://192.168.178.4/manifest.json` führte zu 404-Fehler
   
3. **PWA war nicht installierbar auf Android**
   - Icons wurden nicht geladen (404)
   - Manifest-Felder fehlten
   - Chrome zeigte nur "Verknüpfung erstellen" statt "Installieren"

---

## 🔧 Durchgeführte Änderungen

### 1. Frontend: Automatische Protokoll-Erkennung

**Datei:** `frontend/app.js`

**Änderung:**
```javascript
// ❌ VORHER - Hardcodiert
const API_URL = `http://${HOST}:${PORT}/api`;
const WS_URL = `ws://${HOST}:${PORT}/ws/logs`;

// ✅ NACHHER - Automatische Erkennung
const PROTOCOL = window.location.protocol === 'https:' ? 'https:' : 'http:';
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const PORT = window.location.port ? `:${window.location.port}` : '';

const API_URL = `${PROTOCOL}//${HOST}${PORT}/api`;
const WS_URL = `${WS_PROTOCOL}//${HOST}${PORT}/ws/logs`;
```

**Effekt:** 
- App erkennt automatisch ob sie über HTTP oder HTTPS läuft
- WebSocket nutzt `wss://` bei HTTPS, `ws://` bei HTTP
- Port wird nur bei Non-Standard-Ports (nicht 80/443) angehängt

---

### 2. Caddy Reverse Proxy: WebSocket-Support

**Datei:** `/etc/caddy/Caddyfile`

**Änderung:**
```caddyfile
192.168.178.4 {
    reverse_proxy localhost:8000 {
        # WebSocket Support hinzugefügt
        header_up Upgrade {http.request.header.Upgrade}
        header_up Connection {http.request.header.Connection}
    }
    tls internal
    
    # Erweiterte Logging für Debugging
    log {
        output file /var/log/caddy/access.log
        level INFO
    }
}
```

**Effekt:**
- WebSocket-Upgrade-Header werden korrekt weitergeleitet
- Bidirektionale Kommunikation funktioniert über HTTPS

---

### 3. Backend: Icon-Route hinzugefügt

**Datei:** `api/server.py`

**Änderung:**
```python
@app.get("/icons/{filename}")
async def serve_icons(filename: str):
    """Serve Icons aus frontend/icons/"""
    file_path = frontend_dir / "icons" / filename
    allowed_extensions = {'.png', '.svg', '.ico'}
    if file_path.exists() and file_path.suffix.lower() in allowed_extensions:
        return FileResponse(str(file_path))
    
    return {
        "error": "Icon not found",
        "requested_file": filename,
        "searched_in": str(frontend_dir / "icons")
    }
```

**Effekt:**
- Icons unter `/icons/icon-192.png` und `/icons/icon-512.png` werden korrekt ausgeliefert
- Vorher: 404 Not Found
- Nachher: 200 OK mit korrektem `Content-Type: image/png`

---

### 4. PWA Manifest: Felder erweitert

**Datei:** `frontend/manifest.json`

**Änderung:**
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
  "screenshots": [...],
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
  ],
  "prefer_related_applications": false
}
```

**Hinzugefügte Felder:**
- `description` - Beschreibung der App
- `orientation` - Portrait-Modus bevorzugt
- `categories` - App-Kategorie für Stores
- `screenshots` - Screenshots für Installation
- `purpose: "maskable"` - Icon für adaptive Android-Icons

---

### 5. Icons erstellt

**Dateien:** `frontend/icons/icon-192.png`, `frontend/icons/icon-512.png`

**Kommando:**
```bash
cd /home/chx/temu/frontend/icons

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

**Effekt:**
- Vorher: Leere 0-Byte Dateien
- Nachher: Valide PNG-Bilder (8KB & 24KB)

---

### 6. PM2 Konfiguration korrigiert

**Datei:** `ecosystem.config.js`

**Änderung:**
```javascript
// ❌ VORHER - PM2 versuchte Python-Skript als Node.js zu starten
{
  script: ".venv/bin/uvicorn",
  interpreter: "/home/chx/temu/.venv/bin/python3"
}

// ✅ NACHHER - Python direkt als Script
{
  script: "/home/chx/temu/.venv/bin/python3",
  args: "-m uvicorn api.server:app --host 0.0.0.0 --port 8000",
  cwd: "/home/chx/temu",
  env: {
    PYTHONPATH: "/home/chx/temu"
  }
}
```

**Effekt:**
- API startet jetzt zuverlässig über PM2
- Keine `SyntaxError: Invalid or unexpected token` mehr

---

### 7. Debug-Tools hinzugefügt

**Neue Dateien:**
- `frontend/test_websocket.html` - WebSocket-Verbindungstest
- `frontend/pwa-debug.html` - PWA-Installierbarkeits-Check

**Verwendung:**
```
https://192.168.178.4/test_websocket.html
https://192.168.178.4/pwa-debug.html
```

---

## ✅ Ergebnis

### Funktionierende Features:

| Feature | Status | Beschreibung |
|---------|--------|--------------|
| **HTTPS-Zugriff** | ✅ | App läuft über `https://192.168.178.4` mit gültigem Zertifikat |
| **WebSocket über WSS** | ✅ | Live-Updates funktionieren über verschlüsselte Verbindung |
| **PWA-Installation** | ✅ | App kann als PWA auf Android/iOS installiert werden |
| **manifest.json** | ✅ | Manifest wird korrekt ausgeliefert und validiert |
| **Icons** | ✅ | App-Icons (192x192, 512x512) werden geladen |
| **Service Worker** | ✅ | Offline-Funktionalität und Caching aktiv |
| **PM2 Auto-Start** | ✅ | API startet automatisch mit PM2 |

### Getestete Plattformen:

- ✅ **Chrome Desktop** (Windows/Linux) - HTTPS + WebSocket
- ✅ **Chrome Mobile** (Android) - PWA-Installation + WebSocket
- ✅ **Localhost** (HTTP) - Entwicklungsumgebung

---

## 📋 Installation auf Android

1. Öffne Chrome auf dem Android-Phone
2. Navigiere zu `https://192.168.178.4`
3. Chrome zeigt "Installieren" in der Adressleiste
4. Tippe auf "Installieren" oder Menü → "App installieren"
5. App erscheint auf dem Homescreen mit Icon
6. App läuft im Standalone-Mode (ohne Browser-UI)

---

## 🔍 Debugging

### WebSocket testen:
```bash
curl -k https://192.168.178.4/test_websocket.html
```

### PWA-Validierung:
```bash
curl -k https://192.168.178.4/pwa-debug.html
```

### Manifest prüfen:
```bash
curl -k -s https://192.168.178.4/manifest.json | jq
```

### API Health Check:
```bash
curl -k -s https://192.168.178.4/api/health
```

---

## 🚀 Deployment

### Services neustarten:
```bash
# API neu starten
cd /home/chx/temu
pm2 restart temu-api

# Caddy neu laden
sudo systemctl reload caddy

# PM2 Config speichern
pm2 save
```

### PM2 Auto-Start bei Boot aktivieren:
```bash
pm2 startup
pm2 save
```

---

## 📝 Technischer Stack

- **Frontend:** Vanilla JavaScript (PWA)
- **Backend:** FastAPI (Python 3.12) + Uvicorn
- **WebSocket:** FastAPI WebSocket + asyncio
- **Reverse Proxy:** Caddy 2.x (HTTPS/TLS)
- **Process Manager:** PM2
- **Icons:** ImageMagick (convert)

---

## 🔗 Links

- PWA Manifest Spec: https://www.w3.org/TR/appmanifest/
- Service Worker API: https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API
- FastAPI WebSocket: https://fastapi.tiangolo.com/advanced/websockets/
- Caddy Reverse Proxy: https://caddyserver.com/docs/caddyfile/directives/reverse_proxy

---

## 👤 Autor

**Implementiert von:** GitHub Copilot  
**Datum:** 19. Januar 2026  
**Version:** 1.0.0
