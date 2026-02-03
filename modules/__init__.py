"""
Modules Package - Alle Anwendungsmodule

Dieses Package enthält alle Anwendungsmodule:
- shared: Gemeinsame Funktionen (Database, Logging, Config)
- temu: TEMU-JTL Connector
- pdf_reader: PDF Processor

Verwendung:
    from modules.shared import db_connect, create_module_logger
    from modules.temu import router as temu_router
    from modules.pdf_reader import router as pdf_router
"""

__version__ = "1.0.0"
