"""Static File Router - Zentrale Verwaltung statischer Dateien

Nutzt FastAPIs eingebaute StaticFiles für:
- /static/ → frontend/
- /icons/ → frontend/icons/
- /components/ → frontend/components/

Vorteile gegenüber manuellen Routen:
- Path Traversal Protection bereits eingebaut
- Bessere Performance (Caching, Range Requests)
- Weniger Code
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


def get_static_router(app: FastAPI, frontend_dir: Path):
    """Erstellt und konfiguriert Static File Router.
    
    Args:
        app: Die FastAPI Anwendung
        frontend_dir: Path zum frontend Verzeichnis
    
    Returns:
        Die konfigurierte FastAPI App (mit gemounteten StaticFiles)
    """
    
    # Validate frontend directory exists
    if not frontend_dir.exists():
        app_logger.warning(f"Frontend directory not found: {frontend_dir}")
        return app
    
    # Mount /static/ → frontend/
    static_dir = frontend_dir
    if static_dir.exists():
        app.mount(
            "/static", 
            StaticFiles(
                directory=str(static_dir),
                html=False  # Keine automatische index.html Suche
            ), 
            name="static"
        )
    
    # Mount /icons/ → frontend/icons/
    icons_dir = frontend_dir / "icons"
    if icons_dir.exists():
        app.mount(
            "/icons", 
            StaticFiles(
                directory=str(icons_dir),
                html=False
            ), 
            name="icons"
        )
    
    # Mount /components/ → frontend/components/
    components_dir = frontend_dir / "components"
    if components_dir.exists():
        app.mount(
            "/components", 
            StaticFiles(
                directory=str(components_dir),
                html=True  # Allow serving index.html in component folders
            ), 
            name="components"
        )
    
    return app


def create_module_static_routes(app: FastAPI, base_dir: Path):
    """Erstellt Routen für modul-spezifische statische Dateien.
    
    Diese Funktion richtet spezielle Routen ein für:
    - modules/pdf_reader/frontend/*
    - modules/temu/frontend/*
    - modules/csv_verarbeiter/frontend/*
    
    Args:
        app: Die FastAPI Anwendung
        base_dir: Der Projekt-Root (wo main.py liegt)
    
    Returns:
        Die konfigurierte FastAPI App
    """
    from fastapi import HTTPException
    
    # Frontend directory
    frontend_dir = base_dir / "frontend"
    
    # Mapping von Prefixes zu Modul-Verzeichnissen
    module_dirs = {
        'pdf.': base_dir / "modules" / "pdf_reader" / "frontend",
        'temu.': base_dir / "modules" / "temu" / "frontend",
        'csv.': base_dir / "modules" / "csv_verarbeiter" / "frontend",
    }
    
    @app.get("/static/{filename}")
    async def serve_module_static(filename: str):
        """Serve static files from modules or frontend"""
        allowed_extensions = {'.css', '.js', '.json', '.png', '.ico', '.svg', '.woff', '.woff2', '.ttf'}

        # Check if file extension is allowed
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            raise HTTPException(status_code=403, detail="File type not allowed")

        # Try module-specific files first (pdf.css, temu.js, etc.)
        for prefix, module_dir in module_dirs.items():
            if filename.startswith(prefix):
                module_file = module_dir / filename
                if module_file.exists():
                    return FileResponse(str(module_file))
                # Try without prefix
                clean_filename = filename[len(prefix):]
                module_file = module_dir / clean_filename
                if module_file.exists():
                    return FileResponse(str(module_file))

        # Fallback to frontend directory
        if frontend_dir.exists():
            frontend_file = frontend_dir / filename
            if frontend_file.exists():
                return FileResponse(str(frontend_file))

        raise HTTPException(status_code=404, detail=f"Static file not found: {filename}")
    
    return app


# Import app_logger from shared
from modules.shared import app_logger
