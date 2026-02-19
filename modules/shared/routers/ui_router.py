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
    """Erstellt den UI Router mit allen Frontend-Routen."""
    
    router = APIRouter()
    
    @router.get("/")
    async def root():
        """Root Dashboard"""
        new_index = frontend_dir / "index-new.html"
        old_index = frontend_dir / "index.html"

        if new_index.exists():
            return FileResponse(str(new_index))
        elif old_index.exists():
            return FileResponse(str(old_index))
        else:
            return {
                "message": "TEMU ERP System Gateway",
                "version": "2.0.0",
                "modules": {
                    "pdf": "/pdf",
                    "temu": "/temu"
                },
                "docs": "/docs"
            }

    @router.get("/pdf")
    async def pdf_ui():
        """PDF-Reader UI"""
        pdf_html = BASE_DIR / "modules" / "pdf_reader" / "frontend" / "pdf.html"
        if not pdf_html.exists():
            raise HTTPException(status_code=404, detail="PDF Frontend not found")
        return FileResponse(str(pdf_html))

    @router.get("/temu")
    async def temu_ui():
        """TEMU Dashboard"""
        temu_html = BASE_DIR / "modules" / "temu" / "frontend" / "temu.html"
        if not temu_html.exists():
            raise HTTPException(status_code=404, detail="TEMU Frontend not found")
        return FileResponse(str(temu_html))

    @router.get("/csv")
    async def csv_ui():
        """CSV Verarbeiter UI"""
        csv_html = BASE_DIR / "modules" / "csv_verarbeiter" / "frontend" / "csv.html"
        if not csv_html.exists():
            raise HTTPException(status_code=404, detail="CSV Frontend not found")
        return FileResponse(str(csv_html))

    @router.get("/docs")
    async def docs_ui():
        """API Documentation UI"""
        docs_html = frontend_dir / "docs.html"
        if not docs_html.exists():
            raise HTTPException(status_code=404, detail="Docs Frontend not found")
        return FileResponse(str(docs_html))

    @router.get("/manifest.json")
    async def get_manifest():
        """PWA Manifest"""
        file_path = frontend_dir / "manifest.json"
        if file_path.exists():
            return FileResponse(str(file_path))
        return {"error": "manifest.json nicht gefunden"}

    return router
