# TEMU ERP - Agent Guidelines

> Canonical shared source: `AI_CLI_GUIDELINES.md`
>
> This file is kept tool-specific for CLI auto-discovery compatibility.
> If shared guidance is updated, update `AI_CLI_GUIDELINES.md` first and then sync this file if needed.

This file mirrors the current shared repository guidance for tools that load `CLAUDE.md` automatically.

Refer to `AI_CLI_GUIDELINES.md` for the maintained canonical version.

---

## Current Project Status

- **Stack:** Python 3.11+ | FastAPI | SQLAlchemy 2.0 | MSSQL | Pydantic 2.5 | React 19 | TypeScript | Vite | Tailwind
- **Architecture:** Modular monorepo with a single FastAPI gateway in `main.py`
- **API port:** `8401`
- **Dev frontend port:** `3000`
- **Transition area:** `modules/temu_datev/` exists but is not yet fully integrated into the main gateway/frontend structure

---

## Operational Guidance

- Trust runtime entrypoints and active code before summary docs
- Use `main.py` as the active backend gateway
- Use `frontend-react/` as the active frontend
- Prefer module routers under `modules/<domain>/router.py`
- Prefer business logic under `modules/<domain>/services/`
- Avoid introducing new standalone apps inside modules
- Prefer central settings and the shared `data/` layout over hardcoded local paths

---

## Development Commands

```bash
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8401

./start_dev.sh

cd frontend-react && npm run dev
cd frontend-react && npm run build

black .
flake8 . --max-line-length=120
mypy .
pytest -v

cd frontend-react && npm run lint
cd frontend-react && npx tsc --noEmit
```

---

## Change Hygiene

- Never commit secrets; use `.env`
- Validate inputs with Pydantic models
- Use repository pattern for DB access
- Update `docs/AGENT_CHANGES.md` after meaningful changes

*Last updated: 12. Mar 2026*
