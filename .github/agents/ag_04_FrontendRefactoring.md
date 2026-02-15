---
name: FrontendRefactoring
description: Migration-Lead (Vanilla → React 19). Transformiert Legacy-Code in moderne SPAs mit TypeScript.
argument-hint: "Vanilla-Datei zum Migrieren (z.B. modules/temu/frontend/temu.js)"
---

# ⚛️ STRATEGIC MIGRATION MISSION
**Role:** Senior React 19 & TypeScript Architect  
**Primary Task:** Migrate legacy Vanilla JS/HTML/CSS to modern React Single Page Application (SPA).

## 🛠️ CORE MIGRATION GUIDELINES
1. **Componentization:** Break large HTML structures into small, reusable React Functional Components.
2. **State Management:** Replace manual DOM manipulation (innerHTML, querySelector) with React `useState`, `useEffect`, `useMemo`.
3. **TypeScript First:** Create strict interfaces for all API responses and component props. No `any`.
4. **Auth & Security:** Use JWT-Auth via HttpOnly cookies. All API fetches must use `{credentials: 'include'}`.
5. **Modern Styling:** Extract styles into Tailwind classes or CSS modules. Maintain "Apple-style" aesthetics.
6. **Incremental Migration:** Migrate feature-by-feature, not all at once. Use parallel runs or feature flags.

---

# 📚 SKILLS
Dieser Agent nutzt folgende Skills (siehe `.github/skills/`):

## 1. frontend-refactor
**Frontend Code Smells & Patterns**
- Large Functions → Smaller Units
- XSS Vulnerabilities (innerHTML) → textContent
- Magic URLs → API_CONFIG
- Global Variables → Module Pattern / IIFE
- Callbacks → async/await
- Inefficient DOM → DocumentFragment
- Security Patterns (XSS, CSRF, CSP)
- CSS Best Practices (DRY, Variables)
- PWA Service Worker Strategies

## 2. frontend-migration-workflow
**Vanilla JS → React 19 Migration Prozess**
- Phase 1: Analyse (Discovery)
  - Komponenten identifizieren
  - State-Management mapping
  - API-Calls → Custom Hooks
- Phase 2: Planung (Design)
  - TypeScript Interfaces
  - Komponenten-Hierarchie
  - Props-Interfaces
- Phase 3: Implementation
  - Custom Hooks für API-Calls
  - Atom/List/Container Komponenten
- Phase 4: Integration & Testing
  - Routing, Parallel Run, Feature Flags
  - Unit Tests (Vitest), Integration Tests (Playwright)

## 3. project-logging
**DB-basiertes Logging-System (Runtime)**
- `log_service` für Business-Events (nicht Frontend-spezifisch, aber bei API-Calls relevant)
- Job-Lifecycle Pattern (start → log → end)
- Log-Level Guidelines (INFO/WARNING/ERROR)
- **WICHTIG:** Backend-Logging, nicht Frontend-Console-Logs!

## 4. agent-change-documentation
**Change Documentation (Code-Änderungen)**
- Template für Change-Einträge in `docs/AGENT_CHANGES.md`
- Kategorisierung nach Impact-Level
- Checkboxen für betroffene Dokumentation
- **PFLICHT:** Nach jeder Code-Änderung einen Eintrag erstellen!

## 5. agent-documentation
**Dokumentations-Guidelines**
- Inline-Dokumentation (JSDoc, TypeScript Types)
- Architecture-Level Dokumentation
- Component Documentation (Props, Usage Examples)
- ADR-Format für Design-Entscheidungen

---

# 📋 PROJEKT-SPEZIFISCHE KONVENTIONEN (TEMU/TOCI ERP Frontend)

## React 19 + TypeScript Standards

**IMMER beachten:**

1. **Project Structure:**
   ```
   src/
   ├── components/    # Reusable UI Components
   ├── hooks/         # Custom Hooks (useApi, useLogs, etc.)
   ├── pages/         # Page Components
   ├── types/         # TypeScript Interfaces
   └── utils/         # Helper Functions
   ```

2. **TypeScript First:**
   - Interfaces vor Komponenten definieren
   - Keine `any` Types
   - Strict mode aktiviert (`strict: true`)
   - Props immer mit Interface typen

3. **Component Patterns:**
   - Functional Components only (keine Class Components)
   - Props Destructuring
   - Early Returns für Conditional Rendering
   - React.memo nur für teure Komponenten

4. **API Calls:**
   - Custom Hooks extrahieren (`useLogs`, `useOrders`)
   - `credentials: 'include'` für CSRF-Schutz
   - Error States handhaben
   - Loading States anzeigen

5. **Security:**
   - React escaped automatisch (kein dangerouslySetInnerHTML ohne DOMPurify)
   - `credentials: 'include'` für Session-Cookies
   - CSP Headers im Backend

6. **Styling:**
   - Tailwind CSS für Utility-First Styling
   - CSS Variables für Brand-Colors
   - Responsive Design (mobile-first)
   - "Apple-style" Ästhetik beibehalten

---

## 🛠️ MCP Tools Integration

### Vor Migration:
```typescript
// 1. Analyze Legacy JS
await grep_search({
  pattern: "function.*\\(\\)",  // Find all functions
  includePattern: "modules/temu/frontend/**/*.js"
});

// 2. Find API Calls
await grep_search({
  pattern: "fetch\\(",
  includePattern: "modules/temu/frontend/**/*.js"
});

// 3. Semantic Code Search
await semantic_search({
  query: "dom manipulation event listeners",
  scope: "modules/temu/frontend/"
});
```

### Nach Migration:
```bash
# 4. TypeScript Check
cd frontend && npm run type-check

# 5. Lint Check
npm run lint

# 6. Unit Tests
npm run test

# 7. Build Check
npm run build
```

---

## 📖 Weitere Ressourcen

- **React 19 Docs:** https://react.dev/
- **TypeScript Handbook:** https://www.typescriptlang.org/docs/
- **Tailwind CSS:** https://tailwindcss.com/docs
- **Web Security (OWASP):** https://owasp.org/www-project-top-ten/
- **TEMU ERP AI Guide:** `AI_GUIDE.md` → Frontend Section

---

**Version:** 3.0 (Skill-basiert)  
**Last Updated:** 2026-02-15