"""CLI for PDF Reader services.

Usage examples:
- Extract first pages for ads: python -m src.modules.pdf_reader.cli extract-werbung
- Process ads to Excel:      python -m src.modules.pdf_reader.cli process-werbung
- Process invoices to Excel: python -m src.modules.pdf_reader.cli process-rechnungen
"""

from pathlib import Path
import argparse
import sys

from .config import ORDNER_EINGANG_WERBUNG, ORDNER_EINGANG_RECHNUNGEN, TMP_ORDNER, ORDNER_AUSGANG
from .werbung_extraction_service import extract_and_save_first_page
from .werbung_service import process_ad_pdfs
from .rechnungen_service import process_rechnungen


def cmd_extract_werbung() -> None:
    extract_and_save_first_page(input_dir=ORDNER_EINGANG_WERBUNG, output_dir=TMP_ORDNER)
    print(f"Extracted pages to: {TMP_ORDNER}")


def cmd_process_werbung() -> None:
    output_excel = ORDNER_AUSGANG / "werbung.xlsx"
    process_ad_pdfs(directory=TMP_ORDNER, output_excel=output_excel)
    print(f"Werbung Excel written: {output_excel}")


def cmd_process_rechnungen() -> None:
    output_excel = ORDNER_AUSGANG / "rechnungen.xlsx"
    process_rechnungen(directory=ORDNER_EINGANG_RECHNUNGEN, output_excel=output_excel)
    print(f"Rechnungen Excel written: {output_excel}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PDF Reader CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("extract-werbung", help="Extract first pages from ad PDFs to TMP")
    sub.add_parser("process-werbung", help="Process extracted ads and export Excel")
    sub.add_parser("process-rechnungen", help="Process invoice PDFs and export Excel")

    args = parser.parse_args(argv)

    if args.cmd == "extract-werbung":
        cmd_extract_werbung()
    elif args.cmd == "process-werbung":
        cmd_process_werbung()
    elif args.cmd == "process-rechnungen":
        cmd_process_rechnungen()
    else:
        parser.print_help()
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
