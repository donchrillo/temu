
# TOCI ERP - Vision 2026

**Status:** Strategic direction (living document)  
**Last updated:** 12. Mar 2026

---

## Mission

Build a lean, modular OMS/WMS that incrementally reduces and eventually removes operational dependency on JTL.

---

## Product Direction

### Channels

- TEMU is the active integration baseline
- Target multi-channel expansion: Amazon, eBay, Kaufland, Otto

### Core capabilities

- Order management across marketplaces
- Inventory synchronization and stock governance
- Shipping/tracking automation and status propagation
- Accounting and export tooling (including DATEV-oriented flows)

### Operating principles

- Modular backend services with explicit boundaries
- Single API gateway architecture in `main.py`
- Single active frontend in `frontend-react/`
- Raw-to-core data traceability for platform imports where practical

---

## 2026 Roadmap

### Phase 1: Platform stabilization (active)

- Consolidate monorepo architecture
- Keep FastAPI gateway + React 19 SPA as active baseline
- Harden module boundaries and shared infrastructure
- Continue migration work for `modules/temu_datev` into main architecture

### Phase 2: Multi-channel expansion

- Add channel adapters beyond TEMU
- Unify internal order/product abstractions across channels
- Expand dashboards and operations views for cross-channel monitoring

### Phase 3: Shipping autonomy and JTL reduction

- Increase direct shipping carrier integrations
- Introduce stronger internal WMS workflows (pick/pack/ship)
- Reduce legacy JTL bridge usage where safe and validated

---

## Architecture Guardrails

- No parallel standalone backend apps inside modules
- No second standalone frontend app for production paths
- Prefer shared configuration over hardcoded local paths
- Keep runtime data outside Git and aligned with `data/` conventions
- Treat strategy documents as directional; runtime entrypoints and active code remain authoritative

---

## Current Transition Focus

`modules/temu_datev/` is currently a transition area imported via subtree. The strategic target is:

1. Keep domain logic in `modules/temu_datev/`
2. Expose functionality through the main gateway and module router conventions
3. Integrate UI into `frontend-react/` instead of maintaining a second app

Reference implementation plan:

- `docs/SPECS/TEMU_DATEV_INTEGRATION_PLAN.md`

---

## Success Criteria for Vision Execution

- Core business flows are modular, testable, and observable
- New marketplace integrations fit the same internal contracts
- Operations are run from one coherent frontend and one coherent backend gateway
- JTL becomes an optional bridge, not a hard dependency