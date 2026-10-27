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
- Backend: `127.0.0.1:8401` via `temu-api.service`
- Frontend: built `frontend-react/dist`, served by the backend (`temu-api.service`); the old preview unit `temu-frontend.service` (port 3000) is disabled
- Public entrypoint: `https://temu.toci-lan.app` via Caddy (wildcard block `*.toci-lan.app`, Let's Encrypt; from outside via Cloudflare Tunnel + Access). DNS: nothing to do (Pi-hole answers `*.toci-lan.app`). The old `https://temu.lan` (`tls internal`) runs in parallel during the transition.

### `~/jtl_erp_dev` (development)

Use this folder for:
- feature branches
- experiments and refactoring
- tests before PR

Expected runtime (development):
- API local dev server: `0.0.0.0:8888` (e.g. `./start_dev.sh`)
- Frontend dev server: `:8501` (Vite, `strictPort`)

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

- Keep stable backend on `8401` (`systemd` service).
- Keep stable frontend behind Caddy and expose only HTTPS externally.
- Use `8888` for manual dev API runs.
- Avoid running competing processes on the same port as stable services.

Vite dev runs on `8501` (global scheme: Vite = backend + 100) and does not collide with the stable
backend on `8401`.

---

## 5. Quick Commands

Check stable services:
```bash
systemctl is-active caddy temu-api
```

Check relevant ports:
```bash
ss -ltnp | grep -E ':443|:8401|:8888|:8501'
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
