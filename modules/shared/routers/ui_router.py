"""
UI Router - Frontend Pages

Enthält alle UI-Routen für:
- PDF-Reader (/pdf)
- TEMU Dashboard (/temu)
- CSV Verarbeiter (/csv)
- API Documentation (/docs)
- Root (/)
- PWA Manifest (/manifest.json)
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

# Base directory for relative paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


def get_ui_router(frontend_dir: Path) -> APIRouter:
    """Erstellt den UI Router mit allen Frontend-Routen.
    
    Verwendet das React-Frontend aus frontend-react/dist/
    """
    
    router = APIRouter()
    
    # React Frontend Verzeichnis
    react_dist_dir = BASE_DIR / "frontend-react" / "dist"
    
    @router.get("/")
    async def root():
        """Root Dashboard - React Frontend"""
        if react_dist_dir.exists():
            return FileResponse(str(react_dist_dir / "index.html"))
        else:
            return {
                "message": "TEMU ERP System Gateway",
                "version": "2.0.0",
                "modules": {
                    "pdf": "/pdf",
                    "temu": "/temu",
                    "csv": "/csv"
                },
                "docs": "/docs",
                "error": "React Frontend nicht gefunden. Bitte 'npm run build' ausführen."
            }

    @router.get("/pdf")
    async def pdf_ui():
        """PDF-Reader UI - React Frontend"""
        if react_dist_dir.exists():
            return FileResponse(str(react_dist_dir / "index.html"))
        raise HTTPException(status_code=404, detail="React Frontend not found")

    @router.get("/temu")
    async def temu_ui():
        """TEMU Dashboard - React Frontend"""
        if react_dist_dir.exists():
            return FileResponse(str(react_dist_dir / "index.html"))
        raise HTTPException(status_code=404, detail="React Frontend not found")

    @router.get("/csv")
    async def csv_ui():
        """CSV Verarbeiter UI - React Frontend"""
        if react_dist_dir.exists():
            return FileResponse(str(react_dist_dir / "index.html"))
        raise HTTPException(status_code=404, detail="React Frontend not found")

    @router.get("/docs")
    async def docs_ui():
        """API Documentation UI"""
        docs_html = BASE_DIR / "docs.html"
        if docs_html.exists():
            return FileResponse(str(docs_html))
        raise HTTPException(status_code=404, detail="Docs Frontend not found")

    # PWA-Assets direkt aus dist/ ausliefern (manifest, service worker, icons).
    # vite-plugin-pwa generiert sw.js + workbox-<hash>.js neben das Manifest.
    @router.get("/manifest.webmanifest")
    async def pwa_manifest():
        f = react_dist_dir / "manifest.webmanifest"
        if not f.is_file():
            raise HTTPException(status_code=404)
        return FileResponse(str(f), media_type="application/manifest+json")

    @router.get("/sw.js")
    async def pwa_service_worker():
        f = react_dist_dir / "sw.js"
        if not f.is_file():
            raise HTTPException(status_code=404)
        return FileResponse(str(f), media_type="text/javascript")

    @router.get("/registerSW.js")
    async def pwa_register_sw():
        f = react_dist_dir / "registerSW.js"
        if not f.is_file():
            raise HTTPException(status_code=404)
        return FileResponse(str(f), media_type="text/javascript")

    @router.get("/workbox-{rest}")
    async def pwa_workbox(rest: str):
        f = react_dist_dir / f"workbox-{rest}"
        if not f.is_file() or react_dist_dir not in f.resolve().parents:
            raise HTTPException(status_code=404)
        return FileResponse(str(f), media_type="text/javascript")

    @router.get("/icon-{rest}")
    async def pwa_icon(rest: str):
        f = react_dist_dir / f"icon-{rest}"
        if not f.is_file() or react_dist_dir not in f.resolve().parents:
            raise HTTPException(status_code=404)
        return FileResponse(str(f))

    # SPA-Fallback fuer React-Router-Routen (/dashboard, /jobs/<id>, ...).
    # Muss am Ende stehen, damit die expliziten Routen oben Vorrang haben.
    # /api/* wird bewusst zu 404 statt index.html — sonst kriegen API-Tippfehler
    # HTML statt JSON.
    @router.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        if not react_dist_dir.exists():
            raise HTTPException(status_code=404, detail="React Frontend not found")
        return FileResponse(str(react_dist_dir / "index.html"))

    return router
