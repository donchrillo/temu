#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Temu Bestellberichte → DATEV Konverter
Verarbeitet ALLE CSV-Dateien im Ordner 'bestellberichte/'
"""

import csv
import glob
import json
from datetime import datetime
from pathlib import Path
from config import *
from datev_writer import DatevExtfWriter


class BestellungenConverter:
    """Konvertiert Temu-Bestellberichte zu DATEV-Belegen"""

    def __init__(self):
        self.state_file = OUTPUT_DIR / ".datev_export_state.json"

    def load_export_state(self):
        """
        Lädt bereits exportierte Rechnungsnummern und Storno-Bestellnummern
        aus JSON State-File.
        
        Returns:
            tuple: (exported_invoices: set, exported_storno_orders: set)
        """
        if not self.state_file.exists():
            return set(), set()
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            exported_invoices = set(state.get('exported_invoices', []))
            exported_storno_orders = set(state.get('exported_storno_orders', []))
            
            print(f"   📋 Bereits exportiert: {len(exported_invoices)} Rechnungen, {len(exported_storno_orders)} Stornos")
            return exported_invoices, exported_storno_orders
        except Exception as e:
            print(f"   ⚠️  Fehler beim Laden des Export-Status: {e}")
            return set(), set()

    def save_export_state(self, exported_invoices, exported_storno_orders, new_invoices_count, new_stornos_count):
        """
        Speichert Export-Status in JSON-Datei.
        Fügt neue Einträge zu bestehenden hinzu.
        """
        state = {
            'last_export': datetime.now().isoformat(),
            'exported_invoices': sorted(list(exported_invoices)),
            'exported_storno_orders': sorted(list(exported_storno_orders))
        }
        
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            print(f"   💾 Export-Status gespeichert: {new_invoices_count} neue Rechnungen, {new_stornos_count} neue Stornos")
        except Exception as e:
            print(f"   ⚠️  Fehler beim Speichern des Export-Status: {e}")

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
        Konvertiert deutsches Datum in DATEV-Format (ohne Jahr, ohne führende Null beim Tag)
        
        Input:  "2. Dez. 2025" oder "02. Dez 25"
        Output: "212" (Tag ohne führende Null + Monatsnummer)
        
        Beispiele: 112 (1. Dez), 1312 (13. Dez), 2412 (24. Dez)
        """
        try:
            parts = date_str.split()
            day = str(int(parts[0].rstrip('.')))  # Punkt entfernen, ohne führende Null
            # Monat kann mit oder ohne Punkt sein: "Dez" oder "Dez."
            month_str = parts[1].rstrip('.')
            month = MONTHS_DE_TO_NUM.get(month_str, "01")
            return f"{day}{month}"
        except:
            return ""

    def process_all_files(self):
        """Verarbeitet alle CSV-Dateien im Bestellberichte-Ordner"""
        # Stelle sicher, dass das Output-Verzeichnis existiert
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        csv_files = sorted(glob.glob(str(INPUT_DIR_BESTELLUNGEN / "*.csv")))
        
        if not csv_files:
            print("   ⚠️  Keine CSV-Dateien in 'bestellberichte/' gefunden!")
            return

        print(f"   📂 Gefundene Dateien: {len(csv_files)}")
        for f in csv_files:
            print(f"      • {Path(f).name}")
        print()

        # Lade bereits exportierte Einträge
        exported_invoices, exported_storno_orders = self.load_export_state()

        writer = DatevExtfWriter(
            OUTPUT_BESTELLUNGEN,
            title="Temu Bestellungen",
            beraternummer=BERATERNUMMER,
            mandantennummer=MANDANTENNUMMER
        )

        total_orders = 0
        total_bookings = 0
        skipped_count = 0
        ignored_count = 0

        for csv_file in csv_files:
            print(f"   🔄 Verarbeite: {Path(csv_file).name}")
            orders, bookings, skipped, ignored, _ignored_rows = self.process_file(
                csv_file, writer, exported_invoices, exported_storno_orders
            )
            total_orders += orders
            total_bookings += bookings
            skipped_count += skipped
            ignored_count += ignored
            print(
                f"      → {orders} Bestellungen, {bookings} Buchungen, "
                f"{skipped} uebersprungen, {ignored} ignoriert"
            )

        # Nur schreiben wenn neue Buchungen vorhanden sind
        if total_bookings > 0:
            writer.write()
            
            # Aktualisiere Export-Status mit neuen Einträgen vom Writer
            all_exported_invoices = exported_invoices | writer.new_invoices
            all_exported_stornos = exported_storno_orders | writer.new_stornos
            self.save_export_state(
                all_exported_invoices, 
                all_exported_stornos,
                len(writer.new_invoices),
                len(writer.new_stornos)
            )
            
            print(f"\n   📊 Gesamt: {total_orders} Bestellungen → {total_bookings} Buchungen")
        else:
            print(f"\n   ✅ Keine neuen Buchungen - Export-Status bleibt unverändert")
        
        if skipped_count > 0:
            print(f"   ⏭️  Übersprungen: {skipped_count} bereits exportiert")
        if ignored_count > 0:
            print(f"   🚫 Ignoriert: {ignored_count} fachlich nicht buchbar")

    def detect_delimiter(self, csv_file):
        """Erkennt automatisch das CSV-Delimiter (Semikolon oder Komma)"""
        with open(csv_file, "r", encoding="utf-8") as f:
            first_line = f.readline()
            # Zähle Vorkommen von Semikolon und Komma
            semicolon_count = first_line.count(";")
            comma_count = first_line.count(",")
            # Wähle das häufigere Zeichen
            return ";" if semicolon_count > comma_count else ","

    def process_file(self, csv_file, writer, exported_invoices, exported_storno_orders):
        """Verarbeitet eine einzelne CSV-Datei"""
        orders_count = 0
        bookings_count = 0
        skipped_count = 0
        ignored_count = 0
        ignored_rows = []

        # Automatische Delimiter-Erkennung
        delimiter = self.detect_delimiter(csv_file)

        # Erste Pass: Sammle alle Bestellnummern ohne Rechnungsnummer
        bestellungen_ohne_rechnung = {}
        
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                bestellnummer = row.get("BESTELLNUMMER", "").strip()
                rechnungsnummer = row.get("RECHNUNGSNUMMER", "").strip()
                verkaufsart = row.get("VERKAUFSART", "").strip().lower()
                
                if not bestellnummer:
                    continue
                    
                # Track Bestellungen ohne Rechnungsnummer
                if not rechnungsnummer:
                    if bestellnummer not in bestellungen_ohne_rechnung:
                        bestellungen_ohne_rechnung[bestellnummer] = []
                    bestellungen_ohne_rechnung[bestellnummer].append(verkaufsart)
        
        # Identifiziere echte Storno-Paare (sales + return ohne Rechnung)
        echte_stornos = set()
        for bestellnr, arten in bestellungen_ohne_rechnung.items():
            if "sales" in arten and "return" in arten:
                echte_stornos.add(bestellnr)

        # Zweiter Pass: Verarbeite die Bestellungen
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                bestellnummer = row.get("BESTELLNUMMER", "").strip()
                rechnungsnummer = row.get("RECHNUNGSNUMMER", "").strip()
                zuschuss_rechnungsnummer = row.get("SUBVENTIONSRECHNUNGSNUMMER", "").strip()
                zahlungsdatum = row.get("ZAHLUNGSDATUM DER BESTELLUNG", "").strip()
                verkaufsart = row.get("VERKAUFSART", "").strip().lower()

                # Skip empty rows
                if not bestellnummer:
                    continue

                orders_count += 1
                row_had_booking = False
                row_skipped = False

                # Parse amounts (neue Spaltennamen)
                artikel_netto = self.parse_amount(row.get("PREIS DER ARTIKEL (OHNE UST.)", 0))
                versand_netto = self.parse_amount(row.get("PREIS DER SENDUNG (OHNE UST.)", 0))
                artikel_steuer = self.parse_amount(row.get("UMSATZSTEUERBETRAG DER ARTIKEL", 0))
                versand_steuer = self.parse_amount(row.get("UMSATZSTEUERBETRAG DER SENDUNG", 0))
                
                # Zuschüsse: Alle Spalten mit "ZUSCHUSS" aufaddieren
                zuschuss_artikel_netto = self.parse_amount(row.get("ZUSCHUSSPREIS (OHNE UST.)", 0))
                zuschuss_versand_netto = self.parse_amount(row.get("VERSANDZUSCHUSSPREIS (OHNE MWST.)", 0))
                zuschuss_artikel_steuer = self.parse_amount(row.get("UMSATZSTEUERBETRAG DES ZUSCHUSSES", 0))
                zuschuss_versand_steuer = self.parse_amount(row.get("MEHRWERTSTEUERBETRAG DES VERSANDZUSCHUSSES", 0))

                # Parse date
                belegdatum = self.parse_date(zahlungsdatum)

                hauptbetrag = artikel_netto + versand_netto + artikel_steuer + versand_steuer
                hat_hauptbetrag = hauptbetrag != 0
                hat_zuschuss_rechnung = bool(zuschuss_rechnungsnummer and zuschuss_rechnungsnummer.strip())
                zuschuss_brutto = (
                    zuschuss_artikel_netto + zuschuss_versand_netto + zuschuss_artikel_steuer + zuschuss_versand_steuer
                )
                hat_zuschuss_betrag = zuschuss_brutto != 0

                # S/H-Kennzeichen
                haben = verkaufsart == "return"
                ignore_reason = ""

                # === HAUPTBUCHUNG: Artikel + Versand (Brutto) ===
                # Nur Artikel- und Versandsteuern, KEINE Zuschuss-Steuern!
                if hat_hauptbetrag:
                    brutto = hauptbetrag

                    # Buchungstext bestimmen
                    if rechnungsnummer:
                        # Check: Rechnungsnummer bereits exportiert?
                        if rechnungsnummer in exported_invoices:
                            skipped_count += 1
                            row_skipped = True
                            continue
                        buchungstext = rechnungsnummer
                        writer.add_new_invoice(rechnungsnummer)  # Track neue Rechnung
                    elif bestellnummer in echte_stornos:
                        # Check: Storno bereits exportiert?
                        if bestellnummer in exported_storno_orders:
                            skipped_count += 1
                            row_skipped = True
                            continue
                        # Nur echte Storno-Paare buchen
                        buchungstext = "Storno vor Versand"
                        writer.add_new_storno(bestellnummer)  # Track neuer Storno
                    else:
                        # Einzelne Bestellungen ohne Rechnung gelten als fachlich nicht buchbar
                        buchungstext = None
                        ignore_reason = "Ohne Rechnungsnummer und kein Storno-Paar"

                    if buchungstext is not None:
                        writer.add_row(
                            umsatz=abs(brutto),
                            konto=KONTO_DEBITOREN,
                            gegenkonto=KONTO_ERLOESE,
                            belegdatum=belegdatum,
                            belegfeld1=bestellnummer,
                            buchungstext=buchungstext,
                            bu_schluessel="",
                            haben=haben
                        )
                        bookings_count += 1
                        row_had_booking = True

                # === ZUSCHUSS-BUCHUNG (separat als Brutto) ===
                # Mit OP-Zuordnung, da Teil der Kundenzahlung
                if hat_zuschuss_rechnung:
                    # Check: Zuschuss-Rechnungsnummer bereits exportiert?
                    if zuschuss_rechnungsnummer in exported_invoices:
                        skipped_count += 1
                        row_skipped = True
                        continue
                    
                    writer.add_new_invoice(zuschuss_rechnungsnummer)  # Track neue Zuschuss-Rechnung
                    
                    # Nur buchen wenn Betrag != 0
                    if zuschuss_brutto != 0:
                        # WICHTIG: Vorzeichen des Zuschusses entscheidet über S/H!
                        # Positiver Zuschuss (auch bei return möglich!) → S-Buchung
                        # Negativer Zuschuss (Storno) → H-Buchung
                        zuschuss_haben = zuschuss_brutto < 0
                        
                        # Buchungstext: CN bei negativem Zuschuss, INV bei positivem
                        if zuschuss_haben:
                            zuschuss_text = f"Zuschuss-Storno {rechnungsnummer}" if rechnungsnummer else f"Zuschuss-Storno zu {bestellnummer}"
                        else:
                            zuschuss_text = f"Zuschuss {zuschuss_rechnungsnummer}"
                        
                        writer.add_row(
                            umsatz=abs(zuschuss_brutto),
                            konto=KONTO_DEBITOREN,
                            gegenkonto=KONTO_ERLOESE,
                            belegdatum=belegdatum,
                            belegfeld1=bestellnummer,  # MIT OP! Teil der Kundenzahlung
                            buchungstext=zuschuss_text,
                            bu_schluessel="",
                            haben=zuschuss_haben  # Vorzeichen entscheidet!
                        )
                        bookings_count += 1
                        row_had_booking = True
                    elif not ignore_reason:
                        ignore_reason = "Zuschuss-Rechnung ohne buchbaren Zuschussbetrag"

                if not row_had_booking and not row_skipped:
                    ignored_count += 1
                    if not ignore_reason:
                        if not hat_hauptbetrag and not hat_zuschuss_rechnung:
                            ignore_reason = "Kein Hauptbetrag und keine Zuschuss-Rechnung"
                        elif not hat_hauptbetrag and hat_zuschuss_rechnung and not hat_zuschuss_betrag:
                            ignore_reason = "Zuschuss-Rechnung ohne buchbaren Zuschussbetrag"
                        else:
                            ignore_reason = "Fachlich nicht buchbar"

                    ignored_rows.append(
                        {
                            "bestellnummer": bestellnummer,
                            "rechnungsnummer": rechnungsnummer,
                            "verkaufsart": verkaufsart,
                            "grund": ignore_reason,
                        }
                    )

        return orders_count, bookings_count, skipped_count, ignored_count, ignored_rows

    def convert(self):
        """Hauptfunktion: Konvertiert alle Bestellberichte"""
        print("📊 BESTELLBERICHTE → DATEV")
        print("=" * 60)
        self.process_all_files()
        print("=" * 60)


if __name__ == "__main__":
    converter = BestellungenConverter()
    converter.convert()
