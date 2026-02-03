# Frontend Cache Fix – 2026-02-03

## Übersicht

Fix für Multi-Layer-Caching-Problem im PDF Reader Frontend, das verhinderte, dass Updates und Logs im Browser angezeigt wurden.

**Symptome:**
- Frontend zeigte "0 Dateien" trotz erfolgreicher PDF-Uploads
- Logs wurden nicht angezeigt, obwohl sie auf dem Server geschrieben wurden
- Problem trat nur über Caddy Reverse Proxy (https://192.168.178.4) auf
- Direkter Zugriff (:8000) funktionierte einwandfrei

**Root Cause:**
Drei unabhängige Cache-Layer cachten veraltete Daten:
1. **Caddy Reverse Proxy**: API-Responses wurden mit `max-age=3600` (1 Stunde) gecacht
2. **Service Worker**: Assets ohne Query-Parameter wurden unbegrenzt gecacht
3. **Browser HTTP Cache**: Gespeicherte Responses mit 1-Stunden-TTL

---

## Problem-Analyse

### Schicht 1: Caddy Reverse Proxy Caching

**Datei: `/etc/caddy/Caddyfile` (ALT)**

```caddy
https://192.168.178.4 {
    reverse_proxy localhost:8000

    # PROBLEM: Alle Requests (inkl. /api/*) wurden gecacht
    header {
        Cache-Control "public, max-age=3600"
    }

    # Statische Module-Dateien: 1 Jahr Cache
    @modulefiles {
        path /static/*.js /static/*.css
    }
    header @modulefiles {
        Cache-Control "public, max-age=31536000, immutable"
    }
}
```

**Problem:**
- `/api/pdf/status` → gecacht für 1 Stunde → Frontend zeigte alte Werte
- `/api/pdf/logs/werbung_extraction.log` → gecacht → alte Logs
- Header-Konflikt: `@api` no-cache Regel wurde von default Regel überschrieben

**Beweis:**
```bash
curl -I https://192.168.178.4/api/pdf/status
# cache-control: public, max-age=3600  ❌
# expires: 0                            ❌
# pragma: no-cache                      ❌
# → Widersprüchliche Header, default-Regel gewann
```

### Schicht 2: Service Worker Caching

**Datei: `frontend/service-worker.js` (ALT)**

```javascript
const CACHE_NAME = 'toci-tools-cache-v2026020316';
const ASSETS = [
  '/static/pdf.css',    // ❌ Ohne ?v= Parameter
  '/static/pdf.js',     // ❌ Ohne ?v= Parameter
];
```

**Problem:**
- HTML lud `/static/pdf.js?v=20260203` (mit Query-Parameter)
- Service Worker cachte `/static/pdf.js` (ohne Query-Parameter)
- Browser forderte beide URLs an → Cache-Miss → alte Datei wurde geladen

**Beweis:**
```javascript
// HTML
<script src="/static/pdf.js?v=20260203"></script>

// Service Worker ASSETS
'/static/pdf.js'  // ❌ URL-Mismatch → Cache-Miss
```

### Schicht 3: Browser HTTP Cache

**Problem:**
- Browser hatte alte Responses mit 1-Stunden-TTL gecacht
- Selbst nach Caddy-Fix wurden gecachte Responses verwendet
- Hard-Refresh half nicht, da Service Worker zwischengeschaltet war

**Beweis:**
```
Incognito Mode → Frontend funktionierte ✅
Normaler Browser → Frontend zeigte alte Daten ❌
→ Browser-Cache war das Problem
```

---

## Lösung

### Fix 1: Caddy – Explizite No-Cache für API

**Datei: `/etc/caddy/Caddyfile` (NEU)**

```caddy
https://192.168.178.4 {
    reverse_proxy localhost:8000

    # ✅ API Calls: NIEMALS CACHEN!
    @api {
        path /api/*
    }
    header @api {
        Cache-Control "no-cache, no-store, must-revalidate"
        Pragma "no-cache"
        Expires "0"
    }

    # ✅ Static Module Files: Cache-Busting mit Query-Parametern
    @modulefiles {
        path /static/*.js /static/*.css
    }
    header @modulefiles {
        Cache-Control "public, max-age=300, must-revalidate"
    }

    # ✅ Alles andere (AUSSER /api/*): 1 Stunde
    @notapi {
        not path /api/*
    }
    header @notapi {
        Cache-Control "public, max-age=3600"
    }
}
```

**Änderungen:**
1. **Explizite No-Cache für `/api/*`** mit `@api` Matcher
2. **Negative Matcher** `@notapi` mit `not path /api/*` verhindert Header-Konflikte
3. **Reduzierter Cache** für Module-Dateien: 1 Jahr → 5 Minuten (mit `must-revalidate`)

**Test:**
```bash
curl -I https://192.168.178.4/api/pdf/status
# cache-control: no-cache, no-store, must-revalidate ✅
# pragma: no-cache ✅
# expires: 0 ✅
```

**Wichtig:** Caddy neu laden!
```bash
sudo systemctl reload caddy
# ODER
sudo systemctl restart caddy
```

### Fix 2: Service Worker – Query-Parameter in ASSETS

**Datei: `frontend/service-worker.js` (NEU)**

```javascript
const CACHE_NAME = 'toci-tools-cache-v2026020318'; // ✅ Version erhöht
const ASSETS = [
  '/',
  '/temu',
  '/pdf',
  '/manifest.json',
  '/static/dashboard.css',
  '/static/pdf.css?v=20260203',   // ✅ Mit Query-Parameter
  '/static/pdf.js?v=20260203',    // ✅ Mit Query-Parameter
  '/static/temu.css?v=20260203',  // ✅ Mit Query-Parameter
  '/static/temu.js?v=20260203'    // ✅ Mit Query-Parameter
];

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // ✅ ALL API calls: Network Only (NEVER cache)
  if (url.pathname.startsWith('/api/')) {
    return; // Let browser handle API calls normally
  }

  // HTML/CSS/JS: Stale-while-revalidate
  event.respondWith(
    caches.match(request).then((cached) => {
      const fetchPromise = fetch(request).then((resp) => {
        const respClone = resp.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, respClone));
        return resp;
      });
      return cached || fetchPromise;
    }).catch(() => caches.match('/'))
  );
});
```

**Änderungen:**
1. **Cache-Version erhöht**: `v2026020316` → `v2026020318` erzwingt Cache-Invalidierung
2. **Query-Parameter in ASSETS**: URLs matchen jetzt mit HTML `<script>`/`<link>` Tags
3. **API-Calls explizit ausgeschlossen**: `if (url.pathname.startsWith('/api/'))` verhindert Caching

### Fix 3: Frontend HTML – Query-Parameter

**Datei: `modules/pdf_reader/frontend/pdf.html`**

```html
<link rel="stylesheet" href="/static/pdf.css?v=20260203">
<script src="/static/pdf.js?v=20260203"></script>
```

**Datei: `modules/temu/frontend/temu.html`**

```html
<link rel="stylesheet" href="/static/temu.css?v=20260203">
<script src="/static/temu.js?v=20260203"></script>
```

**Änderung:**
- Query-Parameter `?v=20260203` für Cache-Busting
- Bei Code-Änderungen: Version inkrementieren → Browser lädt neue Datei

**Automatisierung:**
```bash
# Beispiel für zukünftige Updates
VERSION=$(date +%Y%m%d)
sed -i "s|/static/pdf.css?v=[0-9]*|/static/pdf.css?v=$VERSION|g" modules/pdf_reader/frontend/pdf.html
sed -i "s|/static/pdf.js?v=[0-9]*|/static/pdf.js?v=$VERSION|g" modules/pdf_reader/frontend/pdf.html
```

### Fix 4: Browser Cache – Chrome Restart

**Lösung:** Chrome komplett neu starten (nicht nur Tab schließen)

**Alternative:** Incognito Mode für Tests nutzen

**Debug-Tools:**
```
Chrome DevTools → Application Tab
- Service Workers → Unregister
- Storage → Clear Site Data
- Cache Storage → Delete all caches
```

---

## Frontend Cleanup

### Gelöschte Dateien

Im Rahmen des Fixes wurden veraltete Dateien aus `/frontend/` entfernt:

```bash
rm frontend/index.html         # Alte Dashboard-Version (index-new.html aktiv)
rm frontend/index.html.bak     # Backup (41KB)
rm frontend/temu.html          # Duplikat (existiert in modules/temu/frontend/)
rm frontend/app.js             # Nur von alter temu.html verwendet (22KB)
rm frontend/navbar.js          # Nur von alten Dateien verwendet
rm frontend/styles.css         # Nur von alten Dateien verwendet (11KB)
rm frontend/clear-cache.html   # Debug-Tool (nicht mehr benötigt)
```

**Grund:**
- `main.py:301` lädt `index-new.html` wenn vorhanden, sonst `index.html`
- `main.py:327` lädt TEMU UI aus `modules/temu/frontend/temu.html`
- Alte Dateien verwiesen auf `/pdf-reader.html` (existiert nicht mehr)

### Finale Struktur

```
frontend/
├── dashboard.css          # CSS für Root Dashboard
├── icons/                 # PWA Icons
├── index-new.html         # Root Dashboard (aktiv)
├── manifest.json          # PWA Manifest
└── service-worker.js      # Service Worker v2026020318
```

**Monorepo-Struktur:**
```
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

## Best Practices für zukünftige Entwicklungen

### 1. Cache-Busting bei Frontend-Änderungen

**Bei jeder Änderung an CSS/JS:**

```bash
# 1. Version in HTML aktualisieren
VERSION=$(date +%Y%m%d)
sed -i "s|/static/pdf.css?v=[0-9]*|/static/pdf.css?v=$VERSION|g" modules/pdf_reader/frontend/pdf.html
sed -i "s|/static/pdf.js?v=[0-9]*|/static/pdf.js?v=$VERSION|g" modules/pdf_reader/frontend/pdf.html

# 2. Service Worker Cache-Version erhöhen
sed -i "s|const CACHE_NAME = 'toci-tools-cache-v[0-9]*'|const CACHE_NAME = 'toci-tools-cache-v$VERSION'|" frontend/service-worker.js

# 3. ASSETS im Service Worker aktualisieren (manuell prüfen!)
# → Sicherstellen, dass Query-Parameter mit HTML übereinstimmen
```

### 2. Caddy Konfiguration – Matcher-Regeln

**Wichtig:** Bei Caddy-Matchers ist die Reihenfolge wichtig!

```caddy
# ✅ RICHTIG: Explizite Ausnahme mit negativem Matcher
@api { path /api/* }
header @api Cache-Control "no-cache"

@notapi { not path /api/* }
header @notapi Cache-Control "public, max-age=3600"

# ❌ FALSCH: Default-Regel überschreibt alles
header Cache-Control "public, max-age=3600"  # Gilt für ALLES!
@api { path /api/* }
header @api Cache-Control "no-cache"        # Wird ignoriert
```

### 3. API-Responses niemals cachen

**Regel:** Alle `/api/*` Endpoints MÜSSEN folgende Header setzen:

```python
# In FastAPI (automatisch durch Caddy)
# Aber bei direktem Zugriff ohne Caddy:
@app.get("/api/pdf/status")
async def status():
    response = JSONResponse({"status": "ok"})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
```

**Besser:** Middleware in FastAPI:

```python
@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response
```

### 4. Service Worker Testing

**Nach Service Worker Änderungen:**

1. **Hard Reload erzwingen:**
   ```
   Chrome DevTools → Application → Service Workers
   → Check "Update on reload"
   → Dann: Cmd/Ctrl + Shift + R
   ```

2. **Incognito Mode testen:**
   - Garantiert keine Cache-Interferenzen
   - Für Entwicklung immer zuerst testen

3. **Cache-Version bei JEDER Änderung erhöhen:**
   ```javascript
   // ❌ FALSCH: Gleiche Version
   const CACHE_NAME = 'toci-tools-cache-v1';

   // ✅ RICHTIG: Datums-basierte Version
   const CACHE_NAME = 'toci-tools-cache-v20260203';
   ```

### 5. Debugging Multi-Layer-Caching

**Schritt-für-Schritt Diagnose:**

```bash
# 1. Prüfe Caddy Headers
curl -I https://192.168.178.4/api/pdf/status
# Erwartung: Cache-Control: no-cache

# 2. Prüfe Service Worker Status
# Chrome DevTools → Application → Service Workers
# → Zeigt aktive Version und Cache-Einträge

# 3. Prüfe Browser Cache
# Chrome DevTools → Network Tab
# → "Disable cache" aktivieren
# → Dann: Hard Reload (Cmd+Shift+R)

# 4. Prüfe direkt ohne Proxy
curl http://localhost:8000/api/pdf/status
# Sollte gleiche Daten wie über Caddy zeigen
```

**Häufige Symptome:**
- **"Funktioniert auf :8000 aber nicht über Caddy"** → Caddy cached
- **"Incognito funktioniert, normaler Browser nicht"** → Browser Cache Problem
- **"Hard Reload hilft nicht"** → Service Worker cached noch

### 6. PM2 Deployment nach Frontend-Änderungen

**Nach Frontend-Änderungen KEIN PM2-Restart nötig:**
```bash
# Frontend-Dateien werden direkt von FastAPI serviert
# Änderungen sind sofort sichtbar (nach Cache-Bust)
```

**Nur bei Backend-Änderungen:**
```bash
pm2 restart temu-api
```

---

## Zusammenfassung

### Geänderte Dateien

| Datei | Änderung | Grund |
|-------|----------|-------|
| `/etc/caddy/Caddyfile` | `@api` no-cache, `@notapi` Matcher | API-Caching verhindern |
| `frontend/service-worker.js` | Cache v2026020318, Query-Parameter | Cache-Invalidierung |
| `modules/pdf_reader/frontend/pdf.html` | `?v=20260203` Query-Parameter | Cache-Busting |
| `modules/temu/frontend/temu.html` | `?v=20260203` Query-Parameter | Cache-Busting |

### Gelöschte Dateien (Frontend Cleanup)

- `frontend/index.html`, `frontend/index.html.bak`
- `frontend/temu.html`, `frontend/app.js`, `frontend/navbar.js`, `frontend/styles.css`
- `frontend/clear-cache.html`

**Grund:** Duplikate und veraltete Dateien nach Monorepo-Migration

### Testing

**Erfolgreich getestet:**
1. ✅ `/api/pdf/status` wird nicht gecacht (Header: `no-cache`)
2. ✅ Logs werden live aktualisiert ohne Hard-Refresh
3. ✅ Service Worker lädt korrekte JavaScript-Version
4. ✅ Funktioniert über Caddy Proxy (https://192.168.178.4)
5. ✅ Frontend-Struktur aufgeräumt (nur notwendige Dateien)

### Wichtige Erkenntnisse

1. **Multi-Layer-Caching ist komplex:** Caddy, Service Worker UND Browser müssen korrekt konfiguriert sein
2. **Query-Parameter für Cache-Busting:** `?v=20260203` muss in HTML UND Service Worker ASSETS übereinstimmen
3. **Caddy Matcher-Reihenfolge:** Negative Matcher (`not path`) nötig, um Default-Regeln zu überschreiben
4. **Browser Cache persistent:** Selbst nach Caddy-Fix kann Browser-Cache alte Daten zeigen → Chrome-Restart hilft
5. **Incognito Mode für Debug:** Beste Methode, um Cache-Probleme zu isolieren

---

**Datum:** 3. Februar 2026
**Betroffen:** PDF Reader Frontend, TEMU Frontend, Caddy Reverse Proxy
**Priority:** Critical (Frontend nicht benutzbar über Proxy)
**Status:** ✅ Vollständig behoben
