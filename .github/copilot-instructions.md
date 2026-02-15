# TEMU ERP - Agent Instructions

## Project Context
**Modular ERP Integration System**: TEMU Marketplace ↔ JTL ERP (MSSQL)  
**Tech Stack**: Python 3.12+ | FastAPI (async) | SQLAlchemy Core | APScheduler | Vanilla JS PWA

## Essential Commands
```bash
./start_dev.sh              # Dev server (port 8888, jobs disabled)
pm2 status temu-api         # Production status (port 8000)
pm2 logs temu-api --lines 50
```

## Database Pattern (MANDATORY)
**Always use context manager** from [modules/shared/database/connection.py](modules/shared/database/connection.py):
```python
from modules.shared import db_connect
from modules.shared.config.settings import DB_TOCI

with db_connect(DB_TOCI) as conn:  # Auto-commit/rollback
    repo = SomeRepository(conn)
    repo.insert_data(...)
```
**Repository Pattern**: All DB access via [modules/shared/database/repositories/](modules/shared/database/repositories/) (inherit [BaseRepository](modules/shared/database/repositories/base.py))

## Logging Pattern (DB-Based, NOT Files)
```python
from modules.shared import log_service, app_logger

# Business logs → SQL Server (for frontend display)
job_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
log_service.start_job_capture(job_id, "component_name")
log_service.log(job_id, "component_name", "INFO", "Step 1 complete")
log_service.end_job_capture(success=True, duration=12.5)

# Errors only → logs/app/ files
app_logger.error(f"Error: {e}", exc_info=True)
```

## Module Structure (New Features)
```
modules/<domain>/
  ├── router.py              # FastAPI endpoints + get_router()
  ├── services/              # Business logic
  │   └── config.py          # Domain constants
  └── frontend/              # HTML/CSS/JS
```
**Register in [main.py](main.py)**: `app.include_router(get_domain_router(), prefix="/api/<domain>")`

## Dependencies & Conventions
- **Config**: All settings from [modules/shared/config/settings.py](modules/shared/config/settings.py) + `.env`
- **Service DI**: Constructor injection with lazy-loaded repos (see [order_workflow_service.py](modules/temu/services/order_workflow_service.py))
- **Refactoring Standards**: See [.github/skills/backend-refactor/](/.github/skills/backend-refactor/SKILL.md) for code smells
- **Documentation**: Update [docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md) + [docs/AGENT_CHANGES.md](docs/AGENT_CHANGES.md) WITH code changes

## Key Files
- **Architecture**: [AI_GUIDE.md](AI_GUIDE.md) | [docs/README.md](docs/README.md)
- **Current Status**: [docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md)
- **DB Schema**: [db_schema.sql](db_schema.sql)
- **Frontend Entry**: [frontend/index-new.html](frontend/index-new.html) + [master.css](frontend/master.css)

## Security
- API keys in `.env` (NEVER commit)
- Credentials: `TEMU_APP_KEY`, `SQL_USERNAME`, `SQL_PASSWORD`
