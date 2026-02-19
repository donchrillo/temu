# TEMU ERP - Agent Guidelines

## Project Overview
- **Stack:** Python 3.11+ | FastAPI | SQLAlchemy 2.0 | MSSQL | Pydantic 2.5 | React 19 | TypeScript | Vite | Tailwind
- **Architecture:** Modular Monorepo with Repository Pattern
- **Dev Ports:** 8888 (API), 3000 (React Frontend)

---

## Build, Lint & Test Commands

### Development
```bash
# API Server (port 8888)
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8888

# React Frontend (port 3000, with hot reload)
cd frontend-react && npm run dev

# Build React for production
cd frontend-react && npm run build
```

### Python Linting & Testing
```bash
# Format
black .
black --check .          # check only

# Lint
flake8 . --max-line-length=120

# Type check
mypy .

# Test single file/function
pytest tests/test_file.py::TestClass::test_method
pytest -k "pattern"      # match pattern
pytest -v                # verbose
pytest -s               # show prints
```

### React/TypeScript
```bash
cd frontend-react
npm run build            # production build
npm run lint            # ESLint
npx tsc --noEmit       # TypeScript check
```

---

## Code Style Guidelines

### Python (Backend)
- **Imports:** stdlib → third-party → local
- **Naming:** snake_case (functions/vars), PascalCase (classes), UPPER_SNAKE_CASE (constants)
- **Type Hints:** Required, use `|` instead of `Optional` (Python 3.10+)
- **DB Access:** ALWAYS use context manager `with db_connect(DB_TOCI) as conn:`
- **Error Handling:** Specific exceptions + logging + HTTPException

```python
from modules.shared import db_connect
from modules.shared.config.settings import DB_TOCI

with db_connect(DB_TOCI) as conn:
    repo = OrderRepository(conn)
    repo.insert_data(...)
```

### React/TypeScript (Frontend)
- **Components:** Functional components with hooks, PascalCase filenames
- **Styling:** Tailwind CSS classes, no custom CSS unless necessary
- **State:** Use TanStack Query for server state, useState for local state
- **API:** Use apiClient from `@/lib/api-client`

```typescript
import { useState, useEffect } from 'react';
import { apiClient, csvApi } from '@/lib/api-client';

export function MyComponent() {
  const [data, setData] = useState<Type | null>(null);
  
  useEffect(() => {
    csvApi.getStatus(jobId).then(setData);
  }, [jobId]);
  
  return <div>{data}</div>;
}
```

---

## Project Structure
```
modules/<domain>/          # Backend modules
├── router.py             # FastAPI endpoints
├── services/             # Business logic
│   └── config.py         # Constants (UPPER_SNAKE_CASE)

frontend-react/           # React frontend
├── src/
│   ├── pages/           # Page components
│   ├── components/      # Reusable components
│   │   ├── ui/         # shadcn/ui components
│   │   └── shared/      # Custom shared components
│   ├── lib/             # Utilities (api-client.ts, utils.ts)
│   └── types/           # TypeScript interfaces
└── dist/                # Built output
```

---

## Key Commands Reference

| Task | Command |
|------|---------|
| Start API | `uvicorn main:app --reload --port 8888` |
| Start React | `cd frontend-react && npm run dev` |
| Build React | `cd frontend-react && npm run build` |
| Run tests | `pytest -v` |
| Single test | `pytest tests/x.py::TestClass::test_method` |
| Lint Python | `black . && flake8 .` |
| Lint React | `cd frontend-react && npm run lint` |

---

## Important Notes
- Never commit secrets → use `.env`
- Validate input with Pydantic models
- Use repository pattern for DB access
- Update `docs/AGENT_CHANGES.md` after changes

*Last updated: 19. Feb 2026*
