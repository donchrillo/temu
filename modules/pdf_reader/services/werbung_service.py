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
from .werbung_extraction_service import load_filename_mapping

# Logger direkt nutzen
logger = werbung_logger


def parse_amount(amount_str: str, currency: str) -> float:
    """
    Parst einen Betrag basierend auf der Währung.

    Args:
        amount_str: Betrag als String (z.B. "1.234,56" oder "1,234.56")
        currency: Währung (z.B. "EUR", "GBP", "USD")

    Returns:
        float: Geparster Betrag
    """
    # UK und US verwenden Punkt als Dezimaltrennzeichen
    if currency.upper() in ["GBP", "USD"]:
        # Format: 1,234.56 -> entferne Kommas, behalte Punkt
        return float(amount_str.replace(",", ""))
    else:
        # EU-Format: 1.234,56 -> entferne Punkte, ersetze Komma durch Punkt
        return float(amount_str.replace(".", "").replace(",", "."))


def extract_data_from_pdf(pdf_path: Path, original_filename: Optional[str] = None) -> Optional[dict]:
    """
    Extrahiert strukturierte Daten aus einer Amazon-Werbekostenrechnung (PDF).

    Args:
        pdf_path: Pfad zur PDF-Datei.
        original_filename: Ursprünglicher Dateiname (falls umbenannt).

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
            "Dateiname": original_filename if original_filename else pdf_path.name,
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

        # Währung aus patterns extrahieren
        currency = lang_patterns.get("währung", "EUR")

        if lang_patterns.get("summe"):
            match = re.search(fr"{re.escape(lang_patterns['summe'])}\s*([\d.,]+)\s*{currency}", text)
            if match:
                data["Bruttowert"] = parse_amount(match.group(1), currency)

        if lang_patterns.get("mwst"):
            try:
                pattern = fr"{re.escape(lang_patterns['mwst'])}\s*([\d.,]+)\s*{currency}"
                match = re.search(pattern, text)
                if match:
                    data["Mehrwertsteuer"] = parse_amount(match.group(1), currency)
            except Exception as e:
                logger.warning(f"Fehler beim Extrahieren der MwSt: {e}")

        return data
    except Exception as e:
        logger.error(f"Fehler beim Verarbeiten von {pdf_path}: {e}")
        return None


def process_ad_pdfs(directory: Path = TMP_ORDNER, output_excel: Path = ORDNER_AUSGANG / "werbung.xlsx",
                    filename_mapping: Optional[dict[Path, str]] = None) -> pd.DataFrame:
    """
    Verarbeitet alle Werbe-PDFs im Verzeichnis und exportiert sie als Excel-Datei.

    Args:
        directory: Pfad zum Verzeichnis mit einseitigen PDFs.
        output_excel: Pfad zur Zieldatei.
        filename_mapping: Mapping von Dateipfad zu ursprünglichem Dateinamen.
                         Falls None, wird versucht, das Mapping aus dem directory zu laden.

    Returns:
        pd.DataFrame: Extrahierte Daten als DataFrame.
    """
    logger.info(f"🧪 process_ad_pdfs START: directory={directory}")

    # Lade Mapping aus JSON, falls nicht übergeben
    if filename_mapping is None:
        filename_mapping = load_filename_mapping(directory)
        if filename_mapping:
            logger.info(f"Dateinamen-Mapping geladen: {len(filename_mapping)} Einträge")

    pdf_files = list(directory.rglob("*.pdf"))
    if not pdf_files:
        logger.warning(f"Keine PDF-Dateien im Verzeichnis '{directory}' gefunden.")
        return pd.DataFrame()

    all_data = []
    for pdf_file in pdf_files:
        original_name = filename_mapping.get(pdf_file) if filename_mapping else None
        result = extract_data_from_pdf(pdf_file, original_filename=original_name)
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
