"""Modul zum Auslesen von Rechnungs-PDFs und Export als Excel."""
import re
from pathlib import Path
from typing import Optional, List

import pandas as pd
import pdfplumber

from .patterns import pattern as pat
from .document_identifier import determine_country_and_document_type
from .config import ORDNER_EINGANG_RECHNUNGEN, ORDNER_AUSGANG
from modules.shared import log_service


def parse_amount_local(amount_str: str, country_code: str) -> float:
    """Parses amount string based on country code conventions."""
    # Simple logic: UK/US uses dot for decimal, EU uses comma
    if country_code in ['co.uk', 'us', 'ie']: # Irland oft auch Punkt oder Komma, aber meist wie UK in Amazon Kontext
         return float(amount_str.replace(",", ""))
    else:
         # DE, FR, IT, ES, etc. -> 1.000,00 -> 1000.00
         # Entferne Tausendertrennzeichen (Punkt) und ersetze Dezimaltrennzeichen (Komma) durch Punkt
         clean_str = amount_str.replace(".", "").replace(",", ".")
         return float(clean_str)

def find_value_after_labels(text: str, labels: List[str], country_code: str) -> Optional[float]:
    """Sucht nach einer Zahl, die nach einem der Labels im Text steht."""
    for label in labels:
        # Finde Label (case insensitive wäre gut, aber text ist raw)
        # Wir suchen Label, gefolgt von optionalem Doppelpunkt, Whitespace, optional Währung, Whitespace, Zahl
        # Zahl Pattern: Ziffern mit . oder ,
        
        # Regex konstruieren
        # (?i) für Case Insensitive
        # Label
        # \W* : Non-word characters (Doppelpunkt, Space)
        # (?:EUR|GBP|USD)? : Optionale Währung (vereinfacht)
        # \s*
        # ([\d.,]+) : Die Zahl
        
        regex = fr"(?i){re.escape(label)}\W*(?:EUR|GBP|USD|SEK|PLN)?\s*([\d.,]+)"
        match = re.search(regex, text)
        if match:
            amount_str = match.group(1)
            # Validierung: Hat es am Ende .xx oder ,xx?
            # Ignoriere reine Jahreszahlen oder IDs wenn möglich, aber patterns sind meist eindeutig ("Nettobetrag")
            try:
                return parse_amount_local(amount_str, country_code)
            except ValueError:
                continue
    return None


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
            text = "\n".join([page.extract_text() for page in pdf.pages])

        country_code, document_type = determine_country_and_document_type(text)
        if not country_code or not document_type:
            log_service.log(job_id, "pdf_rechnungen_process", "WARNING", f"Land oder Dokumenttyp konnte nicht für die Datei {pdf_path.name} bestimmt werden.")
            return None

        # Spezifischer Fehler wenn Werbung statt Rechnung hochgeladen wird
        if document_type == "werbung":
            log_service.log(job_id, "pdf_rechnungen_process", "ERROR", f"❌ FALSCHER DOKUMENTTYP: '{pdf_path.name}' ist eine Werbe-Rechnung, nicht eine normale Rechnung! Bitte in die Werbung-Sektion hochladen.")
            return None

        lang_patterns = pat.get(country_code, {}).get(document_type, {})
        if not lang_patterns:
            log_service.log(job_id, "pdf_rechnungen_process", "WARNING", f"Keine passenden Patterns für country_code '{country_code}' und document_type '{document_type}' gefunden.")
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

        # --- Rechnungsnummer ---
        rn_keys = [lang_patterns.get("rechnungsnummer")]
        if country_code == 'de':
            rn_keys.extend(["Rechnung Nr.", "Rechnungsnr.", "Rechnungsnummer"])
        
        for key in rn_keys:
            if key and key in text:
                try:
                    # Suche nach dem Key den nächsten "Wort"-Block
                    parts = text.split(key)
                    if len(parts) > 1:
                        val = parts[1].strip().split()[0]
                        if val:
                            data["Rechnungsnummer"] = val
                            break
                except Exception:
                    pass

        # --- Datum ---
        rd_keys = [lang_patterns.get("rechnungsdatum")]
        if country_code == 'de':
            rd_keys.extend(["Rechnungsdatum", "Datum:", "Lieferdatum:"])
            
        for key in rd_keys:
            if key and key in text:
                try:
                    parts = text.split(key)
                    if len(parts) > 1:
                        val = parts[1].strip().split()[0]
                        if val:
                            data["Datum"] = val
                            break
                except Exception:
                    pass

        # --- Beträge (Versuch 1: Zeilenbasiert / Block) ---
        found_amounts = False
        
        sum_key = lang_patterns.get("summe")
        if sum_key and sum_key in text:
            try:
                währung = lang_patterns.get("währung", "EUR")
                re_pattern = fr"{re.escape(sum_key)}\s+-?{währung}\s+\d+\.\d+\s+-?{währung}\s+\d+\.\d+\s+-?{währung}\s+\d+\.\d+"
                result = re.search(re_pattern, text)
                
                if result:
                    line_text = result.group(0)
                    zahlen = re.findall(r"-?\d+\.\d+", line_text)
                    if len(zahlen) >= 2:
                        zahlen = [float(zahl.replace(",", ".")) for zahl in zahlen]
                        if len(zahlen) == 3:
                            data["Nettowert"] = zahlen[0] if document_type != "gutschrift" else -abs(zahlen[0])
                            data["Mehrwertsteuer"] = zahlen[1] if document_type != "gutschrift" else -abs(zahlen[1])
                            data["Bruttowert"] = zahlen[2] if document_type != "gutschrift" else -abs(zahlen[2])
                            found_amounts = True
                        elif len(zahlen) == 2:
                            data["Nettowert"] = zahlen[0] if document_type != "gutschrift" else -abs(zahlen[0])
                            data["Bruttowert"] = zahlen[1] if document_type != "gutschrift" else -abs(zahlen[1])
                            data["Mehrwertsteuer"] = 0.0
                            found_amounts = True
            except Exception:
                pass

        # --- Beträge (Versuch 2: Einzelwert-Suche für DE/Andere Layouts) ---
        if not found_amounts:
            # Spezifische Fallbacks für DE Rechnungen (Tabellarisch)
            if country_code == 'de':
                # Netto
                if not data["Nettowert"]:
                    val = find_value_after_labels(text, ["Nettobetrag", "Netto", "Nettowert"], country_code)
                    if val is not None: data["Nettowert"] = val
                
                # Steuer
                if not data["Mehrwertsteuer"]:
                    val = find_value_after_labels(text, ["USt", "MwSt", "Umsatzsteuer"], country_code)
                    if val is not None: data["Mehrwertsteuer"] = val
                
                # Brutto
                if not data["Bruttowert"]:
                    val = find_value_after_labels(text, ["Bruttobetrag", "Gesamtbetrag", "Rechnungsbetrag", "Gesamtsumme"], country_code)
                    if val is not None: data["Bruttowert"] = val
                
                # Gutschrift-Logik anwenden (Negativ machen)
                if document_type == "gutschrift":
                    if data["Nettowert"]: data["Nettowert"] = -abs(data["Nettowert"])
                    if data["Mehrwertsteuer"]: data["Mehrwertsteuer"] = -abs(data["Mehrwertsteuer"])
                    if data["Bruttowert"]: data["Bruttowert"] = -abs(data["Bruttowert"])

        # Validierung
        if not data["Bruttowert"]:
             log_service.log(job_id, "pdf_rechnungen_process", "WARNING", f"Keine Beträge gefunden für {pdf_path.name}")

        return data
    except Exception as e:
        log_service.log(job_id, "pdf_rechnungen_process", "ERROR", f"Fehler beim Verarbeiten der Datei {pdf_path.name}: {e}")
        return None


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
        log_service.log(job_id, "pdf_rechnungen_process", "WARNING", f"Keine PDF-Dateien im Verzeichnis '{directory.name}' gefunden.")
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

    log_service.log(job_id, "pdf_rechnungen_process", "INFO", f"DataFrame als Excel-Datei gespeichert: {output_excel.name}")
    return df