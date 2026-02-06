"""
log_helper.py – Initialisiert das Logging-System für das Projekt.

Dieses Modul stellt eine zentrale Funktion `init_logger()` bereit,
die ein konsistentes Logging-Format definiert und sowohl in die Konsole
als auch in eine Logdatei schreibt.

Neu: Optionales `force=True`, damit auch gezielt neu initialisiert werden kann.
"""

import logging
import os
from datetime import datetime
from config import ORDNER_LOG

def init_logger(force: bool = False) -> str:
    """
    Initialisiert den globalen Logger für das gesamte Projekt.
    Verhindert doppelte Handler bei Streamlit-Reloads.

    Args:
        force (bool): Wenn True, werden bestehende Handler entfernt und neu initialisiert.

    Returns:
        str: Pfad zur erzeugten Logdatei oder leerer String, wenn bereits initialisiert.
    """
    if logging.getLogger().handlers and not force:
        return ""

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    logdatei = os.path.join(ORDNER_LOG, f"log_{timestamp}.txt")

    logging.basicConfig(
        level=logging.INFO,
        format="[{asctime}] {levelname} - {message}",
        style="{",
        handlers=[
            logging.FileHandler(logdatei, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

    logging.info("✅ Logger erfolgreich initialisiert.")

    return logdatei
