"""
verarbeitung_logik.py – Zentrale Prüf- und Verarbeitungsfunktionen für CSV-Zeilen

Dieses Modul enthält die Kernlogik zur Bewertung und Anpassung von Zeilen innerhalb
einer Amazon/DATEV-kompatiblen CSV-Datei. Dabei wird geprüft:
- ob gültige Amazon-Bestellnummern vorhanden sind
- ob ein kritisches Gegenkonto (0–20) vorliegt
- ob Zusatzinformationen für die Nachverfolgbarkeit ergänzt wurden

Die Verarbeitung erfolgt vollständig auf Basis eines übergebenen DataFrames.
"""

import pandas as pd
import logging
from functools import lru_cache

from verarbeitung_validation import ist_amazon_bestellnummer, ist_kritisches_gegenkonto
from sql import hole_kundennummer


def ist_datei_leer(df: pd.DataFrame, dateiname: str, report) -> bool:
    """
    Prüft, ob ein DataFrame leer ist und erzeugt bei Bedarf einen Fehlerbericht.

    Diese Funktion dient der Absicherung gegen Dateien, die nach der Metazeile
    keine verwertbaren Daten enthalten.

    Args:
        df (pd.DataFrame): Der eingelesene CSV-Inhalt ab Zeile 2 (ohne Metazeile)
        dateiname (str): Ursprünglicher Name der verarbeiteten Datei
        report: Instanz des ReportCollector für Logging und Auswertung

    Returns:
        bool: True, wenn Datei leer ist, False sonst
    """
    if df.empty:
        meldung = "Datei enthält keine Datenzeilen – nur Metadaten & Header"
        logging.error(f"{dateiname}: {meldung}")
        report.log_fehler(dateiname, meldung)
        report.log_report(dateiname, 0, 0, False, False)
        return True
    return False


def pruefe_pflichtspalten(df: pd.DataFrame, dateiname: str, report) -> bool:
    """
    Validiert, ob alle für die Verarbeitung benötigten Spalten vorhanden sind.

    Erwartet werden:
    - "Belegfeld 1" → Amazon-Bestellnummer
    - "Gegenkonto (ohne BU-Schlüssel)" → zur Prüfung kritischer Konten

    Args:
        df (pd.DataFrame): DataFrame der CSV-Daten
        dateiname (str): Ursprünglicher Dateiname
        report: Instanz des ReportCollector für Logging und Auswertung

    Returns:
        bool: True, wenn alle Spalten vorhanden sind, sonst False
    """
    erforderlich = ["Belegfeld 1", "Gegenkonto (ohne BU-Schlüssel)"]
    fehlen = [col for col in erforderlich if col not in df.columns]
    if fehlen:
        meldung = f"❌ Fehlende Spalten: {', '.join(fehlen)}"
        logging.error(f"{dateiname}: {meldung}")
        report.log_fehler(dateiname, meldung)
        return False
    return True


def initialisiere_spalten(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ergänzt Zusatzspalten für Prüfmarken, falls sie fehlen.

    Diese Felder werden verwendet, um Verarbeitungsvermerke in der Datei zu hinterlassen.

    Args:
        df (pd.DataFrame): Eingelesene CSV-Daten

    Returns:
        pd.DataFrame: DataFrame mit garantierten Zusatzspalten
    """
    if "Zusatzinformation - Art 1" not in df.columns:
        df["Zusatzinformation - Art 1"] = ""
    if "Zusatzinformation- Inhalt 1" not in df.columns:
        df["Zusatzinformation- Inhalt 1"] = ""
    return df


@lru_cache(maxsize=1024)
def hole_kundennummer_cached(order_id: str):
    """
    Zwischengespeicherte Version der SQL-Abfrage, um dieselbe Order-ID mehrfach zu vermeiden.

    Args:
        order_id (str): Amazon-Bestellnummer

    Returns:
        str | None: Kundennummer oder None
    """
    return hole_kundennummer(order_id)


def pruefe_und_verarbeite_zeilen(
    df: pd.DataFrame,
    dateiname: str,
    heute: str,
    gegenkonto_dateien: list,
    report
) -> tuple[int, int, bool]:
    """
    Kernfunktion zur Verarbeitung aller relevanten CSV-Zeilen.

    Diese Funktion durchsucht jede Zeile nach Amazon-Bestellnummern,
    führt ggf. SQL-Abfragen zur Kundennummer durch und protokolliert
    alle Änderungen. Zusätzlich wird geprüft, ob ein kritisches Gegenkonto vorliegt.

    Args:
        df (pd.DataFrame): CSV-Daten ohne Metazeile
        dateiname (str): Name der verarbeiteten Datei
        heute (str): Tagesdatum als ISO-String (YYYY-MM-DD)
        gegenkonto_dateien (list): Wird erweitert, wenn Datei kritische Konten enthält
        report: Instanz von ReportCollector

    Returns:
        tuple:
            ersetzt (int): Anzahl ersetzter Amazon-IDs
            offen (int): Anzahl nicht gefundener IDs
            hat_kritisches_konto (bool): True, wenn kritisches Gegenkonto erkannt wurde
    """
    ersetzt = 0
    offen = 0
    hat_kritisches_konto = False

    # Filtert nur die Zeilen mit erkennbaren Amazon-Bestellnummern
    maske_orderid = df["Belegfeld 1"].apply(ist_amazon_bestellnummer)
    df_orderid = df[maske_orderid].copy()

    def ersetze_orderid(row):
        beleg = row["Belegfeld 1"].strip()
        try:
            kundennr = hole_kundennummer_cached(beleg)
            if kundennr:
                # Daten direkt im Haupt-DF aktualisieren
                df.at[row.name, "Belegfeld 1"] = kundennr
                df.at[row.name, "Zusatzinformation - Art 1"] = "Prüfung"
                df.at[row.name, "Zusatzinformation- Inhalt 1"] = f"AmazonOrderID-Check durchgeführt am {heute}"
                report.log_aenderung(dateiname, row.name + 3, beleg, kundennr)
                return "ok"
            else:
                report.log_nicht_gefunden(dateiname, row.name + 3, beleg)
                return "offen"
        except Exception as e:
            logging.error(f"❌ SQL-Fehler bei Order-ID {beleg}: {e}")
            return "fehler"

    # Anwenden der Ersetzungsfunktion auf jede Amazon-Zeile
    status_liste = df_orderid.apply(ersetze_orderid, axis=1)

    # Zählung der Statuswerte
    ersetzt = len(status_liste[status_liste == "ok"])
    offen = len(status_liste[status_liste == "offen"])

    # Prüfung auf kritisches Gegenkonto
    kritisch = df["Gegenkonto (ohne BU-Schlüssel)"].apply(ist_kritisches_gegenkonto)
    if kritisch.any():
        hat_kritisches_konto = True
        if dateiname not in gegenkonto_dateien:
            gegenkonto_dateien.append(dateiname)

    return ersetzt, offen, hat_kritisches_konto
