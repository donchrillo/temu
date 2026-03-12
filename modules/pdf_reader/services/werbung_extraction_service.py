"""Hilfsmodul zum Extrahieren der ersten Seite von Werbe-PDFs."""
from pathlib import Path
from typing import List

from PyPDF2 import PdfReader, PdfWriter
import pdfplumber

from .document_identifier import determine_country_and_document_type
from .config import ORDNER_EINGANG_WERBUNG, TMP_ORDNER
from modules.shared import log_service

# Konstanten für Job-Typ-Identifikation
JOB_TYPE = "pdf_werbung_extract"


def extract_and_save_first_page(
    job_id: str,
    input_dir: Path = ORDNER_EINGANG_WERBUNG,
    output_dir: Path = TMP_ORDNER,
) -> List[Path]:
    """Extrahiert die erste Seite aller Werbe-PDFs und speichert sie im TMP-Verzeichnis.

    Nur als Werbung erkannte PDFs werden verarbeitet. Andere werden übersprungen.

    Args:
        job_id: Job ID für Logging.
        input_dir: Verzeichnis mit den Original-PDFs.
        output_dir: Zielverzeichnis für die extrahierten Einzelseiten.

    Returns:
        Liste der Pfade der erfolgreich extrahierten Dateien.
    """
    pdf_files = [f for f in input_dir.iterdir() if f.suffix.lower() == ".pdf"]
    if not pdf_files:
        log_service.log(job_id, JOB_TYPE, "WARNING", f"Keine PDF-Dateien im Eingangsverzeichnis '{input_dir.name}' gefunden.")
        return []

    extracted_files: List[Path] = []

    for pdf_file in pdf_files:
        try:
            if not _is_werbung_pdf(pdf_file):
                log_service.log(job_id, JOB_TYPE, "WARNING", f"Nicht als Werbekostenrechnung erkannt: {pdf_file.name}")
                continue

            output_path = _extract_first_page(pdf_file, output_dir)
            log_service.log(job_id, JOB_TYPE, "INFO", f"Erste Seite extrahiert: {output_path.name}")
            extracted_files.append(output_path)

        except Exception as e:
            log_service.log(job_id, JOB_TYPE, "ERROR", f"Fehler bei Datei {pdf_file.name}: {e}")

    return extracted_files


def _is_werbung_pdf(pdf_path: Path) -> bool:
    """Prüft ob ein PDF als Werbekostenrechnung erkannt wird."""
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join((page.extract_text() or "") for page in pdf.pages[:1])
    _, document_type = determine_country_and_document_type(text)
    return document_type == "werbung"


def _extract_first_page(pdf_path: Path, output_dir: Path) -> Path:
    """Extrahiert die erste Seite eines PDFs und speichert sie unter dem Originalnamen."""
    output_path = output_dir / pdf_path.name
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    writer.add_page(reader.pages[0])
    with open(output_path, "wb") as f_out:
        writer.write(f_out)
    return output_path
