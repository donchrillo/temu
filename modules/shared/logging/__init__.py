"""Services Package - Zentrale Logger- und Service-Verwaltung"""

from .logger import create_module_logger
import logging

# ✅ Zentrale App Logger Instanz
# Diese wird von allen Modulen importiert, um Redundanz zu vermeiden
app_logger = create_module_logger('APP', 'app',
                                  console_level=logging.ERROR,
                                  file_level=logging.ERROR)

__all__ = ['app_logger']
