# TEMU ERP - Shared CLI Guidelines

This file is the canonical, CLI-neutral instruction set for working in this repository.

Use it as the shared base for tools such as Claude Code, OpenCode, Copilot Chat, or other coding CLIs.

Important practical note:
- Some CLIs auto-discover only tool-specific filenames such as `CLAUDE.md` or `AGENTS.md`.
- Because of that, those files may still need to exist for automatic loading.
- Edit this file first when shared guidance changes, then sync the tool-specific wrappers if needed.

---

## What This File Is

This file is an operating guide, not the full source of truth for the runtime architecture.

When project reality and this file diverge, trust these sources in this order:

1. Runtime entrypoints: `main.py`, `start_dev.sh`, `frontend-react/package.json`
2. Active code under `modules/`, `workers/`, and `frontend-react/src/`
3. Current architecture docs such as `docs/ARCHITECTURE/code_structure.md`
4. Active migration or transition specs such as `docs/SPECS/TEMU_DATEV_INTEGRATION_PLAN.md`
5. This file

---

## Current Project Status

- **Stack:** Python 3.11+ | FastAPI | SQLAlchemy 2.0 | MSSQL | Pydantic 2.5 | React 19 | TypeScript | Vite | Tailwind
- **Architecture:** Modular monorepo with a single FastAPI gateway in `main.py`
- **API port:** `8401`
- **Dev frontend port:** `3000`

### Active backend structure

- `main.py` is the active FastAPI gateway
- Backend routes are primarily attached through module routers and shared routers
- Core active modules are currently:
  - `modules/temu`
  - `modules/pdf_reader`
  - `modules/csv_verarbeiter`
  - `modules/shared`
  - `workers`

### Active frontend structure

- `frontend-react/` is the active frontend application
- The frontend uses Vite, React 19, TypeScript, Tailwind, and TanStack Query

### Transitional area

- `modules/temu_datev/` exists in the repo but is not yet fully integrated into the main gateway/frontend architecture
- It currently contains imported standalone backend/frontend structure that should be treated as migration work, not as the canonical architecture

---

## Development Commands

### Development
```bash
# API server (development)
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8401

# Alternative development start helper
./start_dev.sh

# React frontend
cd frontend-react && npm run dev

# React production build
cd frontend-react && npm run build
```

### Python checks
```bash
black .
black --check .
flake8 . --max-line-length=120
mypy .
pytest -v
pytest -k "pattern"
pytest tests/test_file.py::TestClass::test_method
```

### Frontend checks
```bash
cd frontend-react
npm run build
npm run lint
npx tsc --noEmit
```

---

## Working Rules

### Backend

- Keep the single-gateway architecture centered on `main.py`
- Prefer module routers under `modules/<domain>/router.py`
- Prefer business logic under `modules/<domain>/services/`
- Use type hints consistently
- Use `with db_connect(DB_TOCI) as conn:` for DB access
- Raise specific exceptions and translate API failures to `HTTPException` where appropriate
- Avoid introducing new standalone apps inside modules

### Frontend

- Use the existing `frontend-react/` app instead of adding new standalone frontends
- Use functional components and TypeScript types
- Use Tailwind for styling
- Use TanStack Query for server state
- Use `@/lib/api-client` for API access
- Reuse existing shared and UI components before creating new ones

### Runtime data and configuration

- Keep runtime data outside Git
- Prefer central settings over hardcoded local paths
- Follow the existing `data/` layout and shared config patterns
- Treat `modules/temu_datev/` path handling as an active migration area

---

## Project Structure

```text
main.py                    # Active FastAPI gateway
modules/<domain>/          # Backend modules
├── router.py              # FastAPI endpoints
├── services/              # Business logic
│   └── config.py          # Constants/config when needed

modules/shared/            # Shared infrastructure
workers/                   # Scheduler and job routing

frontend-react/            # Active React frontend
├── src/
│   ├── pages/
│   ├── components/
│   ├── lib/
│   └── types/
└── dist/

data/                      # Runtime inputs/outputs
docs/                      # Architecture, specs, operations docs
```

---

## When Starting Work

For most non-trivial work, read the relevant source files first.

Recommended minimum context:

- `main.py`
- `start_dev.sh`
- `frontend-react/package.json`
- The target module you are changing

Read these docs when relevant:

- `docs/ARCHITECTURE/code_structure.md` for current structure
- `docs/API/architecture.md` for backend/API conventions
- `docs/FRONTEND/architecture.md` for frontend conventions
- `docs/SPECS/TEMU_DATEV_INTEGRATION_PLAN.md` for DATEV integration work

Do not assume this file alone is sufficient for migration or architecture decisions.

---

## Change Hygiene

- Never commit secrets; use `.env`
- Validate inputs with Pydantic models
- Keep changes consistent with the current monorepo architecture
- Update `docs/AGENT_CHANGES.md` after meaningful changes
- If shared guidance changes, update this file first and then sync `AGENTS.md` and `CLAUDE.md`

*Last updated: 12. Mar 2026*