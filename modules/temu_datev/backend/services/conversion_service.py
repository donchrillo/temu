from __future__ import annotations

from pathlib import Path
from typing import List

from config import (
    OUTPUT_DIR,
    OUTPUT_BESTELLUNGEN,
    OUTPUT_ZAHLUNGEN,
    INPUT_DIR_BESTELLUNGEN,
    INPUT_DIR_ZAHLUNGEN,
    BERATERNUMMER,
    MANDANTENNUMMER,
)
from convert_bestellungen import BestellungenConverter
from convert_zahlungen import ZahlungenConverter
from datev_writer import DatevExtfWriter
from simulate_op_buchungen import main as run_op_main


def convert_orders(files: List[Path]) -> dict:
    converter = BestellungenConverter()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    exported_invoices, exported_storno_orders = converter.load_export_state()
    writer = DatevExtfWriter(
        OUTPUT_BESTELLUNGEN,
        title="Temu Bestellungen",
        beraternummer=BERATERNUMMER,
        mandantennummer=MANDANTENNUMMER,
    )

    total_orders = 0
    total_bookings = 0
    skipped_count = 0
    ignored_count = 0
    file_details = []
    ignored_rows = []

    for csv_file in files:
        orders, bookings, skipped, ignored, ignored_in_file = converter.process_file(
            str(csv_file), writer, exported_invoices, exported_storno_orders
        )
        total_orders += orders
        total_bookings += bookings
        skipped_count += skipped
        ignored_count += ignored
        file_details.append(
            {
                "filename": csv_file.name,
                "records": orders,
                "bookings": bookings,
                "skipped": skipped,
                "ignored": ignored,
            }
        )
        ignored_rows.extend(
            {
                "filename": csv_file.name,
                "bestellnummer": row["bestellnummer"],
                "rechnungsnummer": row["rechnungsnummer"],
                "verkaufsart": row["verkaufsart"],
                "grund": row["grund"],
            }
            for row in ignored_in_file
        )

    output_files: List[str] = []
    if total_bookings > 0:
        writer.write()
        all_exported_invoices = exported_invoices | writer.new_invoices
        all_exported_stornos = exported_storno_orders | writer.new_stornos
        converter.save_export_state(
            all_exported_invoices,
            all_exported_stornos,
            len(writer.new_invoices),
            len(writer.new_stornos),
        )
        output_files.append(OUTPUT_BESTELLUNGEN.name)

    notes = []
    if skipped_count > 0:
        notes.append(f"{skipped_count} bereits exportierte Eintraege wurden uebersprungen")
    if ignored_count > 0:
        notes.append(f"{ignored_count} fachlich nicht buchbare Eintraege wurden ignoriert")
    if total_bookings == 0:
        notes.append("Keine neuen Buchungen erzeugt")
    else:
        notes.append(
            f"{len(writer.new_invoices)} neue Rechnungen und {len(writer.new_stornos)} neue Stornos gespeichert"
        )

    return {
        "message": "Bestellberichte verarbeitet",
        "totals": {
            "orders": total_orders,
            "bookings": total_bookings,
            "skipped": skipped_count,
            "ignored": ignored_count,
        },
        "output_files": output_files,
        "details": {
            "mode": "orders",
            "files": file_details,
            "notes": notes,
            "ignored_rows": ignored_rows[:200],
        },
    }


def convert_payments(files: List[Path]) -> dict:
    converter = ZahlungenConverter()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    writer = DatevExtfWriter(
        OUTPUT_ZAHLUNGEN,
        title="Temu Zahlungen",
        beraternummer=BERATERNUMMER,
        mandantennummer=MANDANTENNUMMER,
    )

    total_transactions = 0
    total_bookings = 0
    file_details = []

    for csv_file in files:
        transactions, bookings = converter.process_file(str(csv_file), writer)
        total_transactions += transactions
        total_bookings += bookings
        file_details.append(
            {
                "filename": csv_file.name,
                "records": transactions,
                "bookings": bookings,
                "skipped": 0,
                "ignored": 0,
            }
        )

    output_files: List[str] = []
    if total_bookings > 0:
        writer.write()
        output_files.append(OUTPUT_ZAHLUNGEN.name)

    notes = []
    if total_bookings == 0:
        notes.append("Keine Buchungen aus den gewaehlten Zahlungsberichten erzeugt")
    else:
        notes.append("Zahlungsbuchungen wurden in den DATEV-Export geschrieben")

    return {
        "message": "Zahlungsberichte verarbeitet",
        "totals": {
            "transactions": total_transactions,
            "bookings": total_bookings,
        },
        "output_files": output_files,
        "details": {
            "mode": "payments",
            "files": file_details,
            "notes": notes,
        },
    }


def run_op_analysis() -> dict:
    summary = run_op_main()
    output_files = []
    for filename in ["OP_Analyse.md", "OP_Nicht_Ausgeglichen.csv"]:
        path = OUTPUT_DIR / filename
        if path.exists():
            output_files.append(path.name)

    return {
        "message": "OP-Analyse erstellt",
        "output_files": output_files,
        "summary": summary,
    }


def list_exports() -> List[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return [p for p in sorted(OUTPUT_DIR.glob("*")) if p.is_file()]
