"""Hilfsmodul zum Extrahieren der ersten Seite von Werbe-PDFs."""

import logging
from pathlib import Path  # ← NEU: statt from click import Path
import re
from datetime import datetime  # ← NEU
from PyPDF2 import PdfReader, PdfWriter
import pdfplumber

from document_identifier import determine_country_and_document_type
from patterns import pattern
from config import ORDNER_EINGANG_WERBUNG, TMP_ORDNER, ORDNER_LOG

# Logging wie gehabt …
logger = logging.getLogger("werbung_extraction_logger")
logger.setLevel(logging.INFO)
log_path = ORDNER_LOG / "werbung_extraction.log"
fh = logging.FileHandler(log_path, mode='w', encoding='utf-8')
fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)


# ── NEU: Helfer zum Normalisieren auf YYYY-MM-DD ──────────────────────────────
def _to_iso_date(s: str) -> str:
    """
    Wandelt ein Datum mit Trennern .-/ und Reihenfolgen DMY/YMD in YYYY-MM-DD.
    Unterstützt 2- und 4-stellige Jahre (bei 2-stellig wird 2000+ angenommen).
    """
    s = s.strip()
    s = re.sub(r"[./]", "-", s)  # vereinheitlichen
    # Mögliche Formate versuchen
    fmts = ("%d-%m-%Y", "%d-%m-%y", "%Y-%m-%d", "%m-%d-%Y", "%m-%d-%y")
    for fmt in fmts:
        try:
            dt = datetime.strptime(s, fmt)
            # 2-stelliges Jahr → datetime macht 1900er; anheben auf 2000er wenn nötig
            if dt.year < 1970:  # Heuristik – pass bei Bedarf an
                dt = dt.replace(year=dt.year + 100)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Als Fallback: selbst parsen, wenn Reihenfolge offensichtlich ist
    m = re.match(r"^(\d{1,4})-(\d{1,2})-(\d{2,4})$", s)
    if m:
        a, b, c = m.groups()
        # Wenn erstes Feld 4-stellig → Y-M-D, sonst D-M-Y
        if len(a) == 4:
            y, mth, d = int(a), int(b), int(c)
        else:
            d, mth, y = int(a), int(b), int(c)
            if y < 100:
                y += 2000
        return f"{y:04d}-{mth:02d}-{d:02d}"
    raise ValueError(f"Unbekanntes Datumsformat: {s}")


def extract_and_save_first_page(input_dir: Path, output_dir: Path) -> list[Path]:
    """
    Extrahiert die erste Seite aller PDFs im Eingangsverzeichnis und speichert sie
    unter neuem, sprechendem Namen im Zielverzeichnis.

    Neuer Dateiname: "<land>_<YYYY-MM-DD>_<YYYY-MM-DD>.pdf"
    """
    pdf_files = [file for file in input_dir.iterdir() if file.suffix.lower() == ".pdf"]

    if not pdf_files:
        logger.warning(f"Keine PDF-Dateien im Eingangsverzeichnis '{input_dir}' gefunden.")
        return []

    new_paths = []

    for file in pdf_files:
        file_path = input_dir / file
        try:
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join([page.extract_text() or "" for page in pdf.pages[:1]])

            country_code, document_type = determine_country_and_document_type(text)
            if not country_code or document_type != "werbung":
                logger.warning(f"Nicht als Werbekostenrechnung erkannt: {file}")
                continue

            # Zeitraum-Label aus patterns.py lesen
            lang_patterns = pattern.get(country_code, {}).get("werbung", {})
            zeitraum_label = lang_patterns.get("zeitraum", "Rechnungszeitraum")

            # Flexibles Muster: dd.mm.yyyy / dd-mm-yyyy / dd/mm/yy etc. und -/–/— als Trennstrich
            date_pat = r"(\d{1,4}[.\-\/]\d{1,2}[.\-\/]\d{2,4})"
            match = re.search(
                fr"{re.escape(zeitraum_label)}\s+{date_pat}\s*[-–—]\s*{date_pat}",
                text,
                flags=re.IGNORECASE,
            )
            if not match:
                logger.warning(f"Kein Rechnungszeitraum gefunden: {file}")
                continue

            raw_start, raw_end = match.group(1), match.group(2)
            try:
                start_iso = _to_iso_date(raw_start)
                end_iso = _to_iso_date(raw_end)
            except ValueError as e:
                logger.warning(f"Datum nicht interpretierbar in '{file}': {e}")
                continue

            new_filename = f"{country_code}_{start_iso}_{end_iso}.pdf"
            output_path = output_dir / new_filename

            reader = PdfReader(file_path)
            writer = PdfWriter()
            writer.add_page(reader.pages[0])

            with open(output_path, "wb") as f_out:
                writer.write(f_out)

            logger.info(f"Erste Seite gespeichert als: {output_path}")
            new_paths.append(output_path)

        except Exception as e:
            logger.error(f"Fehler bei Datei {file_path}: {e}")

    return new_paths


if __name__ == "__main__":
    extract_and_save_first_page(ORDNER_EINGANG_WERBUNG, TMP_ORDNER)