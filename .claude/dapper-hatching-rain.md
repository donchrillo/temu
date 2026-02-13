# Architectural Refactoring Plan - TEMU ERP Integration System

**Date:** 2026-02-13
**Status:** Awaiting User Approval

---

## Context

The TEMU ERP integration system is a mature, well-architected FastAPI monorepo that has already undergone extensive refactoring on 13 Feb 2026 (God Method extraction, DRY improvements, frontend security hardening, CSS consolidation).

The comprehensive architectural review identified **10 incremental enhancement opportunities** - no critical structural flaws were found. The system follows solid patterns (Repository, DI, Service layer) with clear module boundaries.

**Why this refactoring?** While the architecture is sound, there are opportunities to:
1. Reduce complexity in the API gateway (`main.py` - 419 lines mixing 5 responsibilities)
2. Standardize error handling patterns across modules
3. Extract hardcoded configuration values
4. Improve code reusability (frontend fetch logic, repository queries)

This refactoring will enhance **maintainability, security, and consistency** without disrupting the stable production system.

---

## Recommended Approach: Phased Implementation

### Phase 1: High-Impact Core Improvements (Recommended Start)
**Focus:** API Gateway & Error Handling
**Effort:** 1 day
**Risk:** LOW (non-breaking, isolated changes)

#### Refactoring 1: API Gateway Separation of Concerns
**Problem:** `main.py` (419 lines) mixes 5 responsibilities:
- API gateway (module router mounting)
- Static file serving (14 custom endpoints)
- Job management API (6 endpoints)
- Logging API (5 endpoints)
- WebSocket endpoint

**Solution:**
- Extract static file serving to `modules/shared/routers/static_router.py`
  - Use FastAPI `StaticFiles` mount (eliminates path traversal risks)
  - Handles `/static/`, `/icons/`, `/components/`, module-specific files
- Extract job management to `workers/router.py` (optional)
- Extract logging API to `modules/shared/routers/log_router.py` (optional)

**Benefit:**
- `main.py`: 419 → ~150 lines (-64% complexity)
- Better security (built-in path traversal protection)
- Testable router components
- Single Responsibility Principle

#### Refactoring 2: Error Handling Standardization
**Problem:** 3 different error handling patterns across routers:
- PDF router: try/except + log_service + HTTPException
- TEMU router: HTTPException only, no error logging
- CSV router: HTTPException + error logging, no traceback capture

**Solution:** Create decorator for consistent error handling
```python
# modules/shared/errors/handler.py
@handle_api_errors("job_type")
async def endpoint_func(job_id: str = None):
    # Decorator handles try/except, logging, HTTPException formatting
    return result
```

**Benefit:**
- Eliminate 50+ lines of duplicate try/except blocks
- Full stack traces logged to database
- Consistent JSON error responses with type info
- ~15 endpoints standardized

---

### Phase 2: Configuration & Validation (Follow-up)
**Focus:** Runtime configuration, fail-fast patterns
**Effort:** 1 day

#### Refactoring 3: Logging Configuration Module
Extract hardcoded values (`10*1024*1024`, `backupCount=5`) to environment-based config.

#### Refactoring 4: Pydantic Job Validation
Convert `workers/job_models.py` from dataclasses to Pydantic for runtime validation.

#### Refactoring 5: Startup Configuration Validation
Add fail-fast checks at startup (env vars, DB connectivity, directories).

---

### Phase 3: Code Duplication Reduction (Optional)
**Focus:** Frontend & backend DRY improvements
**Effort:** 2 days

#### Refactoring 6: Frontend API Client
Extract duplicate fetch logic from `pdf.js`, `temu.js`, `csv.script.js` into shared `api-client.js`.

#### Refactoring 7: Repository Query Helpers
Add generic `find_one_by()` and `find_all_by()` to `BaseRepository`.

#### Refactoring 8-10: Minor Extractions
- CSV report rendering logic to service
- Frontend status badge helper
- Additional small improvements

---

## Critical Files to Modify

### Phase 1 (API Gateway + Error Handling)
**Modified:**
- `/home/chx/entwicklung/main.py` - Extract routers, reduce from 419 to ~150 lines
- `/home/chx/entwicklung/modules/pdf_reader/router.py` - Apply error decorator
- `/home/chx/entwicklung/modules/temu/router.py` - Apply error decorator
- `/home/chx/entwicklung/modules/csv_verarbeiter/router.py` - Apply error decorator

**New Files:**
- `/home/chx/entwicklung/modules/shared/routers/static_router.py` - Static file serving
- `/home/chx/entwicklung/modules/shared/errors/handler.py` - Error handling decorator
- `/home/chx/entwicklung/workers/router.py` (optional) - Job management API
- `/home/chx/entwicklung/modules/shared/routers/log_router.py` (optional) - Logging API

### Phase 2 (Configuration & Validation)
- `/home/chx/entwicklung/modules/shared/logging/config.py` (new)
- `/home/chx/entwicklung/modules/shared/logging/logger.py` (refactor)
- `/home/chx/entwicklung/workers/job_models.py` (dataclass → Pydantic)
- `/home/chx/entwicklung/modules/shared/startup/validation.py` (new)

### Phase 3 (DRY Improvements)
- `/home/chx/entwicklung/frontend/components/api-client.js` (new)
- Module frontend files: `pdf.js`, `temu.js`, `csv.script.js` (refactor)
- `/home/chx/entwicklung/modules/shared/database/repositories/base.py` (extend)
- Repository files in `modules/shared/database/repositories/temu/` (refactor)

---

## Existing Patterns to Reuse

1. **BaseRepository** (`modules/shared/database/repositories/base.py`)
   - Already provides `_fetch_one()`, `_fetch_all()`, transaction context managers
   - Extend with `find_one_by()` and `find_all_by()` helpers

2. **BaseWorkflowService** (`modules/shared/services/base_workflow_service.py`)
   - DI pattern for job/log services
   - Reuse for error handling decorator dependencies

3. **LogService** (`modules/shared/logging/log_service.py`)
   - Already captures job logs to database
   - Integrate with error handler decorator for traceback capture

4. **FastAPI Router Pattern**
   - All modules follow `router.py` → `APIRouter()` → `main.py` inclusion
   - Apply same pattern for new static/job/log routers

5. **Frontend Component Pattern**
   - Shared components: `nav-loader.js`, `ui-helpers.js`, `progress-helper.js`
   - Add `api-client.js` following same pattern

---

## Verification Strategy

### 1. Unit Testing
- Create tests for error handler decorator before refactoring
- Test static router path traversal protection
- Test Pydantic job validation edge cases

### 2. Integration Testing
Run existing workflow tests after each phase:
- Order sync workflow (5 steps)
- Inventory sync workflow (4 steps)
- PDF processing (invoice + advertising)
- CSV processing (JTL → DATEV conversion)

### 3. Manual Verification
- **Frontend:** Test all module frontends in browser
  - PDF Reader: Upload invoices, process ads
  - CSV Verarbeiter: Upload CSVs, view reports
  - TEMU: View jobs, trigger workflows
- **API:** Test endpoints via Swagger docs (`/docs`)
- **Static Files:** Verify CSS/JS/icons load correctly
- **Error Handling:** Trigger errors, check log database entries

### 4. Deployment Verification
- Deploy to development port 8888 first
- Run parallel to production (port 8000)
- Monitor logs for errors
- Test PM2 restart behavior

### 5. Rollback Plan
- Git feature branch for each phase
- Can revert individual commits
- Production port 8000 untouched until verified

---

## Implementation Steps (Phase 1)

### Step 1: Error Handler Decorator (1-2 hours)
1. Create `modules/shared/errors/handler.py`
2. Implement `@handle_api_errors()` decorator
3. Write unit tests for decorator
4. Apply to PDF router endpoints (test first)
5. Apply to TEMU router endpoints
6. Apply to CSV router endpoints
7. Verify all endpoints still work

### Step 2: Static File Router (2-3 hours)
1. Create `modules/shared/routers/static_router.py`
2. Use FastAPI `StaticFiles` for `/static/`, `/icons/`, `/components/`
3. Implement module-specific file serving with validation
4. Update `main.py` to include static router
5. Remove old static endpoints from `main.py`
6. Test all frontend pages load correctly

### Step 3: Job & Log Router Extraction (Optional, 1-2 hours)
1. Create `workers/router.py` (move job endpoints)
2. Create `modules/shared/routers/log_router.py` (move log endpoints)
3. Update `main.py` to include new routers
4. Test job management and log endpoints

### Step 4: Verification (1 hour)
1. Run all workflow tests
2. Manual browser testing
3. Check log database for proper error capture
4. Review `main.py` - should be ~150 lines

---

## Success Metrics

### Phase 1
- ✅ `main.py` complexity reduced by 60% (419 → ~150 lines)
- ✅ All 15+ API endpoints use consistent error handling
- ✅ Zero path traversal vulnerabilities (FastAPI StaticFiles)
- ✅ 100% test coverage for new routers
- ✅ All existing workflows pass integration tests

### Phase 2
- ✅ Zero hardcoded configuration values in logging
- ✅ Job validation catches invalid intervals at API level
- ✅ Application fails fast on misconfiguration (startup validation)

### Phase 3
- ✅ Frontend fetch logic reduced by 80+ lines
- ✅ Repository query patterns DRY (50+ lines removed)
- ✅ Consistent status badge rendering across modules

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Breaking API contracts | HIGH | Feature branch + parallel deployment (port 8888) |
| Frontend breaks due to new static routes | MEDIUM | Test all modules manually before production |
| Error decorator introduces performance overhead | LOW | Minimal - async/await preserved, no I/O in decorator |
| Hardcoded paths break in new router structure | MEDIUM | Use `Path(__file__).parent` for relative paths |
| PM2 restart fails with new structure | MEDIUM | Test with `pm2 restart temu-api` on dev first |

---

## Alternatives Considered

### Alternative 1: Keep current structure, only add error decorator
**Pros:** Minimal changes, lower risk
**Cons:** Doesn't address main.py complexity (419 lines)
**Decision:** Rejected - API gateway separation is high-value, low-risk

### Alternative 2: Full microservices split (separate FastAPI apps per module)
**Pros:** Ultimate separation of concerns
**Cons:** Overkill for current scale, deployment complexity
**Decision:** Rejected - monorepo pattern working well

### Alternative 3: Extract ALL endpoints to routers (not just static/job/log)
**Pros:** Maximum modularity
**Cons:** Module routers already exist, no added value
**Decision:** Rejected - current module structure is correct

---

## Post-Refactoring Actions

1. **Update Documentation**
   - Update `docs/ARCHITECTURE/code_structure.md` with new router structure
   - Document error handling decorator pattern
   - Add logging configuration to `docs/DEPLOYMENT/architecture.md`

2. **Update AI Guide**
   - Add error decorator usage to `AI_GUIDE.md`
   - Document static router pattern
   - Update main.py structure description

3. **Create ADR (Architecture Decision Record)**
   - Document why API gateway was split
   - Document error handling standardization rationale

4. **Code Review Checklist**
   - [ ] All tests pass (unit + integration)
   - [ ] No hardcoded paths or magic numbers
   - [ ] Swagger docs updated
   - [ ] Error responses consistent
   - [ ] Log database captures all errors

---

## Timeline Estimate

**Phase 1 (Recommended):** 1 working day
- Error handler: 2 hours
- Static router: 3 hours
- Job/log routers: 2 hours (optional)
- Testing: 1 hour

**Phase 2:** 1 working day
**Phase 3:** 2 working days

**Total (All Phases):** 4 working days

---

## User Decisions ✅

1. **Implementation Scope:** Phase 1 - API Gateway + Error Handling
2. **Router Extraction:** Extract ALL (static + job + log routers) → main.py to ~150 lines
3. **Testing Strategy:** Test after each refactoring step
4. **Deployment:** Feature branch → dev port 8888 → approval → production port 8000

---

## Recommendation

**Start with Phase 1 (API Gateway + Error Handling)** for these reasons:
- ✅ Highest impact (60% complexity reduction in main.py)
- ✅ Lowest risk (isolated changes, non-breaking)
- ✅ Improves security (FastAPI StaticFiles)
- ✅ Foundation for Phase 2/3 (error handling used across system)
- ✅ Can be completed in 1 day

If Phase 1 goes smoothly, proceed with Phase 2 for complete configuration management.

Phase 3 is optional - nice-to-have DRY improvements that can be done incrementally.
