# TEMU ERP - Documentation Index

Central index for active project documentation.

This page is intended to stay short and reliable. If links here are outdated, fix this file first.

---

## Core Docs

- [ARCHITECTURE/](./ARCHITECTURE/) - Code structure, module boundaries, data flows
- [API/](./API/) - FastAPI and endpoint architecture
- [DATABASE/](./DATABASE/) - DB architecture, repositories, performance patterns
- [FRONTEND/](./FRONTEND/) - React frontend architecture and conventions
- [WORKFLOWS/](./WORKFLOWS/) - Job orchestration and scheduler concepts
- [DEPLOYMENT/](./DEPLOYMENT/) - Deployment and operations runbooks
- [DEPLOYMENT/stable-vs-dev.md](./DEPLOYMENT/stable-vs-dev.md) - local repo separation and promotion workflow (`jtl_erp` vs `jtl_erp_dev`)
- [PERFORMANCE/](./PERFORMANCE/) - Performance practices and monitoring
- [FIXES/](./FIXES/) - Consolidated fixes and lessons learned
- [SPECS/](./SPECS/) - Implementation specs and migration plans

---

## Root-Level Docs

- [AGENT_CHANGES.md](./AGENT_CHANGES.md) - chronological change log from coding/documentation agents
- [VISION_2026.md](./VISION_2026.md) - strategic product direction and architecture target picture

---

## Active Specs

- [SPECS/REACT_MIGRATION.md](./SPECS/REACT_MIGRATION.md)
- [SPECS/TEMU_DATEV_INTEGRATION_PLAN.md](./SPECS/TEMU_DATEV_INTEGRATION_PLAN.md)

---

## Archive

Historical and snapshot documentation is collected in [Archiv/](./Archiv/).

Notable archived snapshots:

- [Archiv/PROJECT_ANALYSIS_2026.md](./Archiv/PROJECT_ANALYSIS_2026.md)
- [Archiv/technical_debt_analysis_de.md](./Archiv/technical_debt_analysis_de.md)

---

## Documentation Hygiene

- Keep architecture claims aligned with runtime entrypoints (`main.py`, `start_dev.sh`, `frontend-react/package.json`)
- Keep this index focused on active documents only
- Move obsolete or time-bound snapshot docs to `docs/Archiv/`
- Update `docs/AGENT_CHANGES.md` after meaningful documentation changes

*Last updated: 12. Mar 2026*
