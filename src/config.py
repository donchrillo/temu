"""
config.py – Zentrale Konfigurationsdatei für Pfade und Initialisierung

Diese Datei definiert alle globalen Konstanten und Pfade, die im Projekt verwendet werden.
Die Pfade werden immer relativ zum App-Root (`/app`) erstellt.
"""

# ========== 📦 Standard-Module ==========
import os  # Für Pfadoperationen, Umgebungsvariablen etc.

# ========== 🔐 Externe Module ==========
from dotenv import load_dotenv  # Zum Einlesen der Umgebungsvariablen aus einer .env-Datei (nur für SQL-Zugang)

# ========== 📥 Umgebungsvariablen laden ==========
load_dotenv()

# ========== 🌐 SQL-Verbindungsdaten ==========
# Diese Daten können weiterhin in der .env liegen, falls nötig
SQL_SERVER = os.getenv("SQL_SERVER", "localhost")
SQL_PORT   = os.getenv("SQL_PORT", "1433")
SQL_DB     = os.getenv("SQL_DB", "datenbank")
SQL_USER   = os.getenv("SQL_USER", "benutzer")
SQL_PASS   = os.getenv("SQL_PASS", "passwort")

# ========== 🗂️ Projektverzeichnisse ==========
# === Verzeichnisstruktur ===
APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATEN_ROOT = os.path.join(APP_ROOT, "daten")

# Unterverzeichnisse
ORDNER_EINGANG = os.path.join(DATEN_ROOT, "eingang")
ORDNER_AUSGANG = os.path.join(DATEN_ROOT, "ausgang")
ORDNER_EINGANG_ARCHIV = os.path.join(DATEN_ROOT, "archive")
ORDNER_AUSGANG_ARCHIV = os.path.join(DATEN_ROOT, "archive")
ORDNER_LOG     = os.path.join(DATEN_ROOT, "log")
ORDNER_ARCHIV  = os.path.join(DATEN_ROOT, "archive")
TMP_ORDNER     = os.path.join(DATEN_ROOT, "tmp")

def ensure_directories() -> None:
    """
    Erstellt alle notwendigen Verzeichnisse für die Projektstruktur.

    Diese Funktion sorgt beim Import dieses Moduls automatisch dafür,
    dass folgende Ordner vorhanden sind:
    - eingang/: CSV- oder ZIP-Dateien, die verarbeitet werden sollen
    - archive/: Sicherung verarbeiteter Dateien
    - tmp/: Entpacken von ZIP-Dateien
    - ausgang/: Ergebnisse der Verarbeitung (neue CSV-Dateien)
    - log/: Logs und Reports zur Nachverfolgung

    Die Funktion nutzt `os.makedirs(..., exist_ok=True)`, um sicherzustellen,
    dass es bei mehrfachen Aufrufen nicht zu Fehlern kommt.
    """
    ordner_liste = [
        DATEN_ROOT,        
        ORDNER_EINGANG,
        ORDNER_AUSGANG,
        ORDNER_LOG,
        ORDNER_ARCHIV,
        TMP_ORDNER,
    ]

    for pfad in ordner_liste:
        os.makedirs(pfad, exist_ok=True)

# Beim Modulimport direkt die Verzeichnisse sicherstellen
ensure_directories()
