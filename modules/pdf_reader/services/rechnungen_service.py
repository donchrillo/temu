"""Modul zum Auslesen von Rechnungs-PDFs und Export als Excel."""
import re
from pathlib import Path
from typing import Optional, List

import pandas as pd
import pdfplumber

from .patterns import PATTERNS
from .document_identifier import determine_country_and_document_type
from .amount_utils import parse_amount, find_value_after_labels
from .config import ORDNER_EINGANG_RECHNUNGEN, ORDNER_AUSGANG
from modules.shared import log_service

# Konstanten für Job-Typ-Identifikation
JOB_TYPE = "pdf_rechnungen_process"


def extract_data_from_pdf(pdf_path: Path, job_id: str) -> Optional[dict]:
    """Extrahiert Rechnungsdaten aus einem einzelnen PDF.

    Args:
        pdf_path: Pfad zur PDF-Datei.
        job_id: Job ID für Logging.

    Returns:
        dict or None: Extrahierte Daten oder None bei Fehlern.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)

        country_code, document_type = determine_country_and_document_type(text)
        if not country_code or not document_type:
            log_service.log(job_id, JOB_TYPE, "WARNING", f"Land oder Dokumenttyp konnte nicht für die Datei {pdf_path.name} bestimmt werden.")
            return None

        if document_type == "werbung":
            log_service.log(job_id, JOB_TYPE, "ERROR", f"❌ FALSCHER DOKUMENTTYP: '{pdf_path.name}' ist eine Werbe-Rechnung, nicht eine normale Rechnung! Bitte in die Werbung-Sektion hochladen.")
            return None

        lang_patterns = PATTERNS.get(country_code, {}).get(document_type, {})
        if not lang_patterns:
            log_service.log(job_id, JOB_TYPE, "WARNING", f"Keine passenden Patterns für country_code '{country_code}' und document_type '{document_type}' gefunden.")
            return None

        data = {
            "Dateiname": pdf_path.name,
            "Country_Code": country_code,
            "Dokumenttyp": document_type,
            "Rechnungsnummer": "",
            "Datum": "",
            "Nettowert": "",
            "Mehrwertsteuer": "",
            "Bruttowert": "",
        }

        data["Rechnungsnummer"] = _extract_field_value(text, lang_patterns, "rechnungsnummer", country_code, extra_keys_de=["Rechnung Nr.", "Rechnungsnr.", "Rechnungsnummer"])
        data["Datum"] = _extract_field_value(text, lang_patterns, "rechnungsdatum", country_code, extra_keys_de=["Rechnungsdatum", "Datum:", "Lieferdatum:"])
        _extract_amounts(data, text, lang_patterns, country_code, document_type, job_id, pdf_path.name)

        return data
    except Exception as e:
        log_service.log(job_id, JOB_TYPE, "ERROR", f"Fehler beim Verarbeiten der Datei {pdf_path.name}: {e}")
        return None


def _extract_field_value(
    text: str,
    lang_patterns: dict,
    pattern_key: str,
    country_code: str,
    extra_keys_de: Optional[List[str]] = None,
) -> str:
    """Extrahiert einen einzelnen Feldwert (z.B. Rechnungsnummer, Datum) aus dem PDF-Text.

    Sucht zuerst mit dem Haupt-Pattern, dann mit länderspezifischen Fallbacks.
    """
    keys = [lang_patterns.get(pattern_key)]
    if country_code == "de" and extra_keys_de:
        keys.extend(extra_keys_de)

    for key in keys:
        if key and key in text:
            try:
                parts = text.split(key)
                if len(parts) > 1:
                    val = parts[1].strip().split()[0]
                    if val:
                        return val
            except Exception:
                pass
    return ""


def _extract_amounts(
    data: dict,
    text: str,
    lang_patterns: dict,
    country_code: str,
    document_type: str,
    job_id: str,
    filename: str,
) -> None:
    """Extrahiert Netto, MwSt und Brutto aus dem PDF-Text.

    Versucht zuerst ein zeilenbasiertes Block-Matching (Versuch 1),
    dann einzelne Label-basierte Suche für DE (Versuch 2).
    """
    # Versuch 1: Zeilenbasiert / Block
    if _try_block_amount_extraction(data, text, lang_patterns, document_type):
        return

    # Versuch 2: Einzelwert-Suche (DE-spezifisch)
    if country_code == "de":
        _extract_de_amounts(data, text, country_code, document_type)

    if not data["Bruttowert"]:
        log_service.log(job_id, JOB_TYPE, "WARNING", f"Keine Beträge gefunden für {filename}")


def _try_block_amount_extraction(
    data: dict,
    text: str,
    lang_patterns: dict,
    document_type: str,
) -> bool:
    """Versucht Beträge via Zeilenblock-Matching zu extrahieren (z.B. 'Total EUR 92.00 EUR 17.48 EUR 109.48').

    Returns:
        True wenn Beträge erfolgreich extrahiert wurden.
    """
    sum_key = lang_patterns.get("summe")
    if not sum_key or sum_key not in text:
        return False

    try:
        währung = lang_patterns.get("währung", "EUR")
        re_pattern = fr"{re.escape(sum_key)}\s+-?{währung}\s+\d+\.\d+\s+-?{währung}\s+\d+\.\d+\s+-?{währung}\s+\d+\.\d+"
        result = re.search(re_pattern, text)

        if not result:
            return False

        zahlen = re.findall(r"-?\d+\.\d+", result.group(0))
        if len(zahlen) < 2:
            return False

        zahlen = [float(z.replace(",", ".")) for z in zahlen]
        is_gutschrift = document_type == "gutschrift"

        if len(zahlen) == 3:
            data["Nettowert"] = -abs(zahlen[0]) if is_gutschrift else zahlen[0]
            data["Mehrwertsteuer"] = -abs(zahlen[1]) if is_gutschrift else zahlen[1]
            data["Bruttowert"] = -abs(zahlen[2]) if is_gutschrift else zahlen[2]
        elif len(zahlen) == 2:
            data["Nettowert"] = -abs(zahlen[0]) if is_gutschrift else zahlen[0]
            data["Bruttowert"] = -abs(zahlen[1]) if is_gutschrift else zahlen[1]
            data["Mehrwertsteuer"] = 0.0

        return True
    except Exception:
        return False


def _extract_de_amounts(
    data: dict,
    text: str,
    country_code: str,
    document_type: str,
) -> None:
    """Extrahiert Beträge für deutsche Rechnungen via Label-basierter Suche."""
    if not data["Nettowert"]:
        val = find_value_after_labels(text, ["Nettobetrag", "Nettobertrag", "Netto", "Nettowert"], country_code)
        if val is not None:
            data["Nettowert"] = val

    if not data["Mehrwertsteuer"]:
        val = find_value_after_labels(text, ["USt:", "MwSt:", "Umsatzsteuer:", "Steuerbetrag:"], country_code)
        if val is not None:
            data["Mehrwertsteuer"] = val

    if not data["Bruttowert"]:
        val = find_value_after_labels(text, ["Bruttobetrag", "Gesamtbetrag", "Rechnungsbetrag", "Gesamtsumme", "Endbetrag"], country_code)
        if val is not None:
            data["Bruttowert"] = val

    # Gutschrift-Logik: Beträge negativ machen
    if document_type == "gutschrift":
        for key in ("Nettowert", "Mehrwertsteuer", "Bruttowert"):
            if data[key]:
                data[key] = -abs(data[key])


def process_rechnungen(job_id: str, directory: Path = ORDNER_EINGANG_RECHNUNGEN, output_excel: Path = ORDNER_AUSGANG / "rechnungen.xlsx") -> pd.DataFrame:
    """Liest alle PDFs aus dem Verzeichnis, extrahiert Daten und speichert sie als Excel.

    Args:
        job_id: Job ID für Logging.
        directory: Verzeichnis mit den PDF-Dateien.
        output_excel: Pfad zur Ausgabedatei.

    Returns:
        pd.DataFrame: Verarbeitete Daten.
    """
    pdf_files = list(directory.rglob("*.pdf"))
    if not pdf_files:
        log_service.log(job_id, JOB_TYPE, "WARNING", f"Keine PDF-Dateien im Verzeichnis '{directory.name}' gefunden.")
        return pd.DataFrame()

    all_data = []
    for pdf_file in pdf_files:
        data = extract_data_from_pdf(pdf_file, job_id)
        if data:
            all_data.append(data)

    if not all_data:
        return pd.DataFrame()

    df = pd.DataFrame(all_data)
    with pd.ExcelWriter(output_excel, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
        workbook = writer.book
        worksheet = writer.sheets["Sheet1"]
        decimal_format = workbook.add_format({"num_format": "#,##0.00"})
        worksheet.set_column("F:H", None, decimal_format)

    log_service.log(job_id, JOB_TYPE, "INFO", f"DataFrame als Excel-Datei gespeichert: {output_excel.name}")
    return df