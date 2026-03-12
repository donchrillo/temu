#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DATEV EXTF Writer - Gemeinsame Klasse für DATEV-Export
"""

import csv
import shutil
from datetime import datetime
from pathlib import Path


class DatevExtfWriter:
    """Schreibt DATEV EXTF (700;21 Buchungsstapel) Format"""

    HEADER_TEMPLATE = (
        "EXTF;700;21;Buchungsstapel;12;{timestamp};;PY;TEMU2DATEV;;{beraternummer};"
        "{mandantennummer};20250101;4;20251201;20251231;{title};;1;0;0;EUR;"
        "{empty_fields}"
    )

    COLUMNS = (
        "Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;WKZ Umsatz;Kurs;Basis-Umsatz;"
        "WKZ Basis-Umsatz;Konto;Gegenkonto (ohne BU-Schlüssel);BU-Schlüssel;Belegdatum;"
        "Belegfeld 1;Belegfeld 2;Skonto;Buchungstext;Postensperre;Diverse Adressnummer;"
        "Geschäftspartnerbank;Sachverhalt;Zinssperre;Beleglink;Beleginfo - Art 1;"
        "Beleginfo - Inhalt 1;Beleginfo - Art 2;Beleginfo - Inhalt 2;Beleginfo - Art 3;"
        "Beleginfo - Inhalt 3;Beleginfo - Art 4;Beleginfo - Inhalt 4;Beleginfo - Art 5;"
        "Beleginfo - Inhalt 5;Beleginfo - Art 6;Beleginfo - Inhalt 6;Beleginfo - Art 7;"
        "Beleginfo - Inhalt 7;Beleginfo - Art 8;Beleginfo - Inhalt 8;KOST1 - Kostenstelle;"
        "KOST2 - Kostenstelle;Kost-Menge;EU-Land und UStID (Bestimmung);EU-Steuersatz "
        "(Bestimmung);Abw. Versteuerungsart;Sachverhalt L+L;Funktionsergänzung L+L;"
        "BU 49 Hauptfunktionstyp;BU 49 Hauptfunktionsnummer;BU 49 Funktionsergänzung;"
        "Zusatzinformation - Art 1;Zusatzinformation- Inhalt 1;Zusatzinformation - Art 2;"
        "Zusatzinformation- Inhalt 2;Zusatzinformation - Art 3;Zusatzinformation- Inhalt 3;"
        "Zusatzinformation - Art 4;Zusatzinformation- Inhalt 4;Zusatzinformation - Art 5;"
        "Zusatzinformation- Inhalt 5;Zusatzinformation - Art 6;Zusatzinformation- Inhalt 6;"
        "Zusatzinformation - Art 7;Zusatzinformation- Inhalt 7;Zusatzinformation - Art 8;"
        "Zusatzinformation- Inhalt 8;Zusatzinformation - Art 9;Zusatzinformation- Inhalt 9;"
        "Zusatzinformation - Art 10;Zusatzinformation- Inhalt 10;Zusatzinformation - Art 11;"
        "Zusatzinformation- Inhalt 11;Zusatzinformation - Art 12;Zusatzinformation- Inhalt 12;"
        "Zusatzinformation - Art 13;Zusatzinformation- Inhalt 13;Zusatzinformation - Art 14;"
        "Zusatzinformation- Inhalt 14;Zusatzinformation - Art 15;Zusatzinformation- Inhalt 15;"
        "Zusatzinformation - Art 16;Zusatzinformation- Inhalt 16;Zusatzinformation - Art 17;"
        "Zusatzinformation- Inhalt 17;Zusatzinformation - Art 18;Zusatzinformation- Inhalt 18;"
        "Zusatzinformation - Art 19;Zusatzinformation- Inhalt 19;Zusatzinformation - Art 20;"
        "Zusatzinformation- Inhalt 20;Stück;Gewicht;Zahlweise;Forderungsart;Veranlagungsjahr;"
        "Zugeordnete Fälligkeit;Skontotyp;Auftragsnummer;Buchungstyp;Ust-Schlüssel "
        "(Anzahlungen);EU-Land (Anzahlungen);Sachverhalt L+L (Anzahlungen);EU-Steuersatz "
        "(Anzahlungen);Erlöskonto (Anzahlungen);Herkunft-Kz;Leerfeld;KOST-Datum;"
        "Mandatsreferenz;Skontosperre;Gesellschaftername;Beteiligtennummer;"
        "Identifikationsnummer;Zeichnernummer;Postensperre bis;Bezeichnung SoBil-Sachverhalt;"
        "Kennzeichen SoBil-Buchung;Festschreibung;Leistungsdatum;Datum Zuord.Steuerperiode;"
        "Fälligkeit;Generalumkehr (GU);Steuersatz;Land;Abrechnungsreferenz;BVV-Postion;"
        "EU-Land und UStID (Ursprung);EU-Steuersatz (Ursprung)"
    )

    def __init__(
        self,
        output_path,
        title="Temu Buchungen",
        beraternummer=10305,
        mandantennummer=70001
    ):
        self.output_path = Path(output_path)
        self.title = title
        self.beraternummer = beraternummer
        self.mandantennummer = mandantennummer
        self.rows = []
        self.new_invoices = set()
        self.new_stornos = set()

    def add_new_invoice(self, invoice_number):
        """Track neue Rechnungsnummer für Export-Status"""
        self.new_invoices.add(invoice_number)

    def add_new_storno(self, order_number):
        """Track neue Storno-Bestellnummer für Export-Status"""
        self.new_stornos.add(order_number)

    def add_row(
        self,
        umsatz,
        konto,
        gegenkonto,
        belegdatum,
        belegfeld1,
        buchungstext="",
        bu_schluessel="",
        haben=False,
        belegfeld2=""
    ):
        """Fügt eine Buchungszeile hinzu"""
        sh_kz = "H" if haben else "S"
        umsatz_str = str(round(float(umsatz), 2)).replace(".", ",")

        # Standardisierte Belegdatum-Konvertierung (DD.MM.YY → DDMMYY)
        if isinstance(belegdatum, str) and "." in belegdatum:
            parts = belegdatum.split(".")
            if len(parts) == 3:
                belegdatum = f"{int(parts[0]):02d}{int(parts[1]):02d}{parts[2][-2:]}"
            else:
                belegdatum = ""

        # Erstelle leere Zeile (117 Felder)
        row = [""] * 117
        row[0] = umsatz_str              # Umsatz
        row[1] = sh_kz                   # S/H
        row[6] = str(konto)              # Konto
        row[7] = str(gegenkonto)         # Gegenkonto
        row[8] = bu_schluessel           # BU-Schlüssel
        row[9] = belegdatum              # Belegdatum
        row[10] = belegfeld1             # Belegfeld 1
        row[11] = belegfeld2             # Belegfeld 2
        row[13] = buchungstext           # Buchungstext

        self.rows.append(row)

    def write(self):
        """Schreibt Header + alle Buchungszeilen in die DATEV-Datei"""
        # Timestamp für Header: JJJJMMTTHHMMSSTTT
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S000")

        # Vorhandene Exportdatei archivieren, damit OP-Abgleich über mehrere
        # Monate auf historischen DATEV-Ständen aufbauen kann.
        if self.output_path.exists():
            history_dir = self.output_path.parent / ".history"
            history_dir.mkdir(parents=True, exist_ok=True)
            archive_name = f"{self.output_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{self.output_path.suffix}"
            shutil.copy2(self.output_path, history_dir / archive_name)
            print(f"   📦 Archiviert: .history/{archive_name}")

        # Header erstellen
        empty_fields = ";" * (117 - self.HEADER_TEMPLATE.count(";") - 1)
        header = self.HEADER_TEMPLATE.format(
            timestamp=timestamp,
            beraternummer=self.beraternummer,
            mandantennummer=self.mandantennummer,
            title=self.title,
            empty_fields=empty_fields
        )

        # Datei schreiben
        with open(self.output_path, "w", encoding="utf-8", newline="") as f:
            f.write(header + "\n")
            f.write(self.COLUMNS + "\n")

            writer = csv.writer(f, delimiter=";", quoting=csv.QUOTE_MINIMAL)
            for row in self.rows:
                writer.writerow(row)

        print(f"   ✓ {self.output_path.name} - {len(self.rows)} Buchungszeilen")
