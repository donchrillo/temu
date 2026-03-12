---
name: agent-change-documentation
description: Strukturierte Dokumentation aller Agent-Änderungen in AGENT_CHANGES.md für Nachvollziehbarkeit und Dokumentations-Synchronisation.
---

# 📝 Agent Change Documentation

## Zweck
Jede Code-Änderung durch einen Agenten **muss** in `docs/AGENT_CHANGES.md` dokumentiert werden, um:
- Änderungen nachvollziehbar zu machen
- Dem Dokumentations-Agenten Signale zu geben
- Ein Audit-Log für Team-Reviews zu haben
- Breaking Changes frühzeitig zu erkennen

## Pflicht-Regel

**Nach JEDER Code-Änderung:**
1. Öffne `docs/AGENT_CHANGES.md`
2. Füge unter **"Pending Changes"** einen neuen Eintrag hinzu
3. Nutze das Template unten
4. Speichere die Datei

## Template für Change-Log Einträge

```markdown
---
### [DATUM] - [AGENT-NAME]
**Modul/Datei:** `path/to/file.py`
**Art der Änderung:** [Refactoring|Feature|Bugfix|Performance|Security]
**Beschreibung:** [Kurze Zusammenfassung in einem Satz]
**Details:**
- [Detaillierter Punkt 1]
- [Detaillierter Punkt 2]
- [Detaillierter Punkt 3]
**Betroffene Dokumentation:**
- [ ] docs/API/architecture.md aktualisieren
- [ ] docs/ARCHITECTURE/code_structure.md überarbeiten
- [ ] README.md anpassen
**Impact:** [Low|Medium|High|Critical]
**Breaking Changes:** [Yes|No]
---
```

## Beispiele nach Änderungsart

### Refactoring (Backend)
```markdown
---
### 2026-02-15 - Backend Refactoring Agent
**Modul/Datei:** `modules/temu/services/order_service.py`
**Art der Änderung:** Refactoring
**Beschreibung:** God Class in fokussierte Services aufgeteilt
**Details:**
- OrderService aufgeteilt in: OrderService, OrderValidator, TaxCalculator
- Dependency Injection implementiert
- 450 Zeilen → 3x ~80 Zeilen reduziert
- Tests erweitert (Coverage: 45% → 75%)
**Betroffene Dokumentation:**
- [x] docs/API/architecture.md (neue Service-Struktur)
- [x] docs/ARCHITECTURE/code_structure.md (DI-Pattern)
- [ ] README.md (Setup-Anleitung anpassen)
**Impact:** Medium
**Breaking Changes:** No (rückwärtskompatibel via Facade)
---
```

### Refactoring (Frontend)
```markdown
---
### 2026-02-15 - Frontend Refactoring Agent
**Modul/Datei:** `frontend/modules/temu/temu.js`
**Art der Änderung:** Refactoring
**Beschreibung:** Vanilla JS zu React-Komponenten migriert
**Details:**
- loadLogs() Funktion (80 Zeilen) aufgeteilt
- Neue Komponenten: LogsList, LogItem, LogFilter
- Magic URLs entfernt → API_CONFIG Konstante
- innerHTML ersetzt durch JSX (XSS-safe)
- Performance: DocumentFragment → React Virtual DOM
**Betroffene Dokumentation:**
- [ ] docs/FRONTEND/architecture.md (React-Migration)
- [ ] docs/FRONTEND/CODE_PATTERNS.md (Komponenten-Guide)
**Impact:** Low
**Breaking Changes:** No
---
```

### Feature (Neu)
```markdown
---
### 2026-02-15 - Backend Refactoring Agent
**Modul/Datei:** `modules/warehouse/router.py`
**Art der Änderung:** Feature
**Beschreibung:** Neues Lager-Modul mit Bestandsverwaltung implementiert
**Details:**
- Neue Endpoints: GET/POST /api/warehouse/inventory
- Pydantic Models: InventoryItem, StockMovement
- Repository Pattern für warehouse_items Tabelle
- Batch-Import für CSV-Bestände
**Betroffene Dokumentation:**
- [ ] docs/API/architecture.md (neue Endpoints)
- [ ] docs/ARCHITECTURE/modules.md (Warehouse-Modul)
- [ ] docs/WORKFLOWS/inventory.md (neu erstellen)
**Impact:** High
**Breaking Changes:** No
---
```

### Bugfix (Critical)
```markdown
---
### 2026-02-15 - Database Architect
**Modul/Datei:** `modules/shared/database/repositories/order_repository.py`
**Art der Änderung:** Bugfix
**Beschreibung:** SQL-Injection Vulnerability in order_search() gefixt
**Details:**
- Raw SQL ersetzt durch Parameterized Query
- Input Validation für search_term hinzugefügt
- Unit-Tests für Edge-Cases ergänzt
- Security-Audit durchgeführt
**Betroffene Dokumentation:**
- [x] docs/SECURITY/vulnerabilities.md (Incident-Report)
- [x] docs/API/architecture.md (Sicherheits-Hinweise)
**Impact:** Critical
**Breaking Changes:** No
---
```

### Performance (Optimierung)
```markdown
---
### 2026-02-15 - Backend Refactoring Agent
**Modul/Datei:** `modules/temu/services/export_service.py`
**Art der Änderung:** Performance
**Beschreibung:** Batch-Processing für CSV-Exports (10x schneller)
**Details:**
- Einzelne DB-Queries ersetzt durch Batch-Query
- Pandas DataFrame für CSV-Generierung
- Streaming-Response für große Exports (>10k Zeilen)
- Benchmark: 45s → 4.2s bei 50k Zeilen
**Betroffene Dokumentation:**
- [ ] docs/PERFORMANCE/optimizations.md (Benchmark-Ergebnisse)
- [ ] docs/API/architecture.md (neue Export-Limits)
**Impact:** High
**Breaking Changes:** No
---
```

## Checkboxen für "Betroffene Dokumentation"

### Standard-Kategorien
- `[ ] docs/API/architecture.md` - API-Änderungen, neue Endpoints
- `[ ] docs/ARCHITECTURE/code_structure.md` - Strukturelle Änderungen
- `[ ] docs/DATABASE/architecture.md` - Schema-Änderungen
- `[ ] docs/FRONTEND/architecture.md` - UI/UX-Änderungen
- `[ ] docs/WORKFLOWS/[workflow].md` - Business-Logic-Änderungen
- `[ ] docs/PERFORMANCE/architecture.md` - Performance-Optimierungen
- `[ ] docs/SECURITY/vulnerabilities.md` - Security-Fixes
- `[ ] README.md` - Setup/Installation-Änderungen
- `[ ] AI_GUIDE.md` - KI-relevante Änderungen

## Impact-Level Guidelines

- **Low:** Kleine Refactorings, Code-Style, Comments
- **Medium:** Größere Refactorings, neue interne Services
- **High:** Neue Features, Breaking Changes in internen APIs
- **Critical:** Security-Fixes, Breaking Changes in Public APIs

## Breaking Changes Hinweise

**Breaking Change = YES**, wenn:
- Public API-Signatur ändert (Parameter, Return-Type)
- Datenbank-Migration erforderlich
- Config-File-Format ändert
- Frontend-Komponenten-Props ändern

**Dann zusätzlich angeben:**
- Migration-Guide (wie upgraden?)
- Deprecation-Timeline (wann wird altes entfernt?)
- Rückwärtskompatibilitäts-Layer (falls vorhanden)

## Workflow mit Dokumentations-Agent

```
1. Code-Agent macht Änderung
   ↓
2. Trägt in AGENT_CHANGES.md ein (Pending)
   ↓
3. Dokumentations-Agent wird aufgerufen
   ↓
4. Liest Pending Changes
   ↓
5. Aktualisiert markierte Dokumentationen
   ↓
6. Verschiebt Eintrag nach "Processed"
   ↓
7. Markiert mit Verarbeitungsdatum
```

## Tipps für gute Change-Logs

✅ **DO:**
- Spezifisch sein (Zeilen-Zahlen, Metriken)
- Begründung angeben (Warum wurde geändert?)
- Tests erwähnen (Coverage, neue Tests)
- Impact realistisch einschätzen

❌ **DON'T:**
- Vage Beschreibungen ("Code verbessert")
- Technischen Jargon ohne Kontext
- Fehlende Dokumentations-Checkboxen
- Impact übertreiben oder unterschätzen
