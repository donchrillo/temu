"""
zip_handler.py – Funktionen für das Entpacken, Aufräumen und Archivieren von CSV-/ZIP-Dateien

Dieses Modul enthält Hilfsfunktionen zur:
- Extraktion von ZIP-Dateien in ein temporäres Arbeitsverzeichnis
- Archivierung von CSV-Dateien gemeinsam mit Reports in ZIP-Dateien
- Reinigung temporärer Verzeichnisse

Die Funktionen werden hauptsächlich im `backend.py` genutzt.
"""

# ========== 📦 Standardbibliotheken ==========

import os
import zipfile
import shutil
import logging

# ========== ⚙️ Projektverzeichnisse aus config.py ==========

from config import (
    ORDNER_EINGANG,
    ORDNER_AUSGANG,
    TMP_ORDNER
)


def entpacke_zip(zip_name: str) -> bool:
    """
    Entpackt eine ZIP-Datei aus dem Eingangsordner in das TEMP-Verzeichnis.

    Vor dem Entpacken wird sichergestellt, dass das TEMP-Verzeichnis leer ist.
    Anschließend wird der Inhalt der ZIP-Datei dorthin extrahiert.

    Args:
        zip_name (str): Name der ZIP-Datei im Eingangsverzeichnis, z. B. "daten.zip"

    Returns:
        bool: True, wenn das Entpacken erfolgreich war, sonst False.
    """
    try:
        zip_path = os.path.join(ORDNER_EINGANG, zip_name)

        # Prüfe, ob die ZIP-Datei existiert
        if not os.path.isfile(zip_path):
            logging.error(f"❌ ZIP-Datei nicht gefunden: {zip_path}")
            return False

        # TEMP-Ordner vollständig löschen (falls vorhanden)
        if os.path.exists(TMP_ORDNER):
            try:
                shutil.rmtree(TMP_ORDNER)
                logging.info(f"🗑️ TEMP-Ordner geleert: {TMP_ORDNER}")
            except Exception as e:
                logging.error(f"❌ Fehler beim Löschen des TEMP-Ordners: {e}")
                return False

        # TEMP-Ordner neu erstellen
        try:
            os.makedirs(TMP_ORDNER, exist_ok=True)
            logging.info(f"📁 TEMP-Ordner erstellt: {TMP_ORDNER}")
        except Exception as e:
            logging.error(f"❌ Fehler beim Erstellen des TEMP-Ordners: {e}")
            return False

        # ZIP-Datei entpacken
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(TMP_ORDNER)
            logging.info(f"📦 ZIP-Datei entpackt: {zip_name} → {TMP_ORDNER}")
            return True
        except Exception as e:
            logging.error(f"❌ Fehler beim Entpacken von {zip_name}: {e}")
            return False

    except Exception as e:
        logging.error(f"❌ Unerwarteter Fehler beim Entpacken von {zip_name}: {e}")
        return False



def aufraeumen_temp() -> None:
    """
    Löscht den kompletten TEMP-Ordner (inkl. aller enthaltenen Dateien).

    Wird meist nach dem Entpacken und Verarbeiten von ZIP-Dateien aufgerufen.
    """
    if os.path.exists(TMP_ORDNER):
        shutil.rmtree(TMP_ORDNER)
        logging.info("🧹 TEMP-Ordner vollständig gelöscht.")


def leere_ordner(pfad: str) -> None:
    """
    Löscht alle Dateien (nicht Unterordner) im angegebenen Verzeichnis.

    Nützlich zum Aufräumen, ohne den gesamten Ordner zu entfernen.

    Args:
        pfad (str): Pfad zum zu leerenden Ordner
    """
    if not os.path.exists(pfad):
        return

    for datei in os.listdir(pfad):
        dateipfad = os.path.join(pfad, datei)
        try:
            os.remove(dateipfad)
        except Exception as e:
            logging.warning(f"⚠️ Datei konnte nicht gelöscht werden: {dateipfad} → {e}")


def zippe_csv_auswahl(dateien: list, zielpfad: str, zusatzdateien: list = None) -> bool:
    """
    Erstellt ein ZIP-Archiv mit ausgewählten CSV-Dateien und optionalen Zusatzdateien.

    Die ZIP-Datei wird im Pfad `zielpfad` gespeichert und enthält:
    - alle angegebenen CSV-Dateien aus dem Ausgangsverzeichnis
    - optional Zusatzdateien (z. B. Report oder Logfile)

    Args:
        dateien (list): Liste von CSV-Dateinamen (nur Dateiname, ohne Pfadangabe)
        zielpfad (str): Zielpfad zur neuen ZIP-Datei (inkl. .zip-Endung)
        zusatzdateien (list, optional): Liste von vollständigen Pfaden zu weiteren Dateien

    Returns:
        bool: True, wenn ZIP erfolgreich erstellt wurde, sonst False.
    """
    try:
        with zipfile.ZipFile(zielpfad, "w", zipfile.ZIP_DEFLATED) as zipf:
            # CSV-Dateien hinzufügen
            for dateiname in dateien:
                csv_pfad = os.path.join(ORDNER_AUSGANG, dateiname)
                if os.path.isfile(csv_pfad):
                    zipf.write(csv_pfad, arcname=dateiname)
                    logging.info(f"➕ CSV-Datei hinzugefügt: {dateiname}")
                else:
                    logging.warning(f"⚠️ Datei nicht gefunden und daher übersprungen: {dateiname}")

            # Weitere Dateien (z. B. Report oder Logfile) hinzufügen
            if zusatzdateien:
                for pfad in zusatzdateien:
                    if os.path.isfile(pfad):
                        zipf.write(pfad, arcname=os.path.basename(pfad))
                        logging.info(f"➕ Zusatzdatei hinzugefügt: {os.path.basename(pfad)}")

        logging.info(f"📦 ZIP-Archiv erfolgreich erstellt: {zielpfad}")
        return True

    except Exception as e:
        logging.error(f"❌ Fehler beim Erstellen des ZIP-Archivs: {e}")
        return False
