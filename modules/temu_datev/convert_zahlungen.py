#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Temu Zahlungsberichte → DATEV Konverter
Verarbeitet ALLE CSV-Dateien im Ordner 'zahlungsberichte/'
"""

import csv
import glob
from pathlib import Path
from config import *
from datev_writer import DatevExtfWriter


class ZahlungenConverter:
    """Konvertiert Temu-Zahlungsberichte zu DATEV-Zahlungsbuchungen"""

    def parse_amount(self, value):
        """Konvertiert '1.234,56' → 1234.56"""
        if not value or value == "":
            return 0.0
        try:
            clean = str(value).strip().replace(".", "").replace(",", ".")
            return float(clean)
        except:
            return 0.0

    def parse_date(self, date_str):
        """
        Konvertiert ISO-Datum in DATEV-Format (ohne Jahr, ohne führende Null beim Tag)
        
        Input:  "2025-12-02 04:35:40" oder "02. Dez 25"
        Output: "212" (Tag ohne führende Null + Monatsnummer)
        """
        try:
            # ISO-Format: "2025-12-02 04:35:40"
            if "-" in date_str and ":" in date_str:
                date_part = date_str.split()[0]  # "2025-12-02"
                year, month, day = date_part.split("-")
                day_no_zero = str(int(day))  # Ohne führende Null
                return f"{day_no_zero}{month}"
            # Deutsches Format: "02. Dez 25"
            else:
                parts = date_str.split()
                day = str(int(parts[0].rstrip('.')))  # Punkt entfernen, ohne führende Null
                month_str = parts[1].rstrip('.')
                month = MONTHS_DE_TO_NUM.get(month_str, "01")
                return f"{day}{month}"
        except:
            return ""

    def process_all_files(self):
        """Verarbeitet alle CSV-Dateien im Zahlungsberichte-Ordner"""
        # Stelle sicher, dass das Output-Verzeichnis existiert
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        csv_files = sorted(glob.glob(str(INPUT_DIR_ZAHLUNGEN / "*.csv")))
        
        if not csv_files:
            print("   ⚠️  Keine CSV-Dateien in 'zahlungsberichte/' gefunden!")
            return

        print(f"   📂 Gefundene Dateien: {len(csv_files)}")
        for f in csv_files:
            print(f"      • {Path(f).name}")
        print()

        writer = DatevExtfWriter(
            OUTPUT_ZAHLUNGEN,
            title="Temu Zahlungen",
            beraternummer=BERATERNUMMER,
            mandantennummer=MANDANTENNUMMER
        )

        total_transactions = 0
        total_bookings = 0

        for csv_file in csv_files:
            print(f"   🔄 Verarbeite: {Path(csv_file).name}")
            transactions, bookings = self.process_file(csv_file, writer)
            total_transactions += transactions
            total_bookings += bookings
            print(f"      → {transactions} Transaktionen, {bookings} Buchungen")

        writer.write()
        print(f"\n   💳 Gesamt: {total_transactions} Transaktionen → {total_bookings} Buchungen")

    def detect_delimiter(self, csv_file):
        """Erkennt automatisch das CSV-Delimiter (Semikolon oder Komma)"""
        with open(csv_file, "r", encoding="utf-8") as f:
            first_line = f.readline()
            # Zähle Vorkommen von Semikolon und Komma
            semicolon_count = first_line.count(";")
            comma_count = first_line.count(",")
            # Wähle das häufigere Zeichen
            return ";" if semicolon_count > comma_count else ","

    def process_file(self, csv_file, writer):
        """Verarbeitet eine einzelne CSV-Datei"""
        transactions_count = 0
        bookings_count = 0

        # Automatische Delimiter-Erkennung
        delimiter = self.detect_delimiter(csv_file)

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                verwandte_id = row.get("Verwandte ID", "").strip()
                bestellid = row.get("Bestell-ID", "").strip()
                transaktionsdatum = row.get("Datum/Uhrzeit", "").strip()
                transaktionstyp = row.get("Transaktionstyp", "").strip()
                
                # Skip empty rows
                if not transaktionsdatum:
                    continue

                transactions_count += 1

                # Parse amounts
                gesamt = self.parse_amount(row.get("Gesamt", 0))
                service_gebuehr = self.parse_amount(row.get("Servicegebühr (inkl. Steuern)", 0))
                plattformanreiz = self.parse_amount(row.get("Plattformanreiz", 0))
                plattformanreiz_versand = self.parse_amount(row.get("Plattformanreiz – Versand", 0))
                sonstiges = self.parse_amount(row.get("Sonstiges", 0))
                
                # Kundenzahlung: Einzelhandelspreis + Temu-Rabatt + Versand + Steuern
                einzelhandelspreis = self.parse_amount(row.get("Einzelhandelspreis", 0))
                temu_rabatt = self.parse_amount(row.get("Temu-Rabatt", 0))
                versand = self.parse_amount(row.get("Versand", 0))
                produktsteuer = self.parse_amount(row.get("Produktsteuer", 0))
                versandsteuer = self.parse_amount(row.get("Versandsteuer", 0))

                # Parse date
                belegdatum = self.parse_date(transaktionsdatum)

                if "order payment" in transaktionstyp.lower():
                    # === ORDER PAYMENT ===
                    # Zahlung vom Kunden eingegangen
                    # BANK (Aktivkonto) wächst im SOLL
                    # DEBITOR (Aktivkonto/Forderung) wird im HABEN gemindert
                    
                    # 1. Kundenzahlung: Einzelhandelspreis + Temu-Rabatt + Versand + Steuern
                    # (VOR Abzug der Servicegebühr - diese wird separat gebucht)
                    # Bank (Soll) an Debitor (Haben)
                    kundenzahlung = einzelhandelspreis + temu_rabatt + versand + produktsteuer + versandsteuer
                    if kundenzahlung != 0 and verwandte_id:
                        writer.add_row(
                            umsatz=abs(kundenzahlung),
                            konto=KONTO_BANK,
                            gegenkonto=KONTO_DEBITOREN,
                            belegdatum=belegdatum,
                            belegfeld1=verwandte_id,
                            buchungstext="Kundenzahlung",
                            bu_schluessel="",
                            haben=False  # SOLL-Buchung (Bank steigt)
                        )
                        bookings_count += 1
                    
                    # 2. Plattformanreiz (Zahlung von Temu): MIT OP-Zuordnung!
                    # WICHTIG: Vorzeichen des Plattformanreizes entscheidet über S/H!
                    # Positiver Plattformanreiz → S-Buchung (Bank steigt), Negativer → H-Buchung
                    if plattformanreiz != 0 and verwandte_id:
                        writer.add_row(
                            umsatz=abs(plattformanreiz),
                            konto=KONTO_BANK,
                            gegenkonto=KONTO_DEBITOREN,
                            belegdatum=belegdatum,
                            belegfeld1=verwandte_id,  # MIT OP! Teil des Zahlungsausgleichs
                            buchungstext="Temu Plattformanreiz",
                            bu_schluessel="",
                            haben=plattformanreiz < 0  # Vorzeichen entscheidet!
                        )
                        bookings_count += 1
                    
                    # 3. Plattformanreiz Versand: MIT OP-Zuordnung!
                    # WICHTIG: Vorzeichen des Plattformanreizes entscheidet über S/H!
                    if plattformanreiz_versand != 0 and verwandte_id:
                        writer.add_row(
                            umsatz=abs(plattformanreiz_versand),
                            konto=KONTO_BANK,
                            gegenkonto=KONTO_DEBITOREN,
                            belegdatum=belegdatum,
                            belegfeld1=verwandte_id,  # MIT OP! Teil des Zahlungsausgleichs
                            buchungstext="Temu Plattformanreiz Versand",
                            bu_schluessel="",
                            haben=plattformanreiz_versand < 0  # Vorzeichen entscheidet!
                        )
                        bookings_count += 1
                    
                    # 4. Gebühren: Bank (Haben) an Aufwandskonto (Soll)
                    # Aufwand wächst im SOLL, Bank sinkt im HABEN
                    if service_gebuehr != 0 and verwandte_id:
                        writer.add_row(
                            umsatz=abs(service_gebuehr),
                            konto=KONTO_BANK,
                            gegenkonto=KONTO_GEBUEHREN,
                            belegdatum=belegdatum,
                            belegfeld1=verwandte_id,
                            buchungstext="Temu Gebühren",
                            bu_schluessel="",
                            haben=True  # HABEN-Buchung (Bank sinkt, Aufwand steigt)
                        )
                        bookings_count += 1

                elif "refund" in transaktionstyp.lower():
                    # === REFUND ===
                    # Rückerstattung an Kunden
                    # S und H werden VERTAUSCHT gegenüber Order Payment!
                    # BANK (Aktivkonto) sinkt im HABEN
                    # DEBITOR (Aktivkonto/Forderung) steigt im SOLL
                    
                    # 1. Kundenrückerstattung: Einzelhandelspreis + Temu-Rabatt + Versand + Steuern
                    # (VOR Abzug der Servicegebühr - diese wird separat gebucht)
                    # Debitor (Soll) an Bank (Haben)
                    kundenerstattung = einzelhandelspreis + temu_rabatt + versand + produktsteuer + versandsteuer
                    if kundenerstattung != 0 and verwandte_id:
                        writer.add_row(
                            umsatz=abs(kundenerstattung),
                            konto=KONTO_BANK,
                            gegenkonto=KONTO_DEBITOREN,
                            belegdatum=belegdatum,
                            belegfeld1=verwandte_id,
                            buchungstext="Kundenzahlung",
                            bu_schluessel="",
                            haben=True  # HABEN-Buchung (Bank sinkt)
                        )
                        bookings_count += 1
                    
                    # 2. Plattformanreiz Rückbuchung: MIT OP-Zuordnung!
                    # WICHTIG: Vorzeichen des Plattformanreizes entscheidet über S/H!
                    if plattformanreiz != 0 and verwandte_id:
                        writer.add_row(
                            umsatz=abs(plattformanreiz),
                            konto=KONTO_BANK,
                            gegenkonto=KONTO_DEBITOREN,
                            belegdatum=belegdatum,
                            belegfeld1=verwandte_id,  # MIT OP!
                            buchungstext="Temu Plattformanreiz",
                            bu_schluessel="",
                            haben=plattformanreiz < 0  # Vorzeichen entscheidet!
                        )
                        bookings_count += 1
                    
                    # 3. Plattformanreiz Versand Rückbuchung: MIT OP-Zuordnung!
                    # WICHTIG: Vorzeichen des Plattformanreizes entscheidet über S/H!
                    if plattformanreiz_versand != 0 and verwandte_id:
                        writer.add_row(
                            umsatz=abs(plattformanreiz_versand),
                            konto=KONTO_BANK,
                            gegenkonto=KONTO_DEBITOREN,
                            belegdatum=belegdatum,
                            belegfeld1=verwandte_id,  # MIT OP!
                            buchungstext="Temu Plattformanreiz Versand",
                            bu_schluessel="",
                            haben=plattformanreiz_versand < 0  # Vorzeichen entscheidet!
                        )
                        bookings_count += 1
                    
                    # 4. Gebühren Erstattung: Aufwandskonto (Haben) an Bank (Soll)
                    # Aufwand sinkt im HABEN, Bank steigt im SOLL
                    if service_gebuehr != 0 and verwandte_id:
                        writer.add_row(
                            umsatz=abs(service_gebuehr),
                            konto=KONTO_BANK,
                            gegenkonto=KONTO_GEBUEHREN,
                            belegdatum=belegdatum,
                            belegfeld1=verwandte_id,
                            buchungstext="Temu Gebühren",
                            bu_schluessel="",
                            haben=False  # SOLL-Buchung (Bank steigt, Aufwand sinkt)
                        )
                        bookings_count += 1

                elif "transfer" in transaktionstyp.lower():
                    # === TRANSFER ===
                    # Transfer von Temu-Bank an Sparkasse
                    # Bank an Geldtransit (Soll an Haben)
                    # Betrag aus "Sonstiges", Belegfeld1 = Verwandte ID
                    if sonstiges != 0 and verwandte_id:
                        writer.add_row(
                            umsatz=abs(sonstiges),
                            konto=KONTO_BANK,
                            gegenkonto=KONTO_TRANSIT,
                            belegdatum=belegdatum,
                            belegfeld1=verwandte_id,
                            buchungstext="Geldtransit",
                            bu_schluessel="",
                            haben=False  # SOLL-Buchung (Bank an Transit)
                        )
                        bookings_count += 1

                elif "shipping label" in transaktionstyp.lower():
                    # === SHIPPING LABEL ===
                    # Rücksendeetiketten als Aufwand
                    # Betrag aus "Sonstiges", Belegfeld1 = Verwandte ID
                    # Buchungstext = "Shipping Label" + Bestell-ID
                    if sonstiges != 0 and verwandte_id:
                        buchungstext = f"Shipping Label {bestellid}" if bestellid else "Shipping Label"
                        writer.add_row(
                            umsatz=abs(sonstiges),
                            konto=KONTO_BANK,
                            gegenkonto=KONTO_GEBUEHREN,
                            belegdatum=belegdatum,
                            belegfeld1=verwandte_id,
                            buchungstext=buchungstext,
                            bu_schluessel="",
                            haben=True  # HABEN-Buchung (Bank sinkt, Aufwand steigt)
                        )
                        bookings_count += 1

                elif "deduction" in transaktionstyp.lower():
                    # === STRAFZAHLUNGEN ===
                    # Strafzahlung als Aufwand (Late fulfillment etc.)
                    # Betrag aus "Sonstiges", Belegfeld1 = Verwandte ID
                    # Buchungstext = Bestell-ID
                    if sonstiges != 0 and verwandte_id:
                        buchungstext = bestellid if bestellid else "Strafzahlung"
                        writer.add_row(
                            umsatz=abs(sonstiges),
                            konto=KONTO_BANK,
                            gegenkonto=KONTO_STRAFZAHLUNGEN,
                            belegdatum=belegdatum,
                            belegfeld1=verwandte_id,
                            buchungstext=buchungstext,
                            bu_schluessel="",
                            haben=True  # HABEN-Buchung (Bank sinkt, Aufwand steigt)
                        )
                        bookings_count += 1

        return transactions_count, bookings_count

    def convert(self):
        """Hauptfunktion: Konvertiert alle Zahlungsberichte"""
        print("💳 ZAHLUNGSBERICHTE → DATEV")
        print("=" * 60)
        self.process_all_files()
        print("=" * 60)


if __name__ == "__main__":
    converter = ZahlungenConverter()
    converter.convert()
