# Live-Gang Plan - Option B (Getrennte Ports + Nginx)

**Ziel-Architektur:**
```
Internet → Nginx (80/443) → localhost:8000 (API)
                         → localhost:3000 (React)
```

---

## Phase 1: Code synchronisieren

```bash
# Backup (empfohlen)
cp -r /home/chx/temu /home/chx/temu.backup.$(date +%Y%m%d)

# Git Pull
cd /home/chx/temu
git pull origin main

# Python Dependencies
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Phase 2: React-Frontend bauen

```bash
cd /home/chx/temu/frontend-react
npm install
npm run build
```

---

## Phase 3: PM2 Config erstellen

Datei: `/home/chx/temu/ecosystem.production.config.js`

```javascript
module.exports = {
  apps: [
    {
      name: "temu-api",
      script: "/home/chx/temu/.venv/bin/python3",
      args: "-m uvicorn main:app --host 0.0.0.0 --port 8000",
      cwd: "/home/chx/temu",
      env: { PYTHONPATH: "/home/chx/temu" },
      autorestart: true,
      max_memory_restart: "500M",
      error_file: "logs/pm2-error.log",
      out_file: "logs/pm2-out.log"
    },
    {
      name: "temu-react",
      script: "npx",
      args: "serve /home/chx/temu/frontend-react/dist -l 3000 -s",
      cwd: "/home/chx/temu/frontend-react",
      autorestart: true,
      error_file: "logs/pm2-react-error.log",
      out_file: "logs/pm2-react-out.log"
    }
  ]
};
```

```bash
pm2 delete temu-api 2>/dev/null
pm2 start /home/chx/temu/ecosystem.production.config.js
pm2 save
```

---

## Phase 4: Nginx Config

Datei: `/etc/nginx/sites-available/temu`

```nginx
server {
    listen 80;
    server_name 192.168.178.4;

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/temu /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Befehlsübersicht

| Schritt | Befehl |
|---------|---------|
| Git Pull | `cd /home/chx/temu && git pull` |
| React bauen | `cd /home/chx/temu/frontend-react && npm install && npm run build` |
| PM2 starten | `pm2 start ecosystem.production.config.js` |
| Nginx reload | `sudo systemctl reload nginx` |

---

## Notfall-Rollback

```bash
# Alten Zustand wiederherstellen
pm2 delete temu-api temu-react
cd /home/chx/temu
pm2 start ecosystem.config.js  # alter Config
sudo rm /etc/nginx/sites-enabled/temu
sudo systemctl reload nginx
```
