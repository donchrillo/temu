# Systemd Cutover Runbook (Frontend 3000 + Backend 8000 + HTTPS)

Ziel:
- Altes Legacy-System (Vanilla JS, Port 8000) sauber abschalten
- Neues FastAPI-Backend auf Port 8000 unter `systemd` betreiben
- React-Frontend als eigener Prozess auf Port 3000 unter `systemd` betreiben
- Alles extern über HTTPS ausliefern

Empfohlener Stack für diesen Cutover:
- Prozessmanager: `systemd`
- Webserver + TLS: `Caddy`

---

## 1) Altservice identifizieren und stoppen

```bash
# Prozesse/Units auf Port 8000 prüfen
sudo ss -ltnp | grep :8000 || true
sudo lsof -iTCP:8000 -sTCP:LISTEN -P -n || true

# Kandidaten für alte Unit suchen
systemctl list-unit-files --type=service | grep -Ei "temu|erp|legacy|old|node|js"
```

Wenn der alte Service gefunden ist (Beispiel: `temu-legacy.service`):

```bash
sudo systemctl stop temu-legacy.service
sudo systemctl disable temu-legacy.service
sudo systemctl status temu-legacy.service --no-pager
```

Optional maskieren (damit er nicht versehentlich startet):

```bash
sudo systemctl mask temu-legacy.service
```

---

## 2) Neues Backend als `systemd`-Service aktivieren

Template im Repo:
- `deploy/systemd/temu-api.service.template`

Installation:

```bash
sudo cp deploy/systemd/temu-api.service.template /etc/systemd/system/temu-api.service
sudo systemctl daemon-reload
sudo systemctl enable --now temu-api.service
sudo systemctl status temu-api.service --no-pager
```

Logs:

```bash
journalctl -u temu-api.service -f
```

Health-Check lokal:

```bash
curl -fsS http://127.0.0.1:8000/api/health
```

---

## 3) React Frontend produktiv bauen + als Service starten

```bash
cd /home/chx/jtl_erp/frontend-react
npm ci
npm run build
```

Build-Ziel:
- `/home/chx/jtl_erp/frontend-react/dist`

Template im Repo:
- `deploy/systemd/temu-frontend.service.template`

Installation:

```bash
sudo cp deploy/systemd/temu-frontend.service.template /etc/systemd/system/temu-frontend.service
sudo systemctl daemon-reload
sudo systemctl enable --now temu-frontend.service
sudo systemctl status temu-frontend.service --no-pager
```

Check lokal:

```bash
curl -I http://127.0.0.1:3000
```

---

## 4) Caddy für HTTPS + Reverse Proxy konfigurieren

Template im Repo:
- `deploy/caddy/Caddyfile.template`

Wichtig:
- Domain in Caddyfile anpassen (`erp.example.de`)
- DNS A/AAAA auf den Server zeigen lassen

Install/Update:

```bash
sudo cp deploy/caddy/Caddyfile.template /etc/caddy/Caddyfile
sudo caddy fmt --overwrite /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
sudo systemctl status caddy --no-pager
```

---

## 5) Go-Live Verifikation

```bash
# HTTPS erreichbar
curl -I https://erp.example.de

# API über HTTPS erreichbar
curl -fsS https://erp.example.de/api/health

# Frontend intern erreichbar
curl -I http://127.0.0.1:3000
```

Browser-Checks:
- Frontend lädt ohne Mixed-Content-Warnungen
- API-Calls gehen auf `/api/*` über HTTPS
- WebSocket-Verbindung auf `/ws/*` funktioniert

---

## 6) Rollback (wenn nötig)

```bash
sudo systemctl stop temu-api.service
sudo systemctl stop temu-frontend.service
# optional: alten Service wieder aktivieren
sudo systemctl unmask temu-legacy.service || true
sudo systemctl enable --now temu-legacy.service
```

---

## Hinweise

- FastAPI läuft intern auf `127.0.0.1:8000`.
- React läuft intern auf `127.0.0.1:3000`.
- Extern wird nur Caddy (443) exponiert.
- Für Produktivbetrieb sollte `--reload` **nicht** in `ExecStart` verwendet werden.
- Falls Node/Legacy-Prozesse noch laufen, diese zusätzlich mit `ps aux | grep -Ei "node|legacy"` prüfen.
