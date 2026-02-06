"""
verarbeitung_io.py – Funktionen zum Einlesen und Schreiben von CSV-Dateien mit Metadaten

Dieses Modul behandelt:
- das sichere Auslesen der ersten Zeile (Metadaten) einer CSV-Datei
- das Laden des Datenbereichs in einen DataFrame
- das Schreiben einer bearbeiteten CSV-Datei mit Metazeile
"""

import os
import pandas as pd
import logging
from datetime import datetime

from config import ORDNER_AUSGANG


def lese_metazeile(pfad: str, dateiname: str, report) -> str:
    """
    Liest die erste Zeile (Metadaten) einer CSV-Datei.

    Die Metazeile enthält systemtechnische Informationen und muss beim Speichern
    der bearbeiteten Datei erhalten bleiben.

    Args:
        pfad (str): Absoluter Pfad zur CSV-Datei
        dateiname (str): Ursprünglicher Dateiname zur Protokollierung
        report: Instanz des ReportCollector zur Fehlerprotokollierung

    Returns:
        str: Die gelesene Metazeile oder ein leerer String bei Fehler
    """
    try:
        with open(pfad, "r", encoding="cp1252") as f:
            return f.readline().strip()
    except Exception as e:
        meldung = f"Fehler beim Lesen der Metazeile: {e}"
        logging.error(f"{dateiname}: {meldung}")
        report.log_fehler(dateiname, meldung)
        report.log_report(dateiname, 0, 0, False, False)
        return ""


def lade_csv_daten(pfad: str, dateiname: str, report) -> tuple[pd.DataFrame, bool]:
    """
    Liest eine CSV-Datei ab der zweiten Zeile (Datenzeilen) in einen DataFrame.

    Diese Funktion überspringt die Metazeile (erste Zeile) und wandelt
    alle Spalten in Strings. Fehlerhafte oder leere Dateien werden erkannt
    und entsprechend im Report erfasst.

    Args:
        pfad (str): Absoluter Pfad zur CSV-Datei
        dateiname (str): Dateiname für Logging und Reporting
        report: Instanz des ReportCollector zur Fehlerprotokollierung

    Returns:
        tuple:
            pd.DataFrame: Geladene Datenzeilen (ohne Metazeile)
            bool: True, wenn erfolgreich geladen, False bei Fehler
    """
    try:
        df = pd.read_csv(pfad, sep=";", dtype=str, encoding="cp1252", skiprows=1)

        if df.empty:
            meldung = "Datei enthält keine Datenzeilen – nur Metadaten & Header"
            logging.error(f"{dateiname}: {meldung}")
            report.log_fehler(dateiname, meldung)
            report.log_report(dateiname, 0, 0, False, False)
            return pd.DataFrame(), False

        return df, True

    except Exception as e:
        meldung = f"❌ Fehler beim CSV-Import ({dateiname}): {e}"
        logging.error(meldung)
        report.log_fehler(dateiname, f"CSV-Fehler: {e}")
        report.log_report(dateiname, 0, 0, False, False)
        return pd.DataFrame(), False


def schreibe_csv_mit_metazeile(df: pd.DataFrame, erste_zeile: str, zieldateiname: str) -> str:
    """
    Schreibt eine verarbeitete CSV-Datei mit Metadatenzeile als erste Zeile.

    Vorgehen:
    1. DataFrame ohne Metazeile wird temporär gespeichert
    2. Danach wird die finale Datei mit Metazeile + Inhalt erstellt
    3. Bei Problemen (z. B. Datei offen) wird ein Zeitstempel-Backup geschrieben

    Args:
        df (pd.DataFrame): Verarbeiteter CSV-Inhalt (ohne Metazeile)
        erste_zeile (str): Metadatenzeile aus dem Original
        zieldateiname (str): Zielname der Ausgabedatei

    Returns:
        str: Absoluter Pfad zur geschriebenen Datei
    """
    zwischenpfad = os.path.join(ORDNER_AUSGANG, f"temp_{zieldateiname}")
    zielpfad = os.path.join(ORDNER_AUSGANG, zieldateiname)

    # 📝 Schritt 1: Nur Daten in temporäre Datei schreiben
    df.to_csv(zwischenpfad, sep=";", index=False, encoding="cp1252")

    try:
        # 📝 Schritt 2: Metazeile + Inhalt in endgültige Datei schreiben
        with open(zielpfad, "w", encoding="cp1252") as out:
            out.write(erste_zeile + "\n")
            with open(zwischenpfad, "r", encoding="cp1252") as temp:
                out.write(temp.read())

    except PermissionError:
        # 📛 Fallback: Datei war evtl. noch in Excel geöffnet
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        fallback_name = f"{os.path.splitext(zieldateiname)[0]}_{timestamp}.csv"
        zielpfad = os.path.join(ORDNER_AUSGANG, fallback_name)

        with open(zielpfad, "w", encoding="cp1252") as out:
            out.write(erste_zeile + "\n")
            with open(zwischenpfad, "r", encoding="cp1252") as temp:
                out.write(temp.read())

        logging.warning(f"{zieldateiname}: Datei war geöffnet → gespeichert als {fallback_name}")

    # 🧹 Schritt 3: Temporäre Datei aufräumen
    try:
        os.remove(zwischenpfad)
    except FileNotFoundError:
        logging.warning(f"⚠️ Temp-Datei nicht gefunden: {zwischenpfad}")

    return zielpfad
