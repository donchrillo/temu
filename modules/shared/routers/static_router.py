"""Static File Router - Zentrale Verwaltung statischer Dateien

Nutzt FastAPIs eingebaute StaticFiles für:
- /assets/ → frontend-react/dist/assets/ (React build)
- /icons/ → frontend-react/dist/icons/

Vorteile gegenüber manuellen Routen:
- Path Traversal Protection bereits eingebaut
- Bessere Performance (Caching, Range Requests)
- Weniger Code
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def get_static_router(app: FastAPI, frontend_dir: Path):
    """Erstellt und konfiguriert Static File Router.
    
    Args:
        app: Die FastAPI Anwendung
        frontend_dir: Path zum frontend Verzeichnis (React dist)
    
    Returns:
        Die konfigurierte FastAPI App (mit gemounteten StaticFiles)
    """
    
    # Validate frontend directory exists
    if not frontend_dir.exists():
        app_logger.warning(f"Frontend directory not found: {frontend_dir}")
        return app
    
    # Mount /assets/ → frontend_dir/assets/ (React build output)
    assets_dir = frontend_dir / "assets"
    if assets_dir.exists():
        app.mount(
            "/assets", 
            StaticFiles(
                directory=str(assets_dir),
                html=False
            ), 
            name="assets"
        )
    
    # Mount /icons/ → frontend_dir/icons/ (if exists)
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
    
    return app


# Import app_logger from shared
from modules.shared import app_logger
