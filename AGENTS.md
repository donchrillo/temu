# TEMU ERP - Agent Guidelines

## Project Overview

**Project:** TEMU ERP / TOCI ERP - JTL Replacement  
**Stack:** Python 3.11+ | FastAPI | SQLAlchemy 2.0 | MSSQL | Pydantic 2.5  
**Architecture:** Modular Monorepo with Repository Pattern  
**Port:** 8888 (dev), 8000 (production)

---

## Build, Lint & Test Commands

### Development Server

```bash
# Start development server (port 8888, jobs disabled)
./start_dev.sh

# Or manually with venv
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8888
```

### Linting & Formatting

```bash
# Format code with Black
black .
black modules/           # format specific directory
black --check .          # check without modifying

# Lint with Flake8
flake8 .
flake8 --max-line-length=120 .  # with custom line length

# Type checking with MyPy
mypy .
mypy modules/shared/     # type check specific module
mypy --ignore-missing-imports .  # with stubs
```

### Testing

```bash
# Run all tests with coverage
pytest
pytest -v                    # verbose output
pytest --cov=.               # with coverage report
pytest --cov=modules/temu    # coverage for specific module

# Run single test file
pytest tests/test_order_service.py
pytest tests/                # all tests in directory

# Run single test function
pytest tests/test_order_service.py::TestOrderService::test_import_orders

# Run tests matching pattern
pytest -k "order"            # tests with 'order' in name
pytest -k "not slow"         # exclude slow tests

# Run with coverage threshold
pytest --cov=. --cov-fail-under=80

# Debugging
pytest --pdb                # drop into debugger on failure
pytest -s                   # show print statements
pytest -vv                  # extra verbose
```

### Database

```bash
# Apply migrations (if using Alembic)
alembic upgrade head

# Create migration
alembic revision --autogenerate -m "add new table"

# Reset database (development only)
# Check workers/ for DB reset scripts
```

---

## Code Style Guidelines

### General Principles

- **Follow existing patterns** - Match the style of surrounding code
- **Keep it simple** - Prefer readability over cleverness
- **DRY** - Don't Repeat Yourself, extract common logic
- **Single Responsibility** - Each function/class does one thing
- **Fail Fast** - Use guard clauses, validate early

### File Organization

```
modules/<domain>/
├── __init__.py           # Exports get_router(), models, services
├── router.py             # FastAPI endpoints + get_router()
├── services/             # Business logic
│   ├── __init__.py
│   ├── config.py         # Domain constants
│   └── *.py             # Service classes
├── models.py             # Pydantic/SQLAlchemy models (optional)
└── frontend/            # Static HTML/CSS/JS (if needed)

modules/shared/
├── config/settings.py   # All settings + .env
├── database/
│   ├── connection.py    # db_connect context manager
│   └── repositories/    # Repository classes
├── logging/             # log_service, app_logger
└── connectors/          # External API clients
```

### Imports (Order: stdlib → third-party → local)

```python
# Standard library
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Third-party
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

# Local modules (use explicit paths)
from modules.shared.config.settings import DB_TOCI
from modules.shared import db_connect, log_service
from modules.shared.database.repositories.temu.order_repository import OrderRepository
from .config import DOMAIN_CONSTANT  # relative for sibling modules
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Modules | lowercase, snake_case | `order_service.py` |
| Classes | PascalCase | `OrderService`, `BaseRepository` |
| Functions/methods | snake_case | `get_orders()`, `_parse_shipping()` |
| Constants | UPPER_SNAKE_CASE | `MAX_BATCH_SIZE`, `DEFAULT_TAX_RATE` |
| Variables | snake_case | `order_list`, `job_id` |
| Type aliases | PascalCase | `OrderDict = Dict[str, Any]` |
| Private methods | prefix with `_` | `_internal_method()` |

### Type Hints (Required)

```python
# Always use type hints for function signatures
def process_order(order_id: int) -> dict[str, Any]:
    pass

# Use Optional for nullable
def get_order(order_id: int) -> Order | None:
    pass

# Use | instead of Optional for Python 3.10+
def parse_value(value: str | None) -> int:
    pass

# Generic types with imports
from typing import TypeVar, Generic
T = TypeVar('T')

class Repository(Generic[T]):
    def get(self, id: int) -> T | None:
        pass
```

### Database Access (MANDATORY)

**Always use the context manager:**

```python
from modules.shared import db_connect
from modules.shared.config.settings import DB_TOCI

# Correct - context manager handles commit/rollback
with db_connect(DB_TOCI) as conn:
    repo = SomeRepository(conn)
    repo.insert_data(...)

# Never create connections directly in service code
# Always use repository pattern
```

**Repository Pattern:**

```python
from modules.shared.database.repositories.base import BaseRepository

class OrderRepository(BaseRepository):
    def find_by_id(self, order_id: int) -> Order | None:
        return self._fetch_one(
            text("SELECT * FROM orders WHERE id = :id"),
            {"id": order_id}
        )
    
    def save(self, order: Order) -> int:
        # insert or update
        pass
```

### Error Handling

```python
# Use try/except with specific exceptions
try:
    result = some_operation()
except ValueError as e:
    log_service.log(job_id, "module", "ERROR", f"Validation failed: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    # Always log with traceback
    error_trace = traceback.format_exc()
    log_service.log(job_id, "module", "ERROR", f"Unexpected: {e}", error_text=error_trace)
    app_logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")

# Use guard clauses for validation
def process(data: dict) -> Result:
    if not data:
        raise ValueError("No data provided")
    # happy path
```

### Logging (DB-Based)

```python
from modules.shared import log_service, app_logger

# Business logs → SQL Server (for frontend display)
job_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
log_service.start_job_capture(job_id, "component_name")
log_service.log(job_id, "component_name", "INFO", "Step 1 complete")
log_service.end_job_capture(success=True, duration=12.5)

# Errors only → app_logger (logs to file)
app_logger.error(f"Error: {e}", exc_info=True)
```

### Configuration

```python
# All config from modules/shared/config/settings.py + .env
from modules.shared.config.settings import DB_TOCI, TEMU_API_KEY

# Domain constants in modules/<domain>/services/config.py
# Use UPPER_SNE_CASE
BATCH_SIZE = 1000
DEFAULT_TIMEOUT = 30
```

### Service Layer (Dependency Injection)

```python
class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository = None,
        item_repo: OrderItemRepository = None,
        job_id: str | None = None
    ):
        self.order_repo = order_repo or OrderRepository()
        self.item_repo = item_repo or OrderItemRepository()
        self.job_id = job_id
    
    def process(self, data: dict) -> dict:
        # Use injected repos for transaction sharing
        if self.order_repo:
            return self._process_with_repo(data)
        else:
            with db_connect(DB_TOCI) as conn:
                repo = OrderRepository(conn)
                return self._process_with_repo(data, repo)
```

### API Endpoints

```python
@router.get("/orders/{order_id}")
async def get_order(order_id: int) -> OrderResponse:
    """Get order by ID."""
    service = OrderService()
    order = service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

# Use response models (Pydantic)
class OrderResponse(BaseModel):
    id: int
    bestell_id: str
    kaufdatum: datetime
    
    class Config:
        from_attributes = True
```

---

## Security

- **NEVER commit secrets** - Use `.env` files, add to `.gitignore`
- **API keys:** `TEMU_APP_KEY`, `SQL_USERNAME`, `SQL_PASSWORD`
- **Validate input** - Use Pydantic models for request validation
- **Sanitize output** - Escape user data in responses

---

## Testing Guidelines

When adding tests:

```python
# tests/test_order_service.py
import pytest
from unittest.mock import Mock, patch
from modules.temu.services.order_service import OrderService

class TestOrderService:
    @pytest.fixture
    def mock_repo(self):
        return Mock()
    
    def test_import_orders_success(self, mock_repo):
        service = OrderService(order_repo=mock_repo)
        result = service.import_from_api_response(
            orders=[...],
            shipping_responses={},
            amount_responses={}
        )
        assert result['total'] == 1
        mock_repo.save.assert_called_once()
    
    def test_import_orders_missing_data(self, mock_repo):
        service = OrderService(order_repo=mock_repo)
        result = service.import_from_api_response(
            orders=[],  # empty
            shipping_responses={},
            amount_responses={}
        )
        assert result['total'] == 0
```

---

## Documentation

Update these files when making significant changes:

- `docs/CURRENT_STATUS.md` - Project status
- `docs/AGENT_CHANGES.md` - Agent-specific changes
- Module README files if adding new modules

---

## Key Files Reference

| Purpose | File |
|---------|------|
| Main app | `main.py` (refactored: 419→162 Zeilen) |
| API Routers | `modules/shared/routers/` + `workers/jobs_router.py` |
| Error Handler | `modules/shared/errors/handler.py` |
| Database connection | `modules/shared/database/connection.py` |
| Settings | `modules/shared/config/settings.py` |
| Logging | `modules/shared/logging/log_service.py` |
| Job scheduler | `workers/worker_service.py` |
| DB Schema | `db_schema.sql` |

---

*Last updated: 19. Februar 2026*

---

## Phase 1 Refactoring (Februar 2026) - Zusammenfassung

### API Gateway Refactoring
- **main.py:** 419 → 162 Zeilen reduziert (-61%)
- **Neue Router-Struktur:**
  - `modules/shared/routers/static_router.py` - StaticFiles (/static, /icons, /components)
  - `modules/shared/routers/ui_router.py` - UI-Routen (/, /pdf, /temu, /csv, /docs)
  - `modules/shared/routers/log_router.py` - Log Management (/api/logs)
  - `modules/shared/routers/websocket_router.py` - WebSocket (/ws/logs)
  - `workers/jobs_router.py` - Job Management (/api/jobs)
  - `modules/temu/router.py` - TEMU API (/api/temu)
  - `modules/pdf_reader/router.py` - PDF API (/api/pdf)
  - `modules/csv_verarbeiter/router.py` - CSV API (/api/csv)
- **Neue Error-Handling:** `@handle_api_errors` Decorator in `modules/shared/errors/handler.py`
