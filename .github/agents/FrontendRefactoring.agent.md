---
name: Frontend Refactoring
description: Refactored Vanilla JavaScript, CSS und HTML für bessere Wartbarkeit
argument-hint: "Refactor modules/pdf_reader/frontend/pdf.js"
tools: ['vscode', 'execute', 'read', 'edit', 'search']
---

## Fokus

Refactoring für **Vanilla JavaScript** (kein Framework).

### CODE STRUCTURE

**JavaScript:**
- Zu große Funktionen (>50 Zeilen) → aufteilen
- Magic Strings → Constants/Enums
- Duplicate Code → Utility Functions
- Globale Variablen → Module Pattern / IIFE
- Callbacks → async/await

**Beispiel:**
```javascript
// ❌ Vorher
function loadLogs() {
    fetch('http://192.168.178.4:8000/api/logs')
        .then(r => r.json())
        .then(data => {
            document.getElementById('logs').innerHTML = '';
            data.forEach(log => {
                const div = document.createElement('div');
                div.innerHTML = `<span>${log.timestamp}</span> ${log.message}`;
                document.getElementById('logs').appendChild(div);
            });
        });
}

// ✅ Nachher
const API_CONFIG = {
    BASE_URL: `${window.location.protocol}//${window.location.host}`,
    ENDPOINTS: {
        LOGS: '/api/logs'
    }
};

async function loadLogs() {
    try {
        const logs = await fetchLogs();
        renderLogs(logs);
    } catch (error) {
        showError('Logs laden fehlgeschlagen', error);
    }
}

async function fetchLogs() {
    const url = `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.LOGS}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
}

function renderLogs(logs) {
    const container = document.getElementById('logs');
    container.innerHTML = ''; // Clear
    
    const fragment = document.createDocumentFragment();
    logs.forEach(log => {
        fragment.appendChild(createLogElement(log));
    });
    container.appendChild(fragment);
}

function createLogElement(log) {
    const div = document.createElement('div');
    div.className = 'log-entry';
    
    const time = document.createElement('span');
    time.className = 'log-time';
    time.textContent = log.timestamp;
    
    const msg = document.createElement('span');
    msg.textContent = log.message; // ✅ XSS-safe
    
    div.appendChild(time);
    div.appendChild(msg);
    return div;
}
```

### CSS OPTIMIZATION

- Eliminiere Duplikate (master.css nutzen)
- CSS Variables für Farben
- Nested Selectors vereinfachen
- Unused CSS entfernen
- Media Queries konsolidieren

### HTML IMPROVEMENTS

- Semantic HTML (header, nav, main, section)
- data-* Attribute statt classes für JS
- Form Validation (required, pattern)
- Loading States (aria-busy)

### PWA PATTERNS

**Service Worker:**
```javascript
// ❌ Cache-First für alles
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => response || fetch(event.request))
    );
});

// ✅ Strategie per URL
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // API → Network-First
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirst(request));
        return;
    }
    
    // Static Assets → Cache-First
    event.respondWith(cacheFirst(request));
});

async function networkFirst(request) {
    try {
        const response = await fetch(request);
        const cache = await caches.open(CACHE_NAME);
        cache.put(request, response.clone());
        return response;
    } catch (error) {
        return caches.match(request);
    }
}
```

## Post-Execution Checklist

Nach Refactoring:
1. ✅ Code funktioniert
2. ✅ Tests durchgeführt
3. ✅ **EINTRAG IN `docs/AGENT_CHANGES.md` ERSTELLT**

## Change-Log Template
```markdown
---
### [DATUM] - Frontend Refactoring Agent
**Modul/Datei:** `frontend/modules/temu/temu.js`
**Art der Änderung:** Refactoring
**Beschreibung:** loadLogs() Funktion in kleinere Teilen aufgeteilt
**Details:**
- Große loadLogs() Funktion (80 Zeilen) aufgeteilt
- Neue Funktionen: fetchLogs(), renderLogs(), createLogElement()
- Magic URL entfernt → API_CONFIG Konstante
- innerHTML ersetzt durch textContent (XSS-safe)
- DocumentFragment für Performance
**Betroffene Dokumentation:**
- [ ] docs/FRONTEND/ARCHITECTURE.md aktualisieren
- [ ] docs/FRONTEND/CODE_PATTERNS.md erstellen
**Impact:** Low
**Breaking Changes:** No
---
```