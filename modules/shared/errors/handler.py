"""Error Handler Decorator für einheitliche API-Fehlerbehandlung"""

import time
import traceback
from functools import wraps
from typing import Callable

from fastapi import HTTPException

from modules.shared import log_service, app_logger


def handle_api_errors(component: str):
    """Decorator für einheitliche API-Fehlerbehandlung.
    
    Zentralisiert try/except-Blöcke und bietet:
    - Vollständige Stack Trace Erfassung
    - DB-Logging mit error_text
    - Konsistente JSON-Fehlerantworten
    - Async-Funktionen Unterstützung
    
    Args:
        component: Der Name der Komponente für das Logging (z.B. 'pdf_reader', 'temu')
    
    Usage:
        @handle_api_errors("pdf_reader")
        async def my_endpoint(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generiere job_id falls nicht vorhanden
            job_id = kwargs.get('job_id') or f"{component}_{int(time.time())}"
            
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # HTTPException nicht nochmal wrappen - direkt weitergeben
                raise
            except Exception as e:
                error_trace = traceback.format_exc()
                log_service.log(
                    job_id, 
                    component, 
                    "ERROR", 
                    str(e), 
                    error_text=error_trace
                )
                app_logger.error(
                    f"[{component}] {type(e).__name__}: {e}",
                    exc_info=True
                )
                raise HTTPException(
                    status_code=500, 
                    detail={
                        "error": str(e),
                        "component": component,
                        "job_id": job_id
                    }
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generiere job_id falls nicht vorhanden
            job_id = kwargs.get('job_id') or f"{component}_{int(time.time())}"
            
            try:
                return func(*args, **kwargs)
            except HTTPException:
                # HTTPException nicht nochmal wrappen - direkt weitergeben
                raise
            except Exception as e:
                error_trace = traceback.format_exc()
                log_service.log(
                    job_id, 
                    component, 
                    "ERROR", 
                    str(e), 
                    error_text=error_trace
                )
                app_logger.error(
                    f"[{component}] {type(e).__name__}: {e}",
                    exc_info=True
                )
                raise HTTPException(
                    status_code=500, 
                    detail={
                        "error": str(e),
                        "component": component,
                        "job_id": job_id
                    }
                )
        
        # Rückgabe basierend auf ob die Funktion async ist
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
