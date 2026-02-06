"""
backend.py – Verarbeitung ausgewählter Eingabedateien (CSV oder ZIP)

Dieses Modul enthält die Hauptlogik zur Steuerung der Verarbeitung.
Es wird direkt von der Streamlit-Oberfläche (`gui.py`) aufgerufen und kümmert sich um:

- Auswahl und Verarbeitung von ZIP- oder CSV-Dateien
- Übergabe an die Detailverarbeitung (`verarbeite_datei`)
- Fortschrittsanzeige in der UI
- Archivierung verarbeiteter Dateien
- Export als ZIP inklusive Report und Logfile
"""

# ========== 📦 Imports ==========

import os
import shutil
import streamlit as st

import pandas as pd
import logging


from config import (
    ORDNER_EINGANG, ORDNER_EINGANG_ARCHIV,
    TMP_ORDNER, ORDNER_AUSGANG, ORDNER_AUSGANG_ARCHIV, ORDNER_LOG
)

from verarbeitung import verarbeite_datei
from report_collector import ReportCollector
from zip_handler import entpacke_zip, leere_ordner, zippe_csv_auswahl


# ========== 🔁 Hauptverarbeitungsfunktion ==========

def verarbeite_auswahl(dateien: list) -> None:
    """
    Führt die Verarbeitung für eine Liste ausgewählter Dateien durch.

    Diese Funktion verarbeitet jede Datei einzeln, entpackt ggf. ZIP-Dateien
    und ruft dann `verarbeite_datei` für jede CSV-Datei auf. Nach der Verarbeitung
    wird der Report gespeichert und in Streamlit eingeblendet.

    Args:
        dateien (list): Liste der Dateinamen im Eingangsordner.
    """
    report = ReportCollector()
    gegenkonto_dateien = []

    progress = st.progress(0)  # UI: Fortschrittsanzeige
    status = st.empty()       # UI: Textbereich für Datei-Status

    for i, dateiname in enumerate(dateien):
        pfad = os.path.join(ORDNER_EINGANG, dateiname)
        status.info(f"🔄 Verarbeite: `{dateiname}`")

        if dateiname.lower().endswith(".zip"):
            # === ZIP entpacken und enthaltene CSV-Dateien einzeln verarbeiten
            if not entpacke_zip(dateiname):
                st.error(f"❌ ZIP {dateiname} konnte nicht entpackt werden.")
                continue

            # 📭 Prüfen, ob überhaupt CSV-Dateien enthalten sind
            csvs = [csv for csv in os.listdir(TMP_ORDNER) if csv.lower().endswith(".csv")]
            if not csvs:
                meldung = f"📭 ZIP-Datei `{dateiname}` enthält keine CSV-Dateien."
                logging.warning(meldung)
                st.warning(meldung)
                continue

            for csv in csvs:
                ersetzt = verarbeite_datei(
                    os.path.join(TMP_ORDNER, csv),
                    csv,
                    gegenkonto_dateien,
                    report=report
                )

                if ersetzt == 0:
                    st.warning(f"{csv}: ⚠️ Keine Order-IDs ersetzt – Datei leer,fehlerhaft oder alles richtig!")
                else:
                    st.success(f"{csv}: ✅ {ersetzt} Ersetzungen durchgeführt.")


            leere_ordner(TMP_ORDNER)
            shutil.move(pfad, os.path.join(ORDNER_EINGANG_ARCHIV, dateiname))


        elif dateiname.lower().endswith(".csv"):
            ersetzt = verarbeite_datei(pfad, dateiname, gegenkonto_dateien, report=report)

            if ersetzt == 0:
                st.warning(f"{dateiname}: ⚠️ Keine Order-IDs ersetzt – Datei leer oder fehlerhaft?")
            else:
                st.success(f"{dateiname}: ✅ {ersetzt} Ersetzungen durchgeführt.")

            shutil.move(pfad, os.path.join(ORDNER_EINGANG_ARCHIV, dateiname))


        progress.progress((i + 1) / len(dateien))  # UI: Fortschritt aktualisieren

    # === Report abspeichern und in GUI anzeigen
    report_path = report.speichere()
    st.session_state.latest_report_path = report_path
    st.session_state.report_visible = True
    #st.success("✅ Alle Dateien verarbeitet.")



# ========== 📦 ZIP-Erstellung für Export ==========

def erstelle_zip_mit_beilagen(
    dateien: list,
    zip_name: str,
    include_report: bool = True,
    include_log: bool = True,
    report_path: str = None
) -> tuple[bool, str]:
    """
    Erstellt ein ZIP-Archiv mit ausgewählten CSV-Dateien und optional:
    - dem zuletzt erstellten Mini-Report
    - dem zuletzt generierten Logfile

    Args:
        dateien (list): Liste der Dateinamen im Ausgangsordner.
        zip_name (str): Dateiname der ZIP-Datei (ohne .zip).
        include_report (bool): Wenn True, wird der Report beigelegt.
        include_log (bool): Wenn True, wird das Logfile beigelegt.
        report_path (str): Pfad zur Reportdatei.

    Returns:
        tuple: (True, ZIP-Pfad) bei Erfolg, (False, Fehlermeldung) bei Fehler.
    """
    try:
        zip_pfad = os.path.join(ORDNER_AUSGANG, f"{zip_name.strip()}.zip")
        beilagen = []

        if include_report and report_path and os.path.isfile(report_path):
            beilagen.append(report_path)
            logging.info(f"📑 Mini-Report hinzugefügt: {report_path}")
        elif include_report:
            logging.warning("📑 Mini-Report wurde angefordert, aber nicht gefunden.")

        if include_log:
            logfiles = sorted(
                [f for f in os.listdir(ORDNER_LOG) if f.startswith("log_")], reverse=True
            )
            if logfiles:
                beilagen.append(os.path.join(ORDNER_LOG, logfiles[0]))
                logging.info(f"📝 Logfile hinzugefügt: {logfiles[0]}")
            else:
                logging.warning("📝 Logfile wurde angefordert, aber kein Logfile gefunden.")

        if zippe_csv_auswahl(dateien, zip_pfad, beilagen):
            logging.info(f"📦 ZIP erfolgreich erstellt: {zip_pfad}")


            # ➕ CSVs archivieren (verschieben nach ausgang/archiv)
            for datei in dateien:
                quellpfad = os.path.join(ORDNER_AUSGANG, datei)
                zielpfad = os.path.join(ORDNER_AUSGANG_ARCHIV, datei)
                try:
                    shutil.move(quellpfad, zielpfad)
                    logging.info(f"📁 Archiviert und verschoben: {datei}")
                except PermissionError:
                    logging.warning(f"⚠️ Datei konnte  nicht verschoben werden – bitte schließen: {datei}")
                    st.warning(f"⚠️ Datei konnte  nicht verschoben werden – bitte schließen: `{datei}`")

            
            return True, zip_pfad
        else:
            return False, "ZIP-Erstellung fehlgeschlagen."

    except Exception as e:
        logging.error(f"❌ Fehler beim ZIP-Export: {e}")
        return False, str(e)


# ========== 📊 Excel-Report (Mini-Report) laden ==========

def lade_report_sheets(pfad: str) -> dict:
    """
    Lädt die einzelnen Sheets aus dem Excel-Report zur Anzeige in Streamlit.

    Args:
        pfad (str): Absoluter Pfad zur Excel-Datei.

    Returns:
        dict: Dictionary mit Keys:
              - "Mini-Report"
              - "Änderungen"
              - "Fehler"
              - "Nicht gefunden"
              Jeder Key enthält einen DataFrame.
    """
    if not os.path.exists(pfad) and 'latest_report_path' in st.session_state:
        pfad = st.session_state.latest_report_path

    sheets = {
        "Mini-Report": pd.DataFrame(),
        "Änderungen": pd.DataFrame(),
        "Fehler": pd.DataFrame(),
        "Nicht gefunden": pd.DataFrame()
    }

    if not os.path.exists(pfad):
        return sheets

    try:
        xls = pd.ExcelFile(pfad)
        for name in sheets:
            if name in xls.sheet_names:
                sheets[name] = pd.read_excel(xls, sheet_name=name)
    except Exception as e:
        logging.error(f"❌ Fehler beim Laden des Reports: {e}")

    return sheets




def leere_verzeichnisse(verzeichnisse: list[str]) -> list[tuple[str, str]]:
    """
    Löscht alle Dateien und Unterverzeichnisse in den angegebenen Verzeichnissen.
    """
    fehler_liste = []
    logging.warning("🧹 Starte Aufräumprozess...")

    for ordner in verzeichnisse:
        try:
            eintraege = os.listdir(ordner)
            logging.warning(f"🔍 Inhalt von {ordner}: {eintraege}")
        except Exception as e:
            logging.warning(f"❌ Fehler beim Lesen von {ordner}: {e}")
            fehler_liste.append((ordner, str(e)))
            continue

        for eintrag in eintraege:
            pfad = os.path.join(ordner, eintrag)
            try:
                if os.path.isfile(pfad) or os.path.islink(pfad):
                    os.unlink(pfad)
                elif os.path.isdir(pfad):
                    shutil.rmtree(pfad)
                logging.info(f"🗑️ Gelöscht: {pfad}")
            except Exception as e:
                fehler_liste.append((pfad, str(e)))
                logging.warning(f"❌ Fehler beim Löschen: {pfad} – {e}")

    return fehler_liste
