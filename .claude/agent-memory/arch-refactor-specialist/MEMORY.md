# Architecture Refactoring Specialist - Memory

**Last Updated:** 2026-02-13

## Project: TEMU ERP Integration System

### Architecture Overview
- **Type:** Mature FastAPI monorepo (5 modules)
- **Backend:** FastAPI + SQLAlchemy + APScheduler
- **Frontend:** Vanilla JS PWA with shared components
- **Recent Refactoring:** 13 Feb 2026 (extensive cleanup completed)
- **Status:** Production-ready, well-architected system

### Key Architectural Patterns Found
1. **Repository Pattern:** BaseRepository with DI, context managers for transactions
2. **Service Layer:** Clear separation (Router → Service → Repository → DB)
3. **Workflow Orchestration:** BaseWorkflowService with inheritance (OrderWorkflow, InventoryWorkflow)
4. **Dependency Injection:** Service constructors with connection/repo injection
5. **Frontend Components:** Shared UI helpers (nav-loader, ui-helpers, progress-helper)

### Recent Refactorings Completed (13 Feb 2026)
- ✅ God Method extraction (order_service.py: 120→5 helper methods)
- ✅ Magic numbers → Named constants (config.py: 15+ constants)
- ✅ BaseWorkflowService extracted (55 lines duplication removed)
- ✅ Dead code cleanup (tracking, stock_sync services)
- ✅ Frontend security review (19 issues fixed)
- ✅ JTL XML export refactoring (critical data loss bug fixed)
- ✅ Shared module refactoring (DRY, type hints, security)

### High-Impact Opportunities Identified
1. **API Gateway Separation** (main.py 419 lines → 3 routers)
   - Extract static file serving to dedicated router
   - Extract job management to workers/router.py
   - Extract logging to shared/routers/log_router.py
   - Use FastAPI StaticFiles for security

2. **Error Handling Standardization**
   - Create @handle_api_errors decorator
   - Consistent HTTPException responses
   - Full traceback capture to log_service
   - ~15 endpoints affected

3. **Logging Configuration Module**
   - Extract hardcoded values (10MB, 5 backups) to config
   - Environment-based logging (LOG_LEVEL, LOG_MAX_BYTES)
   - Centralized format strings

### Code Smells Observed
- **main.py:** Mixed concerns (routing + file serving + job mgmt + logs + WebSocket)
- **Routers:** Inconsistent error handling (3 different patterns)
- **Frontend:** Duplicate fetch logic across 3 modules (pdf, csv, temu)
- **Repositories:** Repeated `find_by_*` patterns (good candidate for BaseRepository generics)

### Anti-Patterns NOT Found ✅
- No God Classes (recently refactored)
- No circular dependencies
- No missing separation of concerns at service layer
- No transaction management issues (context managers used correctly)
- No missing type hints (recently added)

### User Preferences & Constraints
- **Production System:** Avoid breaking changes
- **Recent Work:** Extensive refactoring just completed, build on existing patterns
- **Testing:** Must maintain existing workflow test compatibility
- **Incremental:** Prefer small, reviewable changes over large rewrites

### Implementation Notes
- **Feature Branches:** Create branch for each major refactoring
- **Testing Strategy:** Run existing workflow tests (order_sync, inventory_sync, pdf_process)
- **Rollback Plan:** Easy git revert for each isolated change
- **Documentation:** Update ARCHITECTURE.md after each change

### File Structure Patterns
```
modules/
  shared/        # DB, logging, config, connectors
    database/
      repositories/
        base.py  # BaseRepository with _fetch_one, _fetch_all, _execute_stmt
        common/  # Log repository
        temu/    # Order, OrderItem, Product, Inventory
        jtl_common/ # JTL lookups
    logging/
      log_service.py   # DB-based structured logging
      logger.py        # File-based technical errors
    connectors/
      temu/      # API client, orders_api, inventory_api, service
  temu/          # Order/Inventory workflows, services
  pdf_reader/    # PDF extraction (werbung, rechnungen)
  csv_verarbeiter/ # CSV processing (Amazon DATEV)
  jtl/           # XML export service
workers/         # APScheduler integration
frontend/        # PWA with shared components
```

### Metrics
- **Backend Files:** 50+ Python modules
- **Service Classes:** 14 across modules
- **Repositories:** 7 (all inherit BaseRepository)
- **API Endpoints:** 22 in main.py + module routers
- **Frontend Components:** 5 shared (nav-loader, ui-helpers, progress-helper, etc.)

### Links to Detailed Docs
- Project docs: `/home/chx/entwicklung/docs/`
- Architecture: `docs/ARCHITECTURE/code_structure.md`
- Current status: `docs/CURRENT_STATUS.md`
- Recent changes: `docs/AGENT_CHANGES.md`
