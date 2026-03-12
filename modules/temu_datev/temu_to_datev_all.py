#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Temu → DATEV Master-Konverter
Führt beide Konvertierungen (Bestellungen + Zahlungen) nacheinander aus
"""

from convert_bestellungen import BestellungenConverter
from convert_zahlungen import ZahlungenConverter


def main():
    """Hauptfunktion: Konvertiert alle Temu-Berichte zu DATEV"""
    print("\n" + "=" * 70)
    print("  🚀 TEMU → DATEV KONVERTER")
    print("=" * 70 + "\n")

    # 1. Bestellberichte konvertieren
    print("SCHRITT 1/2: Bestellberichte konvertieren")
    print("-" * 70)
    bestellungen = BestellungenConverter()
    bestellungen.convert()
    print()

    # 2. Zahlungsberichte konvertieren
    print("\nSCHRITT 2/2: Zahlungsberichte konvertieren")
    print("-" * 70)
    zahlungen = ZahlungenConverter()
    zahlungen.convert()
    print()

    # Zusammenfassung
    print("=" * 70)
    print("  ✅ KONVERTIERUNG ABGESCHLOSSEN")
    print("=" * 70)
    print("\n📁 Erstellte Dateien:")
    print("   • Temu_Bestellungen.csv    (Bestellbuchungen)")
    print("   • Temu_zahlung.csv    (Zahlungsbuchungen)")
    print("\n💡 Nächster Schritt:")
    print("   → Dateien in DATEV Unternehmen Online importieren")
    print("   → Optional: python simulate_op_buchungen.py zur Validierung\n")


if __name__ == "__main__":
    main()
