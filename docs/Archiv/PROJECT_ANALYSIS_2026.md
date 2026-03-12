# TEMU ERP / TOCI ERP - Projekt-Analyse & Refactoring-Plan

**Erstellt:** 16. Februar 2026  
**Status:** Analyse abgeschlossen, bereit für Umsetzung  
**Arbeitsumgebung:** Entwicklungsumgebung (Port 8888)

---

## 1. Projektübersicht

### Projektname
- TEMU ERP / TOCI ERP

### Ziel
- Ablösung von JTL-Wawi durch ein proprietäres Multi-Channel OMS/WMS

### Aktuelle Module

| Modul | Status | Beschreibung |
|-------|--------|--------------|
| `modules/temu/` | ✅ Stabil | TEMU API-Integration (Orders, Inventory, Tracking) |
| `modules/pdf_reader/` | ✅ Stabil | PDF-Rechnungen & Werbungs-Extraktion |
| `modules/csv_verarbeiter/` | ✅ Stabil | CSV-Verarbeitung für Amazon DATEV-Exporte |
| `modules/jtl/` | ✅ Stabil | JTL-XML-Export (Legacy-Brücke) |
| `modules/shared/` | ✅ Stabil | DB-Connection, Repositories, Logging, Config |

### Technologie-Stack (Aktuell)

- **Backend:** FastAPI + Python 3.12
- **Frontend:** Vanilla JS + HTML/CSS (pro Modul)
- **Datenbank:** MSSQL (Toci + JTL)
- **Architektur:** Modular Monorepo mit Repository Pattern
- **Ports:** 8888 (dev), 8000 (production)

---

## 2. Refactoring-Status

### Bereits abgeschlossen ✅

| Refactoring | Datum | Beschreibung |
|-------------|-------|--------------|
| Monorepo-Migration | Feb 2026 | Alle Module in `modules/` konsolidiert |
| CSV-Verarbeiter Migration | Feb 2026 | Standalone → Modul integriert |
| TEMU Refactoring | 13.Feb 2026 | God Classes, Magic Numbers, Duplikate entfernt |
| PDF Reader Refactoring | 13.Feb 2026 | Security-Fixes, Parsing-Konsolidierung |
| Shared Module Refactoring | 13.Feb 2026 | BaseRepository, Logging-Zentralisierung |
| JTL XML-Export Refactoring | 13.Feb 2026 | Bug-Fixes, Code-Qualität |
| Frontend Security Review | 13.Feb 2026 | CSP, XSS-Fixes, WCAG AA Konformität |

### Ausstehend / Geplant ⏳

| Priorität | Bereich | Beschreibung |
|-----------|---------|--------------|
| **HOCH** | Frontend-Migration | Vanilla JS → React 19 + TypeScript |
| **HOCH** | Backend API | CORS für React, JWT-Auth Vorbereitung |
| **MITTEL** | Multi-Channel | eBay, Kaufland, Otto, Amazon Integration |
| **MITTEL** | WMS | Picklisten, Lagerverwaltung |
| **NIEDRIG** | Dokumentation | Fortlaufend aktualisieren |

---

## 3. Vision und Ziele

### Vision 2026
- **Ziel:** JTL-Wawi komplett ersetzen
- **Kanäle:** TEMU (live), eBay, Kaufland, Otto, Amazon
- **Architektur:** Lean OMS/WMS ohne JTL-Abhängigkeit

### Phasen-Plan

**Phase 1 (Aktuell):** Brücke bauen
- FastAPI + React 19 SPA
- CORS konfigurieren
- JWT-Auth vorbereiten

**Phase 2 (Q2-Q3 2026):** Multi-Channel Expansion
- eBay API Integration
- Kaufland API Integration
- Otto API Integration

**Phase 3 (Q4 2026+):** Versand-Autonomie
- DHL/DPD API Anbindung
- Eigene Picklisten-Generierung
- JTL-Exit (XML-Export deaktivieren)

### Frontend-Architektur (Geplant)

```
frontend-react/
├── src/
│   ├── app/                    # App Shell & Routing
│   │   ├── App.tsx
│   │   ├── router.tsx
│   │   └── layout/             # Sidebar, Header
│   ├── features/               # Feature-Module
│   │   ├── dashboard/          # Dashboard ⭐ START HIER
│   │   ├── temu/               # TEMU Orders & Inventory
│   │   ├── pdf-reader/         # PDF Processing
│   │   ├── csv-processor/      # CSV Processing
│   │   └── auth/               # Auth (später)
│   ├── shared/                 # Shared Components, Hooks, Utils
│   │   ├── components/         # UI Components
│   │   ├── hooks/              # Custom Hooks
│   │   ├── lib/                # Utils & API Client
│   │   └── types/              # TypeScript Interfaces
│   └── styles/                 # Tailwind CSS
├── public/
│   └── icons/                  # PWA Icons
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
└── components.json              # shadcn/ui config
```

---

## 4. Agenten-Struktur

### Definierte Agenten

| Agent | Rolle | Modell | Status |
|-------|-------|--------|--------|
| **lead_architect** | Projektmanager & Planer | minimax-m2.5 | ✅ Primär |
| **database_architect** | MSSQL-Stratege | minimax-m2.5 | ✅ Subagent |
| **backend_refactoring** | FastAPI Migration-Lead | minimax-m2.5 | ✅ Subagent |
| **frontend_refactoring** | React 19 Migration-Lead | minimax-m2.5 | ✅ Subagent |
| **documentation_agent** | Dokumentations-Pflege | minimax-m2.5 | ✅ Subagent |

### Agenten-Beschreibungen

**lead_architect:**
- Erstellt Blueprints und delegiert an Subagenten
- **SCHREIBT KEINEN CODE** (nur Architektur-Skizzen)
- Definiert API-Verträge zwischen Frontend/Backend

**database_architect:**
- Plant Schemata, Relationen, Migrationspfade
- **ERZEUGT KEINEN SQL-CODE** (nur Spezifikation)

**backend_refactoring:**
- Transformiert Python zu Pydantic & Repository Pattern
- Fokus auf JTL-Independence

**frontend_refactoring:**
- Migriert Vanilla JS → React 19 + TypeScript
- Apple-style UI beibehalten

---

## 5. Skills-Analyse

### Verfügbare Skills

| Skill | Geeignet für | Bewertung |
|-------|--------------|-----------|
| `backend-refactor` | ✅ Python Refactoring | **Geeignet** - Detaillierte Pattern für God Classes, Magic Numbers |
| `frontend-refactor` | ⚠️ Frontend Refactoring | **Teilweise geeignet** - Gut für Vanilla JS Cleanup |
| `frontend-migration-workflow` | ⚠️ Vanilla → React | **Überarbeitungsbedürftig** - Prozess gut, aber basiert auf CRA statt Vite |
| `refactoring-workflow` | ✅ Generell | **Geeignet** - 4-Phasen Prozess |
| `project-logging` | ✅ Backend | **Geeignet** - DB-basiertes Logging |
| `agent-change-documentation` | ✅ Alle | **Geeignet** - AGENT_CHANGES.md |
| `agent-documentation` | ✅ Alle | **Geeignet** - Docstrings, ADR |

### Empfehlungen für Skills

Der Skill **`frontend-migration-workflow`** basiert noch auf **Create React App (CRA)**, aber in `SESSION_HANDOVER.md` wurde entschieden, dass wir **Vite** nutzen sollten.

**Empfehlung:**
- Skill aktualisieren auf Vite-basierten Workflow
- Oder neuen Skill `vite-react-migration-workflow` erstellen

---

## 6. Offene Aufgaben & Nächste Schritte

### Priorität 1: React-Migration starten

1. **Vite + React + TypeScript** Projekt erstellen (`frontend-react/`)
2. **shadcn/ui** installieren
3. **Tailwind CSS** mit Apple-Style Theme konfigurieren
4. **App Shell** erstellen (Layout + Sidebar)
5. **Dashboard** als erste Komponente portieren

### Konkrete Schritte für Agenten

**Input für lead_architect:**
```
1. Starte mit Sprint 1 der React-Migration
2. Erstelle frontend-react/ mit Vite + TypeScript
3. Konfiguriere CORS im Backend für Port 3000
4. Baue die Sidebar-Navigation (alle Module sichtbar)
```

**Input für frontend_refactoring:**
```
1. Analysiere frontend/dashboard.js und frontend/master.css
2. Erstelle React-Komponenten für Dashboard
3. Nutze das frontend-migration-workflow Skill
4. Nutze TypeScript Interfaces für alle API-Responses
```

---

## 7. Potenzielle Risiken

| Risiko | Einschätzung | Mitigation |
|--------|--------------|------------|
| **Skill mismatch** | frontend-migration-workflow basiert auf CRA | Skill aktualisieren oder neuen erstellen |
| **CORS-Probleme** | React + FastAPI auf verschiedenen Ports | CORS-Middleware aktivieren |
| **Parallelbetrieb** | Alte und neue Frontends gleichzeitig | Feature-Flags oder Routing-Strategie |
| **Auth-Komplexität** | JWT via HttpOnly Cookies | Später implementieren (Phase 1 ohne Auth) |
| **Scope Creep** | Immer mehr Features hinzufügen | SPEC.md/REQUIREMENTS.md erstellen |

---

## 8. Architektur-Empfehlung für spätere Trennung

### Langfristiges Ziel: Zwei separate Repositories

```
/home/chx/jtl_erp/
├── backend/              # FastAPI + Business-Logik
│   ├── modules/
│   ├── workers/
│   ├── main.py
│   └── requirements.txt
├── frontend-react/       # React 19 SPA
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
└── docs/                # Bleibt zentral oder wird geteilt
```

**Vorteile:**
- Klare Trennung von Backend und Frontend
- Unabhängige Deployments möglich
- Verschiedene Teams könnten parallel arbeiten

**Nachteile:**
- Mehr Koordinationsaufwand
- Shared Code muss extrahiert werden

---

## 9. Empfehlung: SPEC.md/REQUIREMENTS.md erstellen

### Warum eine Spec-Datei sinnvoll ist:

1. **Scope definieren** - Was soll das ERP können? Was NICHT?
2. **Prioritäten setzen** - Was ist MVP? Was kann später?
3. **Verhindert Feature Creep** - Alles was hinzukommt, muss in die Struktur passen
4. **Fokus behalten** - Du weißt jederzeit wo du stehst
5. **Verhindert "sich verlieren"** - Du hast immer eine Referenz

### Was in die SPEC.md rein sollte:

**Menü-Struktur (Dashboard-Bereich):**
- Dashboard (Übersicht)
- Aufträge (alle Plattformen)
- Lager/Versand
- Artikel/Produkte
- Kunden

**Admin-Bereich:**
- Einstellungen
- Plattform-Verbindungen
- Benutzer

**Was JTL heute kann (relevant für uns):**
- Auftragsverwaltung
- Lagerbestand
- Versandlabel-Druck
- Rechnungsdaten (schon teilweise mit PDF-Reader)
- Kundenverwaltung

### Struktur-Vorschlag:

```
docs/SPEC.md

# TEMU ERP - Specification & Requirements

## 1. Vision
- Kurze Beschreibung des Projekts
- Ziel: JTL-Ablösung

## 2. Scope (MVP)
- Was gehört zum Minimum Viable Product?
- Was gehört NICHT dazu?

## 3. Menü-Struktur
- Haupt-Navigation
- Admin-Bereich

## 4. Funktionale Anforderungen
- Auftragsverwaltung
- Lager/Versand
- Artikel
- Kunden
- Plattform-Integrationen

## 5. Technische Anforderungen
- Tech-Stack
- Architektur
- Security

## 6. Phasen-Plan
- Phase 1: MVP
- Phase 2: Erweiterungen
- Phase 3: JTL-Exit
```

---

## 10. Zusammenfassung

### Projekt ist bereit für React-Migration weil:

1. ✅ Backend ist stabil und gut strukturiert (Repository Pattern, Pydantic)
2. ✅ Module sind sauber getrennt (temu, pdf_reader, csv_verarbeiter, jtl)
3. ✅ Agenten und Skills sind definiert und funktional
4. ✅ Dokumentation ist aktuell und umfassend
5. ✅ Vision ist klar: JTL-Ablösung durch eigenes OMS/WMS

### Empfohlene Reihenfolge:

1. **lead_architect** startet mit React-Planung
2. **frontend_refactoring** beginnt mit Vite-Projekt
3. **backend_refactoring** kümmert sich um CORS
4. **documentation_agent** aktualisiert Docs parallel

### Nächste Schritte (morgen):

1. [ ] SPEC.md/REQUIREMENTS.md erstellen (oder nicht, je nach Präferenz)
2. [ ] lead_architect Agent starten
3. [ ] Vite + React + TypeScript Projekt erstellen
4. [ ] CORS im Backend konfigurieren

---

**Fragen für morgen:**
1. Soll die SPEC.md vor dem Start erstellt werden?
2. Welche Features haben höchste Priorität im Dashboard?
3. Soll die Backend/Frontend-Trennung sofort vorbereitet werden?

---

*Analysis completed: 16. February 2026*
