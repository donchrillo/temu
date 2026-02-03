"""
PDF Reader Module

PDF Upload, Verarbeitung und Analyse für:
- Werbung (Amazon Ads): Erste Seite extrahieren, Daten parsen, Excel-Export
- Rechnungen: Daten extrahieren, Excel-Export

Module-Struktur:
- router.py: FastAPI Endpoints
- services/: Business Logic (re-export von src/modules/pdf_reader/)
- frontend/: Modernes UI (Apple Style)
"""

from .router import router, get_router

__all__ = ["router", "get_router"]
__version__ = "1.0.0"
