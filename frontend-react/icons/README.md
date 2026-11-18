# App-Icons

Quellen der PWA-Icons in `frontend-react/public/` (Synchronisationspfeile (JTL ↔ temu), weiß auf `#007aff`). Einheitlicher Stil aller
Homelab-Apps, entworfen am 15.11.2026 in der toci-erp-Session (Vorbild: toci-erp, mietverwaltung).
`icon-maskable.svg` hat volle Fläche, das Motiv liegt in der sicheren Zone (Android schneidet zu);
daraus entsteht auch `apple-touch-icon.png` (iOS rundet selbst ab, Transparenz würde schwarz).

```bash
cd frontend-react
convert -background none -density 400 icons/icon.svg -resize 512x512 -depth 8 PNG32:public/icon-512.png
convert -background none -density 400 icons/icon.svg -resize 192x192 -depth 8 PNG32:public/icon-192.png
convert -background none -density 400 icons/icon.svg -resize 32x32 -depth 8 PNG32:public/favicon-32.png
convert -background none -density 400 icons/icon-maskable.svg -resize 512x512 -depth 8 PNG32:public/icon-maskable-512.png
convert -background none -density 400 icons/icon-maskable.svg -resize 180x180 -flatten -depth 8 PNG24:public/apple-touch-icon.png
```

Einbindung (Manifest, `index.html`, `no-cache`) nach Muster
`/home/chx/toci-erp/frontend/index.html`, `frontend/public/manifest.webmanifest` und
`backend/src/main.py` (`spa_fallback`).
