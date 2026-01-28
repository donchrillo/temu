"""Modul zum Auslesen von Werbe-Rechnungsdaten und Export als Excel."""
import re
from pathlib import Path
from typing import Optional

import pandas as pd
import pdfplumber

from .patterns import pattern as pat
from .document_identifier import determine_country_and_document_type
from .config import TMP_ORDNER, ORDNER_AUSGANG
from .logger import werbung_logger

# Logger direkt nutzen
logger = werbung_logger


def extract_data_from_pdf(pdf_path: Path) -> Optional[dict]:
    """
    Extrahiert strukturierte Daten aus einer Amazon-Werbekostenrechnung (PDF).

    Args:
        pdf_path: Pfad zur PDF-Datei.

    Returns:
        dict or None: Extrahierte Daten oder None bei Fehlern.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages])

        country_code, document_type = determine_country_and_document_type(text)
        if not country_code or not document_type:
            logger.warning(f"Kein gültiges Dokument erkannt: {pdf_path}")
            return None

        # Spezifischer Fehler wenn normale Rechnung statt Werbung hochgeladen wird
        if document_type in ["rechnung", "gutschrift"]:
            logger.error(f"❌ FALSCHER DOKUMENTTYP: '{pdf_path}' ist eine {document_type}, keine Werbe-Rechnung! "
                        f"Bitte in die Rechnungen-Sektion hochladen.")
            return None

        lang_patterns = pat.get(country_code, {}).get(document_type, {})
        if not lang_patterns:
            logger.warning(f"Keine Patterns gefunden für {country_code}, {document_type}: {pdf_path}")
            return None

        data = {
            "Dateiname": pdf_path.name,
            "Country_Code": country_code,
            "Dokumenttyp": document_type,
            "Rechnungsnummer": "",
            "Rechnungsdatum": "",
            "Zeitraum_Start": "",
            "Zeitraum_Ende": "",
            "Bruttowert": "",
            "Mehrwertsteuer": "",
        }

        if lang_patterns.get("rechnungsnummer"):
            match = re.search(fr"{re.escape(lang_patterns['rechnungsnummer'])}\s*(\w+)", text)
            if match:
                data["Rechnungsnummer"] = match.group(1)

        if lang_patterns.get("rechnungsdatum"):
            match = re.search(fr"{re.escape(lang_patterns['rechnungsdatum'])}\s*([\d\-]+)", text)
            if match:
                data["Rechnungsdatum"] = match.group(1)

        if lang_patterns.get("zeitraum"):
            match = re.search(fr"{re.escape(lang_patterns['zeitraum'])}\s*([\d\-]+)\s*-\s*([\d\-]+)", text)
            if match:
                data["Zeitraum_Start"] = match.group(1)
                data["Zeitraum_Ende"] = match.group(2)

        if lang_patterns.get("summe"):
            match = re.search(fr"{re.escape(lang_patterns['summe'])}\s*([\d.,]+)\s*{lang_patterns['währung']}", text)
            if match:
                bruttowert = match.group(1).replace(".", "").replace(",", ".")
                data["Bruttowert"] = float(bruttowert)

        if lang_patterns.get("mwst"):
            try:
                pattern = fr"{re.escape(lang_patterns['mwst'])}\s*([\d.,]+)\s*{lang_patterns['währung']}"
                match = re.search(pattern, text)
                if match:
                    mwst = match.group(1).replace(".", "").replace(",", ".")
                    data["Mehrwertsteuer"] = float(mwst)
            except Exception as e:
                logger.warning(f"Fehler beim Extrahieren der MwSt: {e}")

        return data
    except Exception as e:
        logger.error(f"Fehler beim Verarbeiten von {pdf_path}: {e}")
        return None


def process_ad_pdfs(directory: Path = TMP_ORDNER, output_excel: Path = ORDNER_AUSGANG / "werbung.xlsx") -> pd.DataFrame:
    """
    Verarbeitet alle Werbe-PDFs im Verzeichnis und exportiert sie als Excel-Datei.

    Args:
        directory: Pfad zum Verzeichnis mit einseitigen PDFs.
        output_excel: Pfad zur Zieldatei.

    Returns:
        pd.DataFrame: Extrahierte Daten als DataFrame.
    """
    logger.info(f"🧪 process_ad_pdfs START: directory={directory}")
    
    pdf_files = list(directory.rglob("*.pdf"))
    if not pdf_files:
        logger.warning(f"Keine PDF-Dateien im Verzeichnis '{directory}' gefunden.")
        return pd.DataFrame()

    all_data = []
    for pdf_file in pdf_files:
        result = extract_data_from_pdf(pdf_file)
        if result:
            all_data.append(result)

    df = pd.DataFrame(all_data)
    with pd.ExcelWriter(output_excel, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Werbung")
        workbook = writer.book
        worksheet = writer.sheets["Werbung"]
        format_euro = workbook.add_format({"num_format": "#,##0.00"})
        worksheet.set_column("G:H", None, format_euro)

    logger.info(f"Daten erfolgreich exportiert: {output_excel}")
    return df
