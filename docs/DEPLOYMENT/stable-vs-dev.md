# Stable vs Dev Workspace Workflow

Status: ACTIVE
Last updated: 2026-03-12

This document defines the local repository split on this machine:
- `~/jtl_erp` = stable runtime workspace
- `~/jtl_erp_dev` = development workspace

---

## 1. Purpose

Use separate local folders for:
- safe production-like operation
- isolated development and experiments

This prevents accidental deployment of untested work.

---

## 2. Folder Roles

### `~/jtl_erp` (stable)

Use this folder for:
- running stable services via `systemd`
- operating the currently approved version
- pulling only merged and validated changes

Expected runtime (stable):
- Backend: `127.0.0.1:8000` via `temu-api.service`
- Frontend process: `127.0.0.1:3000` via `temu-frontend.service`
- Public entrypoint: HTTPS `:443` via Caddy

### `~/jtl_erp_dev` (development)

Use this folder for:
- feature branches
- experiments and refactoring
- tests before PR

Expected runtime (development):
- API local dev server: `0.0.0.0:8888` (e.g. `./start_dev.sh`)
- Frontend dev server: `:3000` (or another free dev port if needed)

---

## 3. Promotion Path

Development flow:
1. Work in `~/jtl_erp_dev` on a feature branch.
2. Run tests/checks in dev context.
3. Push branch and open PR.
4. Merge to target branch on GitHub.
5. Pull merged changes into `~/jtl_erp`.
6. Restart/reload stable services only after validation.

Stable folder rule:
- Do not use `~/jtl_erp` for active experimentation.

---

## 4. Port and Service Rules

- Keep stable backend on `8000` (`systemd` service).
- Keep stable frontend behind Caddy and expose only HTTPS externally.
- Use `8888` for manual dev API runs.
- Avoid running competing processes on the same port as stable services.

If frontend dev needs `3000` while stable frontend is active on `3000`:
- stop `temu-frontend.service` temporarily, or
- run Vite on a different port in dev.

---

## 5. Quick Commands

Check stable services:
```bash
systemctl is-active caddy temu-api temu-frontend
```

Check relevant ports:
```bash
ss -ltnp | grep -E ':443|:8000|:8888|:3000'
```

Start dev API:
```bash
cd ~/jtl_erp_dev
./start_dev.sh
```

---

## 6. Rename Note

If your old development folder is currently `~/temu`, rename it to `~/jtl_erp_dev`:

```bash
mv ~/temu ~/jtl_erp_dev
```

After rename, verify Git still works:

```bash
git -C ~/jtl_erp_dev status
```
