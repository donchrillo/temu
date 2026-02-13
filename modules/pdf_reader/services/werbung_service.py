"""Modul zum Auslesen von Werbe-Rechnungsdaten und Export als Excel."""
import re
from pathlib import Path
from typing import Optional

import pandas as pd
import pdfplumber

from .patterns import PATTERNS
from .document_identifier import determine_country_and_document_type
from .amount_utils import parse_amount
from .config import TMP_ORDNER, ORDNER_AUSGANG
from modules.shared import log_service

# Konstanten für Job-Typ-Identifikation
JOB_TYPE = "pdf_werbung_process"


def _calc_mwst_from_brutto_netto(
    text: str, lang_patterns: dict, currency: str, country_code: str, job_id: str
) -> float:
    """Berechnet MwSt als Differenz von Brutto und Netto."""
    brutto_pattern = lang_patterns.get("brutto_pattern", r"Importo Totale \(Tasse Incluse\)")
    netto_pattern = lang_patterns.get("netto_pattern", r"Totale Parziale \(Tasse Escluse\)")

    brutto_match = re.search(fr"{brutto_pattern}\s*([\d.,]+)\s*{currency}", text, re.IGNORECASE)
    netto_match = re.search(fr"{netto_pattern}\s*([\d.,]+)\s*{currency}", text, re.IGNORECASE)

    if brutto_match and netto_match:
        brutto = parse_amount(brutto_match.group(1), country_code, currency)
        netto = parse_amount(netto_match.group(1), country_code, currency)
        mwst = round(brutto - netto, 2)
        log_service.log(job_id, JOB_TYPE, "INFO", f"MwSt berechnet: {brutto} - {netto} = {mwst} {currency}")
        return mwst

    log_service.log(job_id, JOB_TYPE, "WARNING", "MwSt nicht gefunden, setze auf 0.00")
    return 0.00


def _extract_mwst(
    text: str, lang_patterns: dict, currency: str, country_code: str, job_id: str
) -> float:
    """Extrahiert die Mehrwertsteuer mit mehreren Fallback-Strategien.

    Strategie 1: Spezifische Regex (z.B. 'VAT(19%) - GERMANY 382.53 EUR')
    Strategie 2: Berechnung aus Brutto - Netto (mwst_calc)
    Strategie 3: Legacy-Fallback mit einfachem Pattern-Match
    """
    if not lang_patterns.get("mwst"):
        return 0.00

    try:
        # Strategie 1: Spezifische Regex
        if lang_patterns.get("mwst_regex"):
            match = re.search(lang_patterns["mwst_regex"], text, re.IGNORECASE)
            if match:
                amount = parse_amount(match.group(1), country_code, currency)
                log_service.log(job_id, JOB_TYPE, "INFO", f"MwSt extrahiert via Regex: {amount} {currency}")
                return amount

            # Fallback: Berechne MwSt aus Brutto - Netto
            if lang_patterns.get("mwst_calc"):
                return _calc_mwst_from_brutto_netto(text, lang_patterns, currency, country_code, job_id)

            log_service.log(job_id, JOB_TYPE, "WARNING", "Keine MwSt-Regex vorhanden, setze auf 0.00")
            return 0.00

        # Strategie 3: Legacy-Fallback
        pattern = fr"{re.escape(lang_patterns['mwst'])}\s*([\d.,]+)\s*{currency}"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return parse_amount(match.group(1), country_code, currency)

        log_service.log(job_id, JOB_TYPE, "WARNING", "MwSt nicht gefunden (Legacy), setze auf 0.00")
        return 0.00

    except Exception as e:
        log_service.log(job_id, JOB_TYPE, "WARNING", f"Fehler beim Extrahieren der MwSt: {e}")
        return 0.00


def extract_data_from_pdf(pdf_path: Path, job_id: str) -> Optional[dict]:
    """
    Extrahiert strukturierte Daten aus einer Amazon-Werbekostenrechnung (PDF).

    Args:
        pdf_path: Pfad zur PDF-Datei.
        job_id: Job ID für Logging.

    Returns:
        dict or None: Extrahierte Daten oder None bei Fehlern.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages])

        country_code, document_type = determine_country_and_document_type(text)
        if not country_code or not document_type:
            log_service.log(job_id, JOB_TYPE, "WARNING", f"Kein gültiges Dokument erkannt: {pdf_path.name}")
            return None

        # Spezifischer Fehler wenn normale Rechnung statt Werbung hochgeladen wird
        if document_type in ["rechnung", "gutschrift"]:
            log_service.log(job_id, JOB_TYPE, "ERROR", f"❌ FALSCHER DOKUMENTTYP: '{pdf_path.name}' ist eine {document_type}, keine Werbe-Rechnung! Bitte in die Rechnungen-Sektion hochladen.")
            return None

        lang_patterns = PATTERNS.get(country_code, {}).get(document_type, {})
        if not lang_patterns:
            log_service.log(job_id, JOB_TYPE, "WARNING", f"Keine Patterns gefunden für {country_code}, {document_type}: {pdf_path.name}")
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
            match = re.search(fr"{re.escape(lang_patterns['rechnungsnummer'])}\s*[:\s]*(\w+)", text, re.IGNORECASE)
            if match:
                data["Rechnungsnummer"] = match.group(1)

        if lang_patterns.get("rechnungsdatum"):
            match = re.search(fr"{re.escape(lang_patterns['rechnungsdatum'])}\s*[:\s]*([\d\-]+)", text, re.IGNORECASE)
            if match:
                data["Rechnungsdatum"] = match.group(1)

        if lang_patterns.get("zeitraum"):
            # Für italienisch: "al" statt "-"
            match = re.search(fr"{re.escape(lang_patterns['zeitraum'])}\s*[:\s]*([\d\-]+)\s*(?:-|al)\s*([\d\-]+)", text, re.IGNORECASE)
            if match:
                data["Zeitraum_Start"] = match.group(1)
                data["Zeitraum_Ende"] = match.group(2)

        # Währung aus patterns extrahieren
        currency = lang_patterns.get("währung", "EUR")

        if lang_patterns.get("summe"):
            match = re.search(fr"{re.escape(lang_patterns['summe'])}\s*([\d.,]+)\s*{currency}", text, re.IGNORECASE)
            if match:
                data["Bruttowert"] = parse_amount(match.group(1), country_code, currency)

        data["Mehrwertsteuer"] = _extract_mwst(text, lang_patterns, currency, country_code, job_id)

        return data
    except Exception as e:
        log_service.log(job_id, JOB_TYPE, "ERROR", f"Fehler beim Verarbeiten von {pdf_path.name}: {e}")
        return None


def process_ad_pdfs(job_id: str, directory: Path = TMP_ORDNER, output_excel: Path = ORDNER_AUSGANG / "werbung.xlsx") -> pd.DataFrame:
    """
    Verarbeitet alle Werbe-PDFs im Verzeichnis und exportiert sie als Excel-Datei.

    Args:
        job_id: Job ID für Logging.
        directory: Pfad zum Verzeichnis mit einseitigen PDFs.
        output_excel: Pfad zur Zieldatei.

    Returns:
        pd.DataFrame: Extrahierte Daten als DataFrame.
    """
    log_service.log(job_id, JOB_TYPE, "INFO", f"process_ad_pdfs START: directory={directory.name}")

    pdf_files = list(directory.rglob("*.pdf"))
    if not pdf_files:
        log_service.log(job_id, JOB_TYPE, "WARNING", f"Keine PDF-Dateien im Verzeichnis '{directory}' gefunden.")
        return pd.DataFrame()

    all_data = []
    for pdf_file in pdf_files:
        result = extract_data_from_pdf(pdf_file, job_id)
        if result:
            all_data.append(result)

    if not all_data:
         return pd.DataFrame()

    df = pd.DataFrame(all_data)
    with pd.ExcelWriter(output_excel, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Werbung")
        workbook = writer.book
        worksheet = writer.sheets["Werbung"]
        format_euro = workbook.add_format({"num_format": "#,##0.00"})
        worksheet.set_column("G:H", None, format_euro)

    log_service.log(job_id, JOB_TYPE, "INFO", f"Daten erfolgreich exportiert: {output_excel.name}")
    return df
