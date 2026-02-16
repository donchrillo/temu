# TEMU ERP - OpenCode Session Context

## Projekt-Übersicht

**Projektname:** TEMU ERP / TOCI ERP  
**Ziel:** JTL-Ablösung - Komplettes ERP/WMS/OMS System  
**Technologie:**
- Backend: FastAPI + Python
- Frontend: React 19 + Tailwind (geplant)
- Datenbank: MSSQL
- Architektur: Modular Monorepo

---

## Agenten

Die Agenten sind in `.opencode/agents/` definiert:

| Agent | Beschreibung | Modell-Empfehlung |
|-------|--------------|-------------------|
| **lead-architect** | Projektmanager & Technischer Planer. Erstellt Blueprints und delegiert Aufgaben. Schreibt selbst KEIN Code. | `claude/opus-4.6` oder `minimax/minimax-m2.5` |
| **database-agent** | Daten-Architekt für MSSQL. Plant Schemata, Relationen. Erzeugt KEIN SQL. | `minimax/minimax-m2.5` |
| **backend-refactoring** | FastAPI Migration-Lead. Transformiert Python zu Pydantic & Repository Pattern. | `minimax/minimax-m2.5` |
| **frontend-refactoring** | React 19 Migration-Lead. Vanilla JS → React SPA. | `minimax/minimax-m2.5` |
| **dokumentation** | Documentation Agent. Pflegt Docs, findet Redundanzen. | `minimax/minimax-m2` |

---

## Skills

Die Skills sind in `.opencode/skills/` definiert:

| Skill | Beschreibung |
|-------|--------------|
| `backend-refactor` | Code Smells erkennen und beheben (God Classes, Magic Numbers, etc.) |
| `refactoring-workflow` | Systematischer 4-Phasen Refactoring-Prozess |
| `project-logging` | DB-basiertes Logging-System |
| `agent-change-documentation` | Change-Dokumentation in AGENT_CHANGES.md |
| `agent-documentation` | Dokumentations-Guidelines |
| `frontend-refactor` | Frontend Code Smells & Patterns |
| `frontend-migration-workflow` | Vanilla → React 19 Prozess |

---

## Modell-Empfehlung (Februar 2026)

### Minimax-Modelle (Empfohlen - beste Preis/Leistung)

| Modell | Preis | Context | Stärke |
|--------|-------|---------|--------|
| **minimax-m2.5** | $0.30/M | 197K | Beste Coding-Performance (80.2% SWE-Bench!) |
| minimax-m2 | $0.25/M | 197K | Gut für einfache Tasks |
| minimax-m1 | $0.40/M | 1M | Long Context, Reasoning |

### Premium-Alternativen

| Modell | Preis | Context | Wann nutzen? |
|--------|-------|---------|--------------|
| claude/opus-4.6 | $5.00/M | 1M | Komplexe Architektur-Planung |
| openai/gpt-5.2-codex | ~$3.00/M | 200K | Beste Coding-Performance overall |
| google/gemini-3-pro | ~$1.50/M | 1M | Große Codebasen analysieren |

### Budget-Optionen

| Modell | Preis | Context | Wann nutzen? |
|--------|-------|---------|--------------|
| deepseek/deepseek-chat | $0.10/M | 64K | Einfache Docs |
| qwen/qwen3-coder | $0.07/M | 262K | Einfache Coding-Tasks |

---

## Empfohlene Konfiguration

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "minimax/minimax-m2.5",
  "small_model": "minimax/minimax-m2.1",
  "agent": {
    "lead-architect": {
      "description": "Projektmanager & Technischer Planer",
      "model": "minimax/minimax-m2.5",
      "mode": "primary"
    },
    "database-agent": {
      "description": "Daten-Architekt für MSSQL",
      "model": "minimax/minimax-m2.5",
      "mode": "subagent"
    },
    "backend-refactoring": {
      "description": "FastAPI Migration-Lead",
      "model": "minimax/minimax-m2.5",
      "mode": "subagent"
    },
    "frontend-refactoring": {
      "description": "React 19 Migration-Lead", 
      "model": "minimax/minimax-m2.5",
      "mode": "subagent"
    },
    "dokumentation": {
      "description": "Documentation Agent",
      "model": "minimax/minimax-m2.1",
      "mode": "subagent"
    }
  },
  "permission": {
    "task": {
      "database-agent": "allow",
      "backend-refactoring": "allow",
      "frontend-refactoring": "allow",
      "dokumentation": "allow"
    },
    "edit": "ask",
    "bash": "ask"
  }
}
```

---

## Architektur-Plan

### Bestehender Code (übernehmen)
- `modules/temu/` - TEMU API + Business-Logik (Bestellungen, Inventory)
- `modules/shared/` - Logging, Database, Config

### Neu zu entwickelnde Module
```
modules/
├── temu/                    # ✅ Vorhanden
├── customers/               # NEU
├── articles/                # NEU
├── suppliers/               # NEU
├── orders/                  # NEU (externe Bestellungen)
├── inventory/               # NEU
├── warehouse/               # NEU (Regale, Picklisten)
├── shipping/               # NEU (DHL/DPD)
└── shared/                  # ✅ Vorhanden, erweitern
```

### Legacy (old/ verschieben)
- `modules/csv_verarbeiter/` - Deprecated
- `modules/pdf_reader/` - Mini-Tool, nach tools/ verschieben
- `frontend/` (altes Vanilla JS) - Neu mit React 19

---

## Frontend-Stack (geplant)

- **Framework:** React 19
- **Styling:** Tailwind CSS
- **Design:** Apple Style, clean, hell
- **Features:**
  - Dark Mode / Light Mode Switcher
  - Responsive
  - PWA Ready

---

## Aktuelle Phase

1. ✅ Agenten und Skills definiert
2. ✅ Modell-Auswahl getroffen (Minimax M2.5)
3. ⏳ Ordner-Struktur umbauen
4. ⏳ GitHub Repo clonen
5. ⏳ OpenCode konfigurieren

---

## Wichtige Pfade

| Was | Pfad |
|-----|------|
| Projekt-Root | `/home/chx/entwicklung/` |
| Agenten (neu) | `.opencode/agents/` |
| Skills (neu) | `.opencode/skills/` |
| Agenten (backup) | `.github/agents/` |
| Skills (backup) | `.github/skills/` |
| Dokumentation | `docs/` |
| Module | `modules/` |

---

## Nächste Schritte

1. **GitHub Repo clonen** in neuen Ordner
2. **Config erstellen** - `~/.config/opencode/opencode.json`
3. **Agenten kopieren** - `.github/agents/` → `.opencode/agents/`
4. **Skills kopieren** - `.github/skills/` → `.opencode/skills/`
5. **Legacy umbenennen** - `modules/csv_verarbeiter/` → `old/`
6. **Neue Module planen** - mit LeadArchitect starten

---

*Erstellt: 16. Februar 2026*
*Modell: minimax/minimax-m2.5*
