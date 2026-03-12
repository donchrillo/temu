---
name: frontend-migration-workflow
description: Systematischer Prozess für Migration von Vanilla JS zu React 19 mit TypeScript.
---

# ⚛️ Frontend Migration Workflow (Vanilla → React)

## 🎯 Migration-Philosophie

**Von:** Vanilla JS + DOM Manipulation  
**Nach:** React 19 + TypeScript + Functional Components

**Ziel:** Moderne, wartbare, typsichere Single Page Application

---

## 📋 Migration Workflow (4 Phasen)

### Phase 1: Analyse (Discovery)

**Input:** Legacy Vanilla JS/HTML/CSS  
**Output:** Migration Plan mit Komponenten-Hierarchie

#### Schritt 1: Komponenten identifizieren
```javascript
// Vanilla JS Pattern erkennen:
// - Welche Funktionen manipulieren DOM?
// - Welche Daten werden gerendert?
// - Welche Events werden behandelt?

// Example: temu.js
function loadLogs() { ... }      // → LogsComponent
function renderLogs(logs) { ... } // → LogsList Component
function createLogElement(log) { ... } // → LogItem Component
```

#### Schritt 2: State-Management mapping
```javascript
// Vanilla: Global Variables oder Closures
let currentLogs = [];
let isLoading = false;

// React Mapping:
// → useState<Log[]>([])
// → useState<boolean>(false)
```

#### Schritt 3: API-Calls identifizieren
```javascript
// Vanilla: fetch() Calls
function fetchLogs() {
    return fetch('/api/logs').then(r => r.json());
}

// React Mapping:
// → useEffect() mit fetch
// → Custom Hook: useLogs()
```

#### Schritt 4: Event-Handler mapping
```javascript
// Vanilla: addEventListener
button.addEventListener('click', handleClick);

// React Mapping:
// → <button onClick={handleClick}>
```

**Analyse-Template:**
```
## Migration Analysis: temu.js

### Komponenten-Kandidaten:
- LogsComponent (Container)
  - LogsList (List)
    - LogItem (Item)
  - LoadingSpinner
  - ErrorMessage

### State:
- logs: Log[]
- loading: boolean
- error: string | null

### API-Calls:
- GET /api/logs → useLogs() Hook

### Events:
- Filter ändern → onFilterChange
- Refresh → onRefresh
```

---

### Phase 2: Planung (Design)

#### Schritt 1: TypeScript Interfaces definieren

```typescript
// interfaces/Log.ts
export interface Log {
    id: number;
    timestamp: string;
    message: string;
    level: 'info' | 'warning' | 'error';
    job_id: string;
}

export interface LogsFilter {
    level?: 'info' | 'warning' | 'error';
    search?: string;
    dateFrom?: string;
    dateTo?: string;
}
```

#### Schritt 2: Komponenten-Hierarchie skizzieren

```
LogsPage (Container)
├── LogsFilter (Form)
│   ├── LevelSelect
│   ├── SearchInput
│   └── DateRangePicker
├── LogsList (List)
│   └── LogItem (Item) [repeated]
├── LoadingSpinner
└── ErrorMessage
```

#### Schritt 3: Props-Interfaces

```typescript
// components/LogsList.tsx
interface LogsListProps {
    logs: Log[];
    onRefresh: () => void;
}

// components/LogItem.tsx
interface LogItemProps {
    log: Log;
    onClick?: (log: Log) => void;
}

// components/LogsFilter.tsx
interface LogsFilterProps {
    filter: LogsFilter;
    onFilterChange: (filter: LogsFilter) => void;
}
```

#### Schritt 4: State-Management entscheiden

**Optionen:**
1. **useState:** Für lokalen Component-State
2. **useContext:** Für shared State (z.B. Auth)
3. **Redux/Zustand:** Für komplexe globale State (optional)

**Empfehlung für TEMU ERP:**
- `useState` + `useContext` für Auth
- Kein Redux (zu komplex für unsere Needs)

---

### Phase 3: Migration (Implementation)

#### Schritt 1: TypeScript Interfaces erstellen

```typescript
// src/types/log.ts
export interface Log {
    id: number;
    timestamp: string;
    message: string;
    level: 'info' | 'warning' | 'error';
    job_id: string;
}
```

#### Schritt 2: Custom Hooks für API-Calls

```typescript
// src/hooks/useLogs.ts
import { useState, useEffect } from 'react';
import { Log } from '../types/log';

interface UseLogsResult {
    logs: Log[];
    loading: boolean;
    error: string | null;
    refresh: () => void;
}

export function useLogs(apiBaseUrl: string): UseLogsResult {
    const [logs, setLogs] = useState<Log[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [refreshKey, setRefreshKey] = useState(0);

    useEffect(() => {
        async function fetchLogs() {
            setLoading(true);
            setError(null);
            
            try {
                const response = await fetch(`${apiBaseUrl}/api/logs`, {
                    credentials: 'include'
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                setLogs(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Unknown error');
            } finally {
                setLoading(false);
            }
        }
        
        fetchLogs();
    }, [apiBaseUrl, refreshKey]);

    const refresh = () => setRefreshKey(prev => prev + 1);

    return { logs, loading, error, refresh };
}
```

#### Schritt 3: Atom-Komponenten erstellen

```typescript
// src/components/LogItem.tsx
import React from 'react';
import { Log } from '../types/log';

interface LogItemProps {
    log: Log;
}

export function LogItem({ log }: LogItemProps) {
    return (
        <div className={`log-entry log-${log.level}`}>
            <span className="log-time">{log.timestamp}</span>
            <span className="log-level">{log.level.toUpperCase()}</span>
            <span className="log-message">{log.message}</span>
        </div>
    );
}
```

#### Schritt 4: Listen-Komponenten erstellen

```typescript
// src/components/LogsList.tsx
import React from 'react';
import { Log } from '../types/log';
import { LogItem } from './LogItem';

interface LogsListProps {
    logs: Log[];
}

export function LogsList({ logs }: LogsListProps) {
    if (logs.length === 0) {
        return (
            <div className="empty-state">
                Keine Logs verfügbar
            </div>
        );
    }

    return (
        <div className="logs-list">
            {logs.map(log => (
                <LogItem key={log.id} log={log} />
            ))}
        </div>
    );
}
```

#### Schritt 5: Container-Komponente erstellen

```typescript
// src/pages/LogsPage.tsx
import React from 'react';
import { useLogs } from '../hooks/useLogs';
import { LogsList } from '../components/LogsList';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';

const API_BASE_URL = `${window.location.protocol}//${window.location.host}`;

export function LogsPage() {
    const { logs, loading, error, refresh } = useLogs(API_BASE_URL);

    if (loading) {
        return <LoadingSpinner />;
    }

    if (error) {
        return (
            <ErrorMessage 
                message={error} 
                onRetry={refresh} 
            />
        );
    }

    return (
        <div className="logs-page">
            <header className="page-header">
                <h1>Logs</h1>
                <button onClick={refresh}>
                    Refresh
                </button>
            </header>
            
            <LogsList logs={logs} />
        </div>
    );
}
```

---

### Phase 4: Integration & Testing

#### Schritt 1: Routing integrieren

```typescript
// src/App.tsx
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { LogsPage } from './pages/LogsPage';
import { OrdersPage } from './pages/OrdersPage';

export function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/logs" element={<LogsPage />} />
                <Route path="/orders" element={<OrdersPage />} />
            </Routes>
        </BrowserRouter>
    );
}
```

#### Schritt 2: Schrittweise ersetzen

**Option A: Parallel Run (Empfohlen)**
```html
<!-- Beide Versionen laufen parallel -->
<div id="vanilla-logs" style="display:none">
    <!-- Legacy Vanilla JS -->
</div>

<div id="react-logs">
    <!-- Neue React App -->
</div>
```

**Option B: Feature-Flag**
```typescript
const USE_REACT = localStorage.getItem('use-react') === 'true';

if (USE_REACT) {
    ReactDOM.render(<LogsPage />, document.getElementById('root'));
} else {
    // Legacy Vanilla JS
    loadLogs();
}
```

#### Schritt 3: Testing

**Unit Tests (Vitest/Jest):**
```typescript
// src/hooks/useLogs.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useLogs } from './useLogs';

describe('useLogs', () => {
    it('fetches logs successfully', async () => {
        const { result } = renderHook(() => useLogs('http://localhost:8000'));
        
        expect(result.current.loading).toBe(true);
        
        await waitFor(() => {
            expect(result.current.loading).toBe(false);
            expect(result.current.logs.length).toBeGreaterThan(0);
        });
    });
});
```

**Integration Tests (Playwright):**
```typescript
// tests/logs.spec.ts
import { test, expect } from '@playwright/test';

test('displays logs', async ({ page }) => {
    await page.goto('http://localhost:3000/logs');
    
    // Wait for logs to load
    await page.waitForSelector('.log-entry');
    
    // Check if logs are displayed
    const logItems = await page.locator('.log-entry').count();
    expect(logItems).toBeGreaterThan(0);
});
```

---

## 🎯 React-Spezifische Patterns

### 1. Conditional Rendering

```typescript
// ✅ GOOD: Early Returns
export function LogsPage() {
    const { logs, loading, error } = useLogs();

    if (loading) return <LoadingSpinner />;
    if (error) return <ErrorMessage message={error} />;
    if (logs.length === 0) return <EmptyState />;

    return <LogsList logs={logs} />;
}
```

### 2. Props Destructuring

```typescript
// ✅ GOOD: Destructure Props
interface LogItemProps {
    log: Log;
    onClick?: (log: Log) => void;
}

export function LogItem({ log, onClick }: LogItemProps) {
    return (
        <div onClick={() => onClick?.(log)}>
            {log.message}
        </div>
    );
}
```

### 3. Custom Hooks für Wiederverwendbare Logic

```typescript
// ✅ GOOD: Extract Common Logic
function useApi<T>(url: string) {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = async () => {
        setLoading(true);
        try {
            const response = await fetch(url, { credentials: 'include' });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            setData(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [url]);

    return { data, loading, error, refetch: fetchData };
}

// Usage
function OrdersPage() {
    const { data: orders, loading, error } = useApi<Order[]>('/api/orders');
    // ...
}
```

### 4. Memo für Performance

```typescript
// ✅ GOOD: Memo für teure Komponenten
export const LogItem = React.memo(function LogItem({ log }: LogItemProps) {
    return (
        <div className="log-entry">
            {log.message}
        </div>
    );
});

// Nur re-rendern wenn log sich ändert
```

---

## 🔐 React Security Patterns

### 1. XSS-Prevention (automatisch)

```typescript
// ✅ React escaped automatisch
export function LogItem({ log }: LogItemProps) {
    return <div>{log.message}</div>; // ✅ Safe: Auto-escaped
}

// ⚠️ Dangerous nur wenn nötig + sanitized
import DOMPurify from 'dompurify';

export function HtmlContent({ html }: { html: string }) {
    return (
        <div 
            dangerouslySetInnerHTML={{ 
                __html: DOMPurify.sanitize(html) 
            }} 
        />
    );
}
```

### 2. CSRF mit Credentials

```typescript
// ✅ GOOD: credentials: 'include'
async function createOrder(orderData: OrderCreate) {
    const response = await fetch('/api/orders', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include', // ✅ Include HttpOnly cookies
        body: JSON.stringify(orderData)
    });
    
    return response.json();
}
```

---

## 📦 Project Structure

```
src/
├── components/          # Reusable UI Components
│   ├── LogItem.tsx
│   ├── LogsList.tsx
│   ├── LoadingSpinner.tsx
│   └── ErrorMessage.tsx
├── hooks/              # Custom Hooks
│   ├── useLogs.ts
│   ├── useOrders.ts
│   └── useAuth.ts
├── pages/              # Page Components
│   ├── LogsPage.tsx
│   ├── OrdersPage.tsx
│   └── DashboardPage.tsx
├── types/              # TypeScript Interfaces
│   ├── log.ts
│   ├── order.ts
│   └── user.ts
├── utils/              # Helper Functions
│   ├── api.ts
│   ├── format.ts
│   └── validation.ts
└── App.tsx             # Root Component
```

---

## 🚦 Migration Decision Helper

### ✅ Migriere zu React wenn:
- UI wird häufig geändert
- Komplexe State-Management benötigt
- Team hat React-Erfahrung
- Lange Lebenszeit des Features

### ⚠️ Behalte Vanilla JS wenn:
- Sehr simple Komponente (<50 Zeilen)
- Keine State-Changes
- Legacy-Code funktioniert gut
- Keine Zeit für Migration

---

## 💡 Pro-Tipps

1. **Incremental Migration:** Migriere Feature für Feature, nicht alles auf einmal
2. **TypeScript First:** Interfaces vor Komponenten definieren
3. **Custom Hooks:** Wiederverwendbare Logic extrahieren
4. **Memo Sparingly:** Nur für teure Komponenten
5. **Testing:** Unit Tests für Hooks, Integration Tests für Pages
6. **Storybook:** Komponenten isoliert entwickeln und dokumentieren
