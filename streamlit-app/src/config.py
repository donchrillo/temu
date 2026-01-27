"""
config.py – Zentrale Konfigurationsdatei für Pfade und Initialisierung

Diese Datei definiert alle globalen Konstanten und Pfade, die im Projekt verwendet werden.
Die Pfade sind relativ zum Projekt-Root aufgebaut und werden beim Import automatisch erstellt.
"""

from pathlib import Path

# === Basisverzeichnis (Projekt-Root) ermitteln ===
APP_ROOT = Path(__file__).resolve().parent.parent
DATEN_ROOT = APP_ROOT / "daten"

# === Unterverzeichnisse ===
ORDNER_EINGANG_RECHNUNGEN = DATEN_ROOT / "eingang" / "rechnungen"
ORDNER_EINGANG_WERBUNG = DATEN_ROOT / "eingang" / "werbung"
ORDNER_LOG = DATEN_ROOT / "log"
ORDNER_AUSGANG = DATEN_ROOT / "ausgang"
TMP_ORDNER = DATEN_ROOT / "tmp"

def ensure_directories() -> None:
    """Erstellt bei Bedarf die notwendigen Verzeichnisse für das Projekt."""
    ordner_liste = [
        DATEN_ROOT,
        ORDNER_EINGANG_RECHNUNGEN,
        ORDNER_EINGANG_WERBUNG,
        ORDNER_LOG,
        ORDNER_AUSGANG,
        TMP_ORDNER,
    ]
    for pfad in ordner_liste:
        pfad.mkdir(parents=True, exist_ok=True)

# Beim Modulimport direkt die Verzeichnisse sicherstellen
ensure_directories()
