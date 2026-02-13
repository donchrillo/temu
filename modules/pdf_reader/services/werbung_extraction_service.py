"""Hilfsmodul zum Extrahieren der ersten Seite von Werbe-PDFs."""
import re
from pathlib import Path
from typing import List

from PyPDF2 import PdfReader, PdfWriter
import pdfplumber

from .document_identifier import determine_country_and_document_type
from .config import ORDNER_EINGANG_WERBUNG, TMP_ORDNER
from modules.shared import log_service


def extract_and_save_first_page(job_id: str, input_dir: Path = ORDNER_EINGANG_WERBUNG, output_dir: Path = TMP_ORDNER) -> List[Path]:
    """
    Extrahiert die erste Seite aller PDFs im Eingangsverzeichnis und speichert sie
    unter dem Originalnamen im Zielverzeichnis.

    Returns:
        List[Path]: Liste der Pfade der erfolgreich extrahierten Dateien im Zielverzeichnis.
    """
    pdf_files = [file for file in input_dir.iterdir() if file.suffix.lower() == ".pdf"]
    if not pdf_files:
        log_service.log(job_id, "pdf_werbung_extract", "WARNING", f"Keine PDF-Dateien im Eingangsverzeichnis '{input_dir.name}' gefunden.")
        return []

    extracted_files: List[Path] = []
    
    # Zielverzeichnis leeren/sicherstellen? 
    # Aktuell überschreiben wir einfach. Das ist ok für TMP.
    
    for file in pdf_files:
        file_path = input_dir / file
        try:
            # Validierung: Ist es eine Werberechnung?
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join([(page.extract_text() or "") for page in pdf.pages[:1]])

            country_code, document_type = determine_country_and_document_type(text)
            if not country_code or document_type != "werbung":
                log_service.log(job_id, "pdf_werbung_extract", "WARNING", f"Nicht als Werbekostenrechnung erkannt: {file.name}")
                continue

            # Speichern unter Originalnamen
            output_path = output_dir / file.name

            reader = PdfReader(file_path)
            writer = PdfWriter()
            writer.add_page(reader.pages[0])
            with open(output_path, "wb") as f_out:
                writer.write(f_out)

            log_service.log(job_id, "pdf_werbung_extract", "INFO", f"Erste Seite extrahiert: {output_path.name}")
            extracted_files.append(output_path)
            
        except Exception as e:
            log_service.log(job_id, "pdf_werbung_extract", "ERROR", f"Fehler bei Datei {file.name}: {e}")

    return extracted_files
