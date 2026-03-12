#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zentrale Konfiguration für Temu → DATEV Konverter
"""

from pathlib import Path

# === DATEV KONFIGURATION ===
BERATERNUMMER = 10305       # DATEV Beraternummer
MANDANTENNUMMER = 70001     # DATEV Mandantennummer

# === SKR04 KONTEN-KONFIGURATION ===
KONTO_BANK = 1860070              # BAnkkonto für Marktplatz TEMU
KONTO_DEBITOREN = 10012000        # TEMU Debitorenkonto (Kundenrechnungen)
KONTO_TRANSIT = 1460070           # Geldtransit
KONTO_ERLOESE = 4400000           # Erlöse 19% DE
KONTO_GEBUEHREN = 6770060         # Service-Gebühren TEMU
KONTO_VERSAND_LABEL = 6770060        # Rücksendeetiketten
KONTO_STRAFZAHLUNGEN = 6770060       # Strafzahlungen
KONTO_PLATTFORMANREIZ = 4400000   # Plattformanreize (Zuschüsse von Temu)

# === PFAD-KONFIGURATION ===
PROJECT_ROOT = Path(__file__).parent
INPUT_DIR_BESTELLUNGEN = PROJECT_ROOT / "bestellberichte"
INPUT_DIR_ZAHLUNGEN = PROJECT_ROOT / "zahlungsberichte"
OUTPUT_DIR = PROJECT_ROOT / "export"

# === OUTPUT-DATEIEN ===
OUTPUT_BESTELLUNGEN = OUTPUT_DIR / "Temu_Bestellungen.csv"
OUTPUT_ZAHLUNGEN = OUTPUT_DIR / "Temu_zahlung.csv"

# === DATEV EXTF EINSTELLUNGEN ===
EXTF_VERSION = "700;21"
EXTF_FORMAT = "Buchungsstapel"
WIRTSCHAFTSJAHR_START = "20250101"  # Format: JJJJMMTT
WIRTSCHAFTSJAHR_ENDE = "20251231"   # Format: JJJJMMTT
PERIODE_VON = "20251201"            # Format: JJJJMMTT
PERIODE_BIS = "20251231"            # Format: JJJJMMTT

# === MONATS-MAPPING (für Datumskonvertierung) ===
MONTHS_DE_TO_NUM = {
    # Kurze Varianten (2-4 Buchstaben)
    "Jan": "01", "Feb": "02", "Mär": "03", "Apr": "04",
    "Mai": "05", "Jun": "06", "Jul": "07", "Aug": "08",
    "Sep": "09", "Okt": "10", "Nov": "11", "Dez": "12",
    # Längere/Alternative Varianten (deutsche Abkürzungen)
    "Febr": "02", "Mrz": "03", "Juni": "06", "Juli": "07",
    "Sept": "09", "Okt.": "10", "Dez.": "12",
    # Vollständige deutsche Monatsnamen (falls diese auch vorkommen)
    "Januar": "01", "Februar": "02", "März": "03", "April": "04",
    "Juni": "06", "Juli": "07", "August": "08", "September": "09",
    "Oktober": "10", "November": "11", "Dezember": "12"
}
