# 🚀 SESSION HANDOVER: React Migration Team
**Datum:** 15. Februar 2026 → 16. Februar 2026
**Status:** Team-Setup vorbereitet, bereit für Umsetzung
**Zweck:** Persistentes Team-Setup für React-Migration über mehrere Tage

---

## 📋 PROJEKT-KONTEXT

### Vision
Kompletter Umbau des **TEMU ERP Systems** zu einem modernen Multi-Channel OMS/WMS:
- **Ziel:** JTL-Wawi ersetzen
- **Aktuelle Kanäle:** TEMU (live), PDF Reader, CSV Processor
- **Zukünftige Kanäle:** eBay, Kaufland, Otto, Amazon

### Migration
- **Von:** FastAPI + Vanilla JS + master.css
- **Zu:** FastAPI + React 19 + TypeScript + Tailwind + shadcn/ui

---

## 🎯 ENTSCHEIDUNGEN (15. Feb 2026)

### Tech-Stack Frontend
✅ **Framework:** React 19 + TypeScript
✅ **Build Tool:** Vite (statt Create React App)
✅ **UI Components:** shadcn/ui (Radix UI + Tailwind)
✅ **Styling:** Tailwind CSS
✅ **State Management:**
   - TanStack Query (Server State)
   - Zustand (Client State)
✅ **Forms:** React Hook Form
✅ **Routing:** TanStack Router oder React Router v6
✅ **Icons:** lucide-react

### Tech-Stack Backend
✅ **Framework:** FastAPI (BLEIBT!)
✅ **Server:** uvicorn + PM2
✅ **Datenbank:** MSSQL
✅ **Validierung:** Pydantic V2

### Projekt-Struktur
✅ **Monorepo:** `/frontend-react/` neben `/modules/`
✅ **Auslagerbar:** So strukturiert, dass spätere Trennung möglich ist

### Ports
✅ **FastAPI Dev:** 8888 (bleibt)
✅ **FastAPI Prod:** 8000 (bleibt)
✅ **React Dev:** 3000 (aus Login-Modul übernommen)

### Prioritäten
1. **Phase A (JETZT):** React-Frontend aufsetzen + erste Module portieren
2. **Phase B (Falls nötig):** Backend API modernisieren
3. **Phase C (Später):** Datenbank-Schema für neues OMS/WMS

### Auth
⏸️ **JWT-Auth:** Erst nach React-Migration

### Multi-Channel
📅 **Reihenfolge:** eBay → Kaufland → Otto → Amazon (ganz am Ende)

---

## 🗂️ REFERENZ-PROJEKT: Login-Modul

**Pfad:** `~/code_test/frontend/`

### Struktur
```
~/code_test/frontend/src/
├── components/
│   ├── LoginPage.tsx          # Login-Komponente
│   ├── LoginPage.css          # Login-Styles
│   └── DashboardPage.tsx      # Dashboard nach Login
├── services/
│   └── authService.ts         # Auth-Logik (JWT?)
├── types/
│   └── auth.ts                # TypeScript Interfaces
├── App.tsx                    # Main App
└── index.tsx                  # Entry Point
```

### Tech-Stack (Referenz)
- React 19.2.4
- React Router v6
- TypeScript 4.9.5
- Create React App (react-scripts)
- Port 3000

**💡 Wichtig:** Wir nutzen **Vite** statt CRA (moderner, schneller)

---

## 📐 GEPLANTE STRUKTUR: Frontend-React

```
/home/chx/entwicklung/
├── modules/                      # Backend (bleibt)
├── frontend/                     # Altes Vanilla JS Frontend (bleibt erstmal)
├── frontend-react/              # NEUES React Frontend ⭐
│   ├── public/
│   │   └── icons/               # PWA Icons
│   ├── src/
│   │   ├── app/                 # App Shell & Routing
│   │   │   ├── App.tsx
│   │   │   ├── router.tsx
│   │   │   └── layout/          # Sidebar, Header
│   │   ├── features/            # Feature-Module
│   │   │   ├── dashboard/       # Dashboard ⭐ START HIER
│   │   │   ├── temu/            # TEMU Orders & Inventory
│   │   │   ├── pdf-reader/      # PDF Processing
│   │   │   ├── csv-processor/   # CSV Processing
│   │   │   └── auth/            # Auth (später)
│   │   ├── shared/              # Shared Code
│   │   │   ├── components/
│   │   │   │   ├── ui/          # shadcn/ui components
│   │   │   │   ├── layout/      # Layout Components
│   │   │   │   └── common/      # Common Components
│   │   │   ├── hooks/           # Custom Hooks
│   │   │   ├── lib/             # Utils & API Client
│   │   │   │   ├── api.ts       # Axios/Fetch
│   │   │   │   └── utils.ts     # Helpers
│   │   │   └── types/           # Global Types
│   │   ├── styles/
│   │   │   └── globals.css      # Tailwind + Theme
│   │   └── main.tsx             # Entry Point
│   ├── .env                     # React Env Vars
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── components.json          # shadcn/ui config
├── docs/
│   └── FRONTEND/
│       └── REACT_MIGRATION.md   # Migration-Tracking
├── AI_GUIDE.md                  # Haupt-Guide (aktualisieren!)
└── SESSION_HANDOVER.md          # Diese Datei
```

---

## 👥 TEAM-STRUKTUR: "React Migration Team"

### Team Lead: Claude Sonnet (Du - der Human orchestriert)

### Agent 1: Frontend Architecture Agent
**Name:** `frontend-architect`
**Typ:** `general-purpose`
**Modell:** `opus` oder `sonnet` (Architektur ist kritisch!)
**Aufgaben:**
- Vite + React + TypeScript Setup
- shadcn/ui Installation & Konfiguration
- Tailwind CSS Theme (Apple-Style)
- Design System (Colors, Typography, Spacing)
- App Shell (Layout, Sidebar, Navigation)
- Shared Components (Button, Card, Dialog, Table)

### Agent 2: Feature Migration Agent
**Name:** `feature-migrator`
**Typ:** `general-purpose`
**Modell:** `sonnet` (Standard-Entwicklung)
**Aufgaben:**
- Vanilla JS → React konvertieren
- TypeScript Interfaces erstellen
- State Management (TanStack Query + Zustand)
- API Integration
- Module-Reihenfolge:
  1. Dashboard (einfach)
  2. TEMU Orders (komplex)
  3. TEMU Inventory (mittel)
  4. PDF Reader (mittel)
  5. CSV Processor (einfach)

### Agent 3: Backend API Agent
**Name:** `backend-api`
**Typ:** `general-purpose`
**Modell:** `haiku` oder `sonnet` (meist einfache Config)
**Aufgaben:**
- CORS für React konfigurieren (Port 3000)
- Pydantic Schemas überprüfen
- Response-Format vereinheitlichen
- API-Dokumentation aktualisieren
- FastAPI-Readiness checken

### Agent 4: Documentation Agent
**Name:** `doc-keeper`
**Typ:** `general-purpose`
**Modell:** `haiku` (Dokumentation ist straightforward)
**Aufgaben:**
- `docs/FRONTEND/REACT_MIGRATION.md` erstellen & pflegen
- `AI_GUIDE.md` aktualisieren
- Migration-Tracking
- API-Änderungen dokumentieren
- Component-Library dokumentieren

---

## 🚀 MIGRATIONS-PLAN: Phase A

### Sprint 1: Foundation (Tag 1-2)
- [ ] Vite Projekt erstellen (`frontend-react/`)
- [ ] shadcn/ui installieren
- [ ] Tailwind CSS konfigurieren (Apple-Style Theme)
- [ ] Design System definieren
- [ ] App Shell erstellen (Layout + Sidebar)
- [ ] API Client Setup (axios + TanStack Query)

### Sprint 2: Shared Components (Tag 2-3)
- [ ] shadcn/ui Components: Button, Card, Input, Select, Dialog
- [ ] Table Component (für Orders, Inventory)
- [ ] Loading States (Skeleton, Spinner)
- [ ] Toast/Notifications
- [ ] Error Boundaries

### Sprint 3: Dashboard Migration (Tag 3-4)
- [ ] Dashboard Page Layout
- [ ] Stats Cards (Orders, Inventory, Jobs)
- [ ] Quick Actions
- [ ] API Integration (Stats-Endpoint)

### Sprint 4: TEMU Module (Tag 4-7)
- [ ] TEMU Orders Page
  - [ ] Orders Table (TanStack Table)
  - [ ] Filter & Search
  - [ ] Order Details Dialog
  - [ ] Sync Dialog
- [ ] TEMU Inventory Page
  - [ ] Inventory Table
  - [ ] Sync Dialog
  - [ ] Status Display

### Sprint 5: PDF & CSV Module (Tag 7-10)
- [ ] PDF Reader Page (Upload, Processing, Results)
- [ ] CSV Processor Page (Upload, Validation, Download)

---

## 🎨 DESIGN SYSTEM: Apple-Style

### Colors (Tailwind Config)
```js
colors: {
  primary: '#007AFF',      // Apple Blue
  secondary: '#636366',    // Gray
  success: '#34C759',      // Green
  warning: '#FF9500',      // Orange
  danger: '#FF3B30',       // Red
  background: '#FFFFFF',   // White
  surface: '#F5F5F7',      // Light Gray
  text: {
    primary: '#000000',
    secondary: '#636366',
    tertiary: '#8E8E93',
  }
}
```

### Typography
- **Font:** SF Pro (Fallback: -apple-system, BlinkMacSystemFont, 'Segoe UI')
- **Sizes:** text-sm, text-base, text-lg, text-xl, text-2xl
- **Weights:** font-normal (400), font-medium (500), font-semibold (600)

### Spacing
- **Consistent:** 4px Grid (p-1, p-2, p-4, p-6, p-8)
- **Radius:** rounded-lg (8px), rounded-xl (12px)
- **Shadows:** shadow-sm, shadow-md, shadow-lg

---

## 📚 WICHTIGE DOKUMENTE

### Bereits vorhanden:
- [AI_GUIDE.md](AI_GUIDE.md) - Haupt-Guide für AI-Agenten
- [docs/VISION_2026.md](docs/VISION_2026.md) - Strategischer Fahrplan
- [docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md) - Aktueller Projektstatus
- [docs/README.md](docs/README.md) - Dokumentations-Index

### Neu erstellen:
- [ ] `docs/FRONTEND/REACT_MIGRATION.md` - Migration-Tracking
- [ ] `frontend-react/README.md` - Frontend-Dokumentation
- [ ] `frontend-react/.env.example` - Environment Variables

---

## 🔧 TECHNISCHE DETAILS

### CORS Setup (Backend)
```python
# main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React Dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Environment Variables (React)
```bash
# frontend-react/.env
VITE_API_URL=http://localhost:8888
VITE_WS_URL=ws://localhost:8888/ws
```

### Package.json Scripts
```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  }
}
```

---

## 📝 NÄCHSTE SCHRITTE (Morgen, 16. Feb 2026)

### 0. ZUERST: Bestehende Agenten lesen! 🔍
```bash
# Im Claude Code Chat:
"Lies alle Agent-Definitionen in .ai_ops/agenten/ und .ai_ops/skills/
Verstehe meine Patterns, Prioritäten und Arbeitsweise.
Dann optimiere die Team-Struktur und update das SESSION_HANDOVER.md"
```

**Wichtig:** Besonders diese Dateien lesen:
- `.ai_ops/agenten/ag_03_Backend_Refactoring-old.md` (26KB!)
- `.ai_ops/agenten/ag_04_FrontendRefactoring-old.md` (7KB)
- `.ai_ops/skills/skill_changeDoc.md`
- `.ai_ops/skills/skill_logging.md`

### 1. Team erstellen (NACH dem Lesen!)
```bash
# Im Claude Code Chat:
"Erstelle jetzt das optimierte React Migration Team mit den richtigen Modell-Zuweisungen"
```

### 2. Sprint 1 starten
```bash
# frontend-architect startet:
"Erstelle das Vite + React + TypeScript Projekt im Ordner frontend-react/
Installiere shadcn/ui und konfiguriere Tailwind mit Apple-Style Theme"
```

### 3. Parallel: Backend vorbereiten
```bash
# backend-api agent:
"Füge CORS-Middleware für Port 3000 hinzu und teste die API-Readiness"
```

### 4. Dokumentation starten
```bash
# doc-keeper agent:
"Erstelle docs/FRONTEND/REACT_MIGRATION.md und beginne Migration-Tracking"
```

---

## 🎯 SUCCESS CRITERIA (Woche 1)

- ✅ Vite Projekt läuft auf Port 3000
- ✅ shadcn/ui Components funktionieren
- ✅ Tailwind Theme (Apple-Style) implementiert
- ✅ App Shell mit Sidebar funktional
- ✅ API Client mit TanStack Query funktioniert
- ✅ Dashboard-Page deployed (erste Migration abgeschlossen)

---

## 💾 MEMORY & PERSISTENCE

### Team wird persistent gespeichert in:
```
~/.claude/teams/react-migration-team/
├── config.json          # Team-Konfiguration
└── members/             # Agent-Definitionen
```

### Task List wird gespeichert in:
```
~/.claude/tasks/react-migration-team/
└── tasks.json          # Alle Tasks & Status
```

### Dieses Dokument als Single Source of Truth:
- Immer aktualisieren bei Entscheidungen
- Datum bei Updates anpassen
- Als "Memory" für alle Agents nutzen

---

## 🔗 QUICK LINKS

- **Aktuelles Projekt:** `/home/chx/entwicklung/`
- **Login-Referenz:** `~/code_test/frontend/`
- **Dokumentation:** `docs/`
- **FastAPI Dev:** http://localhost:8888/docs
- **React Dev (zukünftig):** http://localhost:3000

---

**Status:** ⏸️ Warten auf Optimierung nach Lesen der bestehenden Agenten
**Nächster Schritt:**
1. Bestehende Agent-Definitionen lesen (.ai_ops/agenten/ & skills/)
2. Team-Struktur optimieren (Modelle, Patterns)
3. SESSION_HANDOVER.md updaten
4. Team erstellen mit optimierten Einstellungen
**Letzte Aktualisierung:** 15. Februar 2026, 23:58 Uhr

---

## 🌙 GUTE NACHT & BIS MORGEN!

Alles vorbereitet für einen produktiven Start morgen.
Die Team-Struktur steht, der Plan ist klar, die Dokumentation ist da.

**Morgen einfach sagen:**
_"Lies das SESSION_HANDOVER.md und lass uns das React Migration Team starten!"_

Schlaf gut! 💤
