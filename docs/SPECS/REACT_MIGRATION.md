# React 19 Migration - Spezifikation

**Projekt:** TEMU ERP / TOCI ERP  
**Ziel:** Migration von Vanilla JS zu React 19 + TypeScript + Vite + Tailwind + shadcn/ui  
**Erstellt:** 19. Februar 2026  
**Version:** 1.3  
**Status:** Phase 1-4 Abgeschlossen

---

## 1. Ziel-Architektur

### Tech Stack
- **Build Tool:** Vite 5.x
- **Framework:** React 19.x
- **Sprache:** TypeScript 5.x
- **Styling:** Tailwind CSS 3.x (Apple-Design)
- **UI-Library:** shadcn/ui (v0.5.x)
- **Routing:** React Router 7.x
- **State Management:** TanStack Query (React Query) v5.x
- **HTTP Client:** axios

### Verzeichnisstruktur
```
frontend-react/
├── src/
│   ├── components/
│   │   ├── ui/              # shadcn/ui Komponenten
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── input.tsx
│   │   │   ├── select.tsx
│   │   │   ├── table.tsx
│   │   │   └── ...
│   │   ├── layout/          # Layout-Komponenten
│   │   │   ├── app-shell.tsx
│   │   │   ├── sidebar.tsx
│   │   │   ├── header.tsx
│   │   │   └── navigation.tsx
│   │   └── shared/          # Custom Komponenten
│   │       ├── loading-spinner.tsx
│   │       ├── error-boundary.tsx
│   │       └── toast.tsx
│   ├── pages/
│   │   ├── dashboard.tsx
│   │   ├── temu/
│   │   │   ├── orders.tsx
│   │   │   └── inventory.tsx
│   │   ├── pdf/
│   │   │   └── reader.tsx
│   │   └── csv/
│   │       └── processor.tsx
│   ├── hooks/
│   │   ├── use-api.ts
│   │   └── use-websocket.ts
│   ├── lib/
│   │   ├── api-client.ts    # axios instance
│   │   └── utils.ts         # tailwind helper
│   ├── types/
│   │   ├── order.ts
│   │   ├── inventory.ts
│   │   └── api.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── public/
│   └── icons/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── postcss.config.js
```

---

## 2. Migrations-Reihenfolge

### Phase 1: Foundation (Sprint 1)
1. Vite-Projekt erstellen
2. TypeScript konfigurieren
3. Tailwind CSS einrichten
4. shadcn/ui installieren und konfigurieren
5. App Shell erstellen (Layout, Sidebar, Header)

### Phase 2: Shared Components (Sprint 2)
1. Basis-Komponenten: Button, Card, Input, Dialog, Table
2. Loading States: Spinner, Skeleton
3. Toast-Notifications
4. Error Boundary

### Phase 3: Dashboard (Sprint 3)
- Aus `frontend/index-new.html` + `frontend/dashboard.js`
- Stats-Cards, Quick-Actions
- API-Integration

### Phase 4: TEMU Module (Sprint 4)
- Aus `modules/temu/frontend/temu.js`, `temu.html`, `temu.css`
- Orders Page mit Table, Filter, Sortierung
- Inventory Page
- Sync-Dialoge mit Progress

### Phase 5: PDF & CSV (Sprint 5)
- PDF Reader: Upload, Processing, Results
- CSV Processor: Upload, Validation, Processing

---

## 3. API-Endpunkte (bestehende)

### TEMU
- `GET /api/temu/orders` - Bestellungen abrufen
- `POST /api/temu/sync/orders` - Bestellungen synchronisieren
- `GET /api/temu/inventory` - Inventar abrufen
- `POST /api/temu/sync/inventory` - Inventar synchronisieren

### PDF
- `POST /api/pdf/process` - PDF verarbeiten
- `GET /api/pdf/result/{job_id}` - Ergebnis abrufen

### CSV
- `POST /api/csv/validate` - CSV validieren
- `POST /api/csv/process` - CSV verarbeiten

### System
- `GET /api/logs` - Logs abrufen
- `GET /api/jobs` - Jobs abrufen
- `WebSocket /ws/logs` - Live-Log-Stream

---

## 4. Erwartete Verbesserungen

| Aspekt | Vanilla JS (alt) | React 19 (neu) |
|--------|------------------|----------------|
| **Type Safety** | Keine | TypeScript (100%) |
| **Komponenten-Wiederverwendung** | Manuell | shadcn/ui |
| **State Management** | Vanilla + DOM | TanStack Query |
| **Routing** | Multi-HTML | Single Page |
| **Styling** | CSS-Dateien | Tailwind CSS |
| **Build** | Kein | Vite (HMR) |
| **Performance** | Mittel | Optimiert |

---

## 5. Parallelbetrieb

Während der Migration:
- **Alt (Port 8888):** Vanilla JS Frontend bleibt aktiv
- **Neu (Port 3000):** React Frontend wird entwickelt

Übergang:
1. React auf Port 3000 testen
2. API-Endpunkte validieren
3. Feature-Parität sicherstellen
4. DNS/Routing umstellen

---

## 6. Acceptance Criteria

### Sprint 1 (Foundation)
- [x] `npm run dev` startet React auf Port 3000
- [x] shadcn/ui Components importierbar
- [x] Sidebar und Navigation funktionieren
- [x] Routing zwischen Pages möglich
- [x] Vite Proxy (/api → localhost:8888) eingerichtet
- [x] API-Client mit korrekten Endpunkten

### Sprint 2 (Shared Components)
- [x] Alle Basis-Components vorhanden (Button, Card, Input, Select, Dialog, Table, Dropdown, Tabs)
- [x] Loading/Error States implementiert (Skeleton, Spinner, Error Boundary)
- [x] Toast-Notifications funktionieren
- [x] Custom Components: Empty States, Progress Overlay

### Sprint 3 (Dashboard)
- [x] Dashboard zeigt Stats an
- [x] Neue Navigation mit einklappbaren Menüs (Werkzeuge, Verwaltung)
- [x] Quick Actions Component

### Sprint 4 (TEMU Module)
- [x] TEMU-Connector Page: Scheduled Jobs, Manual Trigger, Logs
- [ ] TEMU Orders mit Table + Filter
- [ ] TEMU Inventory mit Table

### Sprint 5 (PDF & CSV Module)
- [x] PDF Reader mit Upload Zone, Tabs, Progress Overlay, Excel Download, Logs
- [x] CSV Processor mit Upload, Status, Report, Export, Logs

---

## 7. Offene Punkte

### Kurzfristig
- [ ] TEMU Orders Page (Table mit Filter/Sortierung)
- [ ] TEMU Inventory Page

### Mittelfristig
- [ ] Platzhalter-Seiten: Kundenzahl, Aufträge, Artikel, Versand
- [ ] Weitere Marktplätze: Amazon, eBay, Otto, Kaufland

### Technisch
- [ ] Storybook für Component-Dokumentation
- [ ] E2E Tests (Playwright)
- [ ] Performance-Tests

---

## 8. Implementierte Features (19.02.2026)

### Abgeschlossen ✅
- Vite Projekt mit React 19 + TypeScript + Tailwind
- shadcn/ui Components (Button, Card, Input, Select, Dialog, Table, Dropdown, Tabs)
- Custom Components (Loading Spinner, Skeleton, Toast, Error Boundary, Empty State, Progress Overlay)
- Dashboard mit Stats Cards und Quick Actions
- Navigation mit einklappbaren Menüs (Werkzeuge, Verwaltung)
- TEMU-Connector Page (Scheduled Jobs, Manual Trigger, Logs)
- PDF Reader Page (Upload Zone, Tabs, Progress Overlay, Excel Download, Logs)
- CSV Processor Page (Upload Zone, Status Polling, Mini-Report, Tabs, Export, Logs)
- API-Client mit allen Endpoints (TEMU, PDF, CSV, Jobs, Logs)
- Vite Proxy (/api → localhost:8888)
- React-Frontend aktiviert (alte Vanilla JS Frontends entfernt)

### In Progress 🔄
- TEMU Orders/Inventory Pages

### Geplant 📋
- Weitere Marktplätze (Amazon, eBay, Otto, Kaufland)
- Platzhalter-Seiten (Kundenzahl, Aufträge, Artikel, Versand)

---

## 9. Notes

- **CSS-Konsolidierung:** Alte CSS-Dateien (.css) nach Tailwind-Klassen migriert
- **API-Client:** Vollständiger TypeScript-Client mit allen Endpoints
- **Icons:** shadcn/ui Icons (Lucide) verwenden
- **Service Worker:** Aktueller SW bleibt für PWA-Funktion
- **React-Frontend aktiviert:** Alte Vanilla JS Frontends entfernt (frontend/, modules/*/frontend/)
- **Entwicklungsumgebung:** API auf Port 8888, React Dev Server auf Port 3000

---

*Zuletzt aktualisiert: 19. Februar 2026*