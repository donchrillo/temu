"""
Base Logger Factory - Generische Logger-Erstellung
Wird von Modul-spezifischen Loggern verwendet (temu, pdf_reader, etc.)
Funktioniert auch ohne DB-Verbindung.
"""
import logging
import sys
from pathlib import Path

def create_module_logger(
    module_name: str,
    log_subdir: str,
    console_level: int = logging.ERROR,
    file_level: int = logging.INFO,
    file_name: str = None
) -> logging.Logger:
    """
    Generische Logger Factory für Module
    
    Args:
        module_name: Name des Loggers (z.B. 'TEMU', 'PDF_READER')
        log_subdir: Unterverzeichnis in logs/ (z.B. 'temu', 'pdf_reader')
        console_level: Log Level für Console (default: ERROR)
        file_level: Log Level für File (default: INFO)
        file_name: Optional - Name der Log-Datei (default: {log_subdir}.log)
    
    Returns:
        Konfigurierter Logger mit Console + File Handler
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)  # Niedrigster Level, Handler filtern dann

    # Verhindere doppelte Handler
    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%d.%m.%Y %H:%M:%S'
    )

    # 1. Console Handler (stderr, default nur ERROR+)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. File Handler (logs/{log_subdir}/{file_name})
    # Go up to project root: modules/shared/logging/ -> modules/shared/ -> modules/ -> root/
    log_dir = Path(__file__).parent.parent.parent.parent / "logs" / log_subdir
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = file_name or f"{log_subdir}.log"
    file_handler = logging.FileHandler(log_dir / log_file, encoding='utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# ✅ Zentrale App Logger Instanz
# Diese wird von allen Modulen importiert, um Redundanz zu vermeiden
app_logger = create_module_logger('APP', 'app',
                                  console_level=logging.ERROR,
                                  file_level=logging.ERROR)