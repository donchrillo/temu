---
name: frontend-refactor
description: Frontend Code Smells erkennen und beheben - Vanilla JS, React-Patterns und Security.
---

# 🎨 Frontend Refactoring Patterns

## 🎯 Frontend-Spezifische Code Smells

### 🔴 HIGH IMPACT (Immer fixen)

#### 1. Large Monolithic Functions (>50 Zeilen)
**Symptom:** Eine Funktion macht alles (API Call + Rendering + Error Handling)  
**Fix:** Aufteilen in fokussierte Funktionen

```javascript
// ❌ BEFORE: Monolithische loadLogs() (80 Zeilen)
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

// ✅ AFTER: Modular aufgeteilt
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
    container.innerHTML = '';
    
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

**Vorteile:**
- Jede Funktion <20 Zeilen
- Testbar in Isolation
- Wiederverwendbar
- Lesbar

---

#### 2. XSS-Vulnerabilities (innerHTML)
**Symptom:** User-Content direkt in `innerHTML` geschrieben  
**Fix:** Nutze `textContent` oder sanitize Input

```javascript
// ❌ BEFORE: XSS-Vulnerability
function displayUserComment(comment) {
    const div = document.getElementById('comment');
    div.innerHTML = comment; // ⚠️ DANGER: XSS!
}
// User input: "<script>alert('XSS')</script>"

// ✅ AFTER: XSS-safe
function displayUserComment(comment) {
    const div = document.getElementById('comment');
    div.textContent = comment; // ✅ SAFE: Escaped
}

// Oder bei HTML-Struktur: DOMPurify nutzen
import DOMPurify from 'dompurify';

function displayUserComment(comment) {
    const div = document.getElementById('comment');
    div.innerHTML = DOMPurify.sanitize(comment); // ✅ SAFE: Sanitized
}
```

---

#### 3. Magic URLs/Strings
**Symptom:** Hardcoded URLs, API-Endpoints, Konstanten  
**Fix:** Zentrale Config-Objekte

```javascript
// ❌ BEFORE: Magic URLs überall
function fetchOrders() {
    return fetch('http://192.168.178.4:8000/api/orders');
}

function fetchProducts() {
    return fetch('http://192.168.178.4:8000/api/products');
}

// ✅ AFTER: Zentrale Config
const API_CONFIG = {
    BASE_URL: `${window.location.protocol}//${window.location.host}`,
    ENDPOINTS: {
        ORDERS: '/api/orders',
        PRODUCTS: '/api/products',
        LOGS: '/api/logs'
    },
    TIMEOUT: 5000
};

function fetchOrders() {
    return fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ORDERS}`);
}

function fetchProducts() {
    return fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.PRODUCTS}`);
}
```

---

#### 4. Global Variables
**Symptom:** Globale Variablen für State  
**Fix:** Module Pattern oder IIFE

```javascript
// ❌ BEFORE: Global State
var currentUser = null;
var isLoggedIn = false;

function login(user) {
    currentUser = user;
    isLoggedIn = true;
}

// ✅ AFTER: Module Pattern (IIFE)
const AuthModule = (function() {
    let currentUser = null;
    let isLoggedIn = false;
    
    return {
        login(user) {
            currentUser = user;
            isLoggedIn = true;
        },
        logout() {
            currentUser = null;
            isLoggedIn = false;
        },
        getCurrentUser() {
            return currentUser;
        },
        isAuthenticated() {
            return isLoggedIn;
        }
    };
})();

// Usage
AuthModule.login({id: 123, name: 'Max'});
```

---

### 🟡 MEDIUM IMPACT (Nächster Sprint)

#### 1. Callbacks → async/await
**Symptom:** Callback-Hell, schwer zu lesen  
**Fix:** Modern async/await

```javascript
// ❌ BEFORE: Callback Hell
function loadData(callback) {
    fetch('/api/data')
        .then(r => r.json())
        .then(data => {
            processData(data, (processed) => {
                saveData(processed, (result) => {
                    callback(result);
                });
            });
        });
}

// ✅ AFTER: async/await
async function loadData() {
    const response = await fetch('/api/data');
    const data = await response.json();
    const processed = await processData(data);
    const result = await saveData(processed);
    return result;
}
```

---

#### 2. Ineffiziente DOM-Manipulation
**Symptom:** Mehrfaches Reflow/Repaint  
**Fix:** DocumentFragment

```javascript
// ❌ BEFORE: Ineffizient (N Reflows)
function renderItems(items) {
    const container = document.getElementById('items');
    container.innerHTML = '';
    
    items.forEach(item => {
        const div = document.createElement('div');
        div.textContent = item.name;
        container.appendChild(div); // ⚠️ Reflow bei jedem Append!
    });
}

// ✅ AFTER: DocumentFragment (1 Reflow)
function renderItems(items) {
    const container = document.getElementById('items');
    container.innerHTML = '';
    
    const fragment = document.createDocumentFragment();
    items.forEach(item => {
        const div = document.createElement('div');
        div.textContent = item.name;
        fragment.appendChild(div); // ✅ Kein Reflow
    });
    
    container.appendChild(fragment); // ✅ 1x Reflow
}
```

---

#### 3. Fehlende Error-Boundaries
**Symptom:** Unhandled Promise Rejections  
**Fix:** Try-Catch mit User-Feedback

```javascript
// ❌ BEFORE: Keine Error-Handling
async function loadData() {
    const response = await fetch('/api/data');
    const data = await response.json();
    renderData(data);
}

// ✅ AFTER: Proper Error Handling
async function loadData() {
    try {
        const response = await fetch('/api/data');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        renderData(data);
        
    } catch (error) {
        console.error('Failed to load data:', error);
        showErrorMessage('Daten konnten nicht geladen werden');
    }
}

function showErrorMessage(message) {
    const alert = document.createElement('div');
    alert.className = 'error-alert';
    alert.textContent = message;
    document.body.appendChild(alert);
    
    setTimeout(() => alert.remove(), 5000);
}
```

---

### 🔵 LOW IMPACT (Nice-to-Have)

#### 1. querySelector Optimization
**Symptom:** Wiederholte Queries für gleiche Elemente  
**Fix:** Cache DOM-Referenzen

```javascript
// ❌ BEFORE: Repeated Queries
function updateUI() {
    document.getElementById('status').textContent = 'Loading...';
    document.getElementById('status').classList.add('loading');
    
    setTimeout(() => {
        document.getElementById('status').textContent = 'Done';
        document.getElementById('status').classList.remove('loading');
    }, 1000);
}

// ✅ AFTER: Cached Reference
function updateUI() {
    const statusEl = document.getElementById('status'); // ✅ Cache
    statusEl.textContent = 'Loading...';
    statusEl.classList.add('loading');
    
    setTimeout(() => {
        statusEl.textContent = 'Done';
        statusEl.classList.remove('loading');
    }, 1000);
}
```

---

#### 2. Event Delegation
**Symptom:** Event-Listener auf viele Child-Elemente  
**Fix:** Event Delegation auf Parent

```javascript
// ❌ BEFORE: N Event Listeners
function attachListeners() {
    const items = document.querySelectorAll('.item');
    items.forEach(item => {
        item.addEventListener('click', handleClick); // ⚠️ N Listener
    });
}

// ✅ AFTER: Event Delegation (1 Listener)
function attachListeners() {
    const container = document.getElementById('items');
    container.addEventListener('click', (e) => {
        if (e.target.classList.contains('item')) {
            handleClick(e);
        }
    });
}
```

---

## 🔐 Security Patterns

### 1. XSS-Prevention
```javascript
// ✅ BEST PRACTICES
// Option 1: textContent (für Plain Text)
element.textContent = userInput;

// Option 2: DOMPurify (für HTML)
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(userInput);

// Option 3: Template Literals mit Escaping
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
```

### 2. CSRF-Protection
```javascript
// ✅ CSRF-Token bei POST/PUT/DELETE
async function createOrder(orderData) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
    
    const response = await fetch('/api/orders', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken
        },
        credentials: 'include', // Include cookies
        body: JSON.stringify(orderData)
    });
    
    return response.json();
}
```

### 3. Content Security Policy
```html
<!-- ✅ CSP Header in HTML -->
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';">
```

---

## 🎨 CSS Best Practices

### 1. Eliminiere Duplikate
```css
/* ❌ BEFORE: Duplikate */
.button-primary {
    padding: 10px 20px;
    border-radius: 5px;
    font-size: 14px;
}

.button-secondary {
    padding: 10px 20px;
    border-radius: 5px;
    font-size: 14px;
    background: gray;
}

/* ✅ AFTER: DRY */
.button-base {
    padding: 10px 20px;
    border-radius: 5px;
    font-size: 14px;
}

.button-primary {
    composes: button-base;
}

.button-secondary {
    composes: button-base;
    background: gray;
}
```

### 2. CSS Variables
```css
/* ✅ Zentrale Farb-Variablen */
:root {
    --color-primary: #007bff;
    --color-secondary: #6c757d;
    --color-success: #28a745;
    --color-danger: #dc3545;
    --spacing-sm: 8px;
    --spacing-md: 16px;
    --spacing-lg: 24px;
}

.button-primary {
    background-color: var(--color-primary);
    padding: var(--spacing-md);
}
```

### 3. Media Queries konsolidieren
```css
/* ❌ BEFORE: Scattered */
.header { font-size: 24px; }
.sidebar { width: 300px; }

@media (max-width: 768px) {
    .header { font-size: 18px; }
}

@media (max-width: 768px) {
    .sidebar { width: 100%; }
}

/* ✅ AFTER: Consolidated */
.header { font-size: 24px; }
.sidebar { width: 300px; }

@media (max-width: 768px) {
    .header { font-size: 18px; }
    .sidebar { width: 100%; }
}
```

---

## 📱 PWA Patterns

### Service Worker Strategien

```javascript
// service-worker.js

const CACHE_NAME = 'v1';

self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // API → Network-First (Fresh Data prioritize)
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirst(request));
        return;
    }
    
    // Static Assets → Cache-First (Fast Load)
    event.respondWith(cacheFirst(request));
});

async function networkFirst(request) {
    try {
        const response = await fetch(request);
        const cache = await caches.open(CACHE_NAME);
        cache.put(request, response.clone());
        return response;
    } catch (error) {
        // Fallback to cache
        const cached = await caches.match(request);
        return cached || new Response('Offline', { status: 503 });
    }
}

async function cacheFirst(request) {
    const cached = await caches.match(request);
    if (cached) return cached;
    
    try {
        const response = await fetch(request);
        const cache = await caches.open(CACHE_NAME);
        cache.put(request, response.clone());
        return response;
    } catch (error) {
        return new Response('Offline', { status: 503 });
    }
}
```

---

## 📋 Quick Reference Katalog

### Extract Function
**Trigger:** Funktion >50 Zeilen  
**Steps:**
1. Identifiziere logische Blöcke (Fetch, Render, Error)
2. Extrahiere in fokussierte Funktionen
3. Nutze sprechende Namen (`fetchOrders`, `renderOrders`)

### Remove XSS
**Trigger:** `innerHTML` mit User-Input  
**Steps:**
1. Replace `innerHTML` mit `textContent`
2. Oder: DOMPurify.sanitize()
3. Test mit `<script>alert('XSS')</script>`

### Centralize Config
**Trigger:** Hardcoded URLs/Strings  
**Steps:**
1. Create `config.js` oder `API_CONFIG`
2. Move alle URLs/Constants
3. Update alle Referenzen

### Module Pattern
**Trigger:** Globale Variablen  
**Steps:**
1. Wrap in IIFE
2. Expose nur Public API
3. Private via Closure

---

## 💡 Pro-Tipps

1. **Performance:** DocumentFragment für Batch-Rendering
2. **Security:** Immer `textContent` für User-Input
3. **Maintainability:** Config-Objekte für URLs
4. **Modern:** async/await statt Callbacks
5. **Memory:** Event Delegation statt N Listener
6. **PWA:** Network-First für API, Cache-First für Assets
