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

    @router.get("/manifest.json")
    async def get_manifest():
        """PWA Manifest"""
        # React doesn't use manifest.json the same way
        return {"error": "manifest.json nicht mehr verfügbar"}

    return router
