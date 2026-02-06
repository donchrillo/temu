"""
verarbeitung.py – Kernmodul zur Bearbeitung einer einzelnen CSV-Datei

Diese Datei enthält den Hauptprozess zum Einlesen, Prüfen und Verarbeiten
von Amazon-/DATEV-kompatiblen CSV-Dateien. Sie ruft dabei Hilfsfunktionen auf zur:

- Erkennung und Ersetzung von Amazon-Bestellnummern durch Kundennummern (via SQL)
- Prüfung kritischer Gegenkonten (z.B. Konten 0–20)
- Ergänzung von Prüfmarken (in Zusatzfeldern)
- Speicherung der Ergebnisse unter Beibehaltung einer Metazeile
- Protokollierung aller Ergebnisse und Fehler über den ReportCollector
"""

# ========== 📦 Imports ==========

import os
import logging
from datetime import date

from config import ORDNER_AUSGANG
from verarbeitung_io import lese_metazeile, lade_csv_daten, schreibe_csv_mit_metazeile
from verarbeitung_logik import (
    pruefe_und_verarbeite_zeilen,
    ist_datei_leer,
    pruefe_pflichtspalten,
    initialisiere_spalten
)
from report_collector import ReportCollector

# ========== 🚀 Hauptfunktion ==========

def verarbeite_datei(
    pfad: str,
    dateiname: str,
    gegenkonto_dateien: list,
    report: ReportCollector
) -> int:
    """
    Hauptverarbeitung einer CSV-Datei: Prüft, ersetzt und protokolliert Inhalte.

    Diese Funktion wird typischerweise aus einer Verarbeitungsroutine (z. B. `backend.py`)
    für jede einzelne CSV-Datei aufgerufen. Sie verarbeitet die Daten in mehreren Schritten:

    1. Einlesen der Metazeile (DATEV-Header)
    2. Laden der Daten ab Zeile 2 als DataFrame
    3. Prüfung auf leere Dateien oder fehlende Spalten
    4. Initialisierung von Zusatzfeldern für Prüfmarken
    5. Zeilenweise Prüfung auf Amazon-Bestellnummern und kritische Gegenkonten
    6. Speichern des Ergebnisses mit Metazeile
    7. Protokollieren aller Änderungen in einem zentralen ReportCollector

    Args:
        pfad (str): Absoluter Pfad zur CSV-Datei.
        dateiname (str): Ursprünglicher Dateiname (für Logging & Reporting).
        gegenkonto_dateien (list): Referenz auf Liste, die Dateinamen mit kritischen Konten sammelt.
        report (ReportCollector): Instanz zur Protokollierung aller Änderungen und Fehler.

    Returns:
        int: Anzahl erfolgreich ersetzter Amazon-Order-IDs.
    """

    logging.info(f"📂 Verarbeite Datei: {dateiname}")
    heute = date.today().isoformat()

    # === 1. Metazeile lesen (DATEV-Header mit z. B. Kanzlei-Nummer etc.)
    erste_zeile = lese_metazeile(pfad, dateiname, report)
    if not erste_zeile:
        return 0

    # === 2. CSV-Daten ab Zeile 2 laden
    df, erfolgreich = lade_csv_daten(pfad, dateiname, report)
    if not erfolgreich:
        return 0

    # === 3. Leere Datei erkennen
    if ist_datei_leer(df, dateiname, report):
        return 0

    # === 4. Pflichtfelder prüfen (z. B. "Belegfeld 1" und "Gegenkonto (ohne BU-Schlüssel)")
    if not pruefe_pflichtspalten(df, dateiname, report):
        return 0

    # === 5. Zusatzfelder sicherstellen (für Prüfmarken)
    df = initialisiere_spalten(df)

    # === 6. Zeilenweise Prüfung & Ersetzung durchführen
    ersetzt, offen, hat_kritisches_konto = pruefe_und_verarbeite_zeilen(
        df, dateiname, heute, gegenkonto_dateien, report
    )

    # === 7. Dateiname anpassen, wenn kritisches Gegenkonto enthalten
    zieldateiname = f"#_{dateiname}" if dateiname in gegenkonto_dateien else dateiname

    # === 8. Temporäre Datei speichern (reine Daten ohne Metazeile)
    zwischenpfad = os.path.join(ORDNER_AUSGANG, f"temp_{zieldateiname}")
    df.to_csv(zwischenpfad, sep=";", index=False, encoding="cp1252")

    # === 9. Finale CSV-Datei mit Metazeile schreiben
    zielpfad = schreibe_csv_mit_metazeile(df, erste_zeile, zieldateiname)
    logging.info(f"CSV gespeichert unter: {zielpfad}")

    # === 10. Temporäre Datei bereinigen
    if os.path.exists(zwischenpfad):
        os.remove(zwischenpfad)

    # === 11. Report aktualisieren
    report.log_report(dateiname, ersetzt, offen, hat_kritisches_konto, ersetzt > 0)

    # === 12. Logging für Übersicht
    logging.info(f"✅ Verarbeitet: {dateiname} → {zieldateiname}")
    logging.info(f"➡️ Ersetzungen: {ersetzt}, Offene IDs: {offen}, Gesamtzeilen: {len(df)}")

    return ersetzt
