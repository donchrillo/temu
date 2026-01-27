"""Modul zum Auslesen von Rechnungs-PDFs und Export als Excel."""

from os import path
from click import Path
import pdfplumber
import pandas as pd
import logging
import re

from patterns import pattern as pat
from document_identifier import determine_country_and_document_type
from config import ORDNER_EINGANG_RECHNUNGEN, ORDNER_AUSGANG, ORDNER_LOG



# Logger-Konfiguration
logger = logging.getLogger("rechnung_read_logger")
logger.setLevel(logging.INFO)

log_path = ORDNER_LOG / "rechnung_read.log"
fh = logging.FileHandler(log_path, mode='w', encoding='utf-8')
fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)


def extract_data_from_pdf(pdf_path: Path) -> dict | None:
    """Extrahiert Rechnungsdaten aus einem einzelnen PDF.

    Args:
        pdf_path (str): Pfad zur PDF-Datei.

    Returns:
        dict or None: Extrahierte Daten oder None bei Fehlern.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages])

        country_code, document_type = determine_country_and_document_type(text)

        if not country_code or not document_type:
            logger.warning(f"Land oder Dokumenttyp konnte nicht für die Datei {pdf_path} bestimmt werden.")
            return None

        lang_patterns = pat.get(country_code, {}).get(document_type, {})

        if not lang_patterns:
            logger.warning(f"Keine passenden Patterns für country_code '{country_code}' und document_type '{document_type}' gefunden.")
            return None

        data = {
            "Dateiname": pdf_path.name,
            "Country_Code": country_code,
            "Dokumenttyp": document_type,
            "Rechnungsnummer": "",
            "Datum": "",
            "Nettowert": "",
            "Mehrwertsteuer": "",
            "Bruttowert": ""
        }

        if lang_patterns.get("rechnungsnummer") in text:
            data["Rechnungsnummer"] = text.split(lang_patterns["rechnungsnummer"])[1].split()[0]

        if lang_patterns.get("rechnungsdatum") in text:
            data["Datum"] = text.split(lang_patterns["rechnungsdatum"])[1].split()[0]

        try:
            if lang_patterns.get("summe") in text:
                re_pattern = fr"{lang_patterns['summe']}\s+-?{lang_patterns['währung']}\s+\d+\.\d+\s+-?{lang_patterns['währung']}\s+\d+\.\d+\s+-?{lang_patterns['währung']}\s+\d+\.\d+"
                result = re.search(re_pattern, text)

                if result:
                    line = result.group(0)
                    zahlen = re.findall(r'-?\d+\.\d+', line)

                    if len(zahlen) >= 2:
                        zahlen = [float(zahl.replace(',', '.')) for zahl in zahlen]

                        if len(zahlen) == 3:
                            if document_type == "gutschrift":
                                data["Nettowert"] = -abs(zahlen[0])
                                data["Mehrwertsteuer"] = -abs(zahlen[1])
                                data["Bruttowert"] = -abs(zahlen[2])
                            else:
                                data["Nettowert"] = zahlen[0]
                                data["Mehrwertsteuer"] = zahlen[1]
                                data["Bruttowert"] = zahlen[2]
                        elif len(zahlen) == 2:
                            if document_type == "gutschrift":
                                data["Nettowert"] = -abs(zahlen[0])
                                data["Bruttowert"] = -abs(zahlen[1])
                                data["Mehrwertsteuer"] = 0.0
                            else:
                                data["Nettowert"] = zahlen[0]
                                data["Bruttowert"] = zahlen[1]
                                data["Mehrwertsteuer"] = 0.0
                    else:
                        logger.warning(f"Weniger als 2 Beträge gefunden in der Zeile für {pdf_path}")
        except ValueError as e:
            logger.error(f"Fehler beim Konvertieren der Beträge in {pdf_path}: {e}")

        return data

    except Exception as e:
        logger.error(f"Fehler beim Verarbeiten der Datei {pdf_path}: {e}")
        return None


def process_rechnungen(directory: Path, output_excel: Path) -> pd.DataFrame:
    """Liest alle PDFs aus dem Verzeichnis, extrahiert Daten und speichert sie als Excel.

    Args:
        directory (str): Verzeichnis mit den PDF-Dateien als PATH
        output_excel (str): Pfad zur Ausgabedatei.

    Returns:
        pd.DataFrame: Verarbeitete Daten.
    """

    pdf_files = list(directory.rglob("*.pdf"))


    if not pdf_files:
        logger.warning(f"Keine PDF-Dateien im Verzeichnis '{directory}' gefunden.")
        return pd.DataFrame()

    all_data = []

    for pdf_file in pdf_files:
        data = extract_data_from_pdf(pdf_file)
        if data:
            all_data.append(data)

    df = pd.DataFrame(all_data)

    with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        decimal_format = workbook.add_format({'num_format': '#,##0.00'})
        worksheet.set_column('F:H', None, decimal_format)

    logger.info(f'DataFrame als Excel-Datei gespeichert: {output_excel}')
    return df


if __name__ == "__main__":
    process_rechnungen(ORDNER_EINGANG_RECHNUNGEN, ORDNER_AUSGANG / "rechnungen.xlsx")
