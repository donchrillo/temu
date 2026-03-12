#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OP-Buchungs-Simulator für DATEV EXTF Dateien
Simuliert Offene-Posten-Buchhaltung und zeigt nicht ausgeglichene Posten
"""

import csv
from datetime import datetime
from collections import defaultdict
from config import OUTPUT_BESTELLUNGEN, OUTPUT_ZAHLUNGEN, OUTPUT_DIR


class OPSimulator:
    """Simuliert Offene-Posten-Buchhaltung"""

    def __init__(self):
        # OP-Liste: {belegfeld1: saldo}
        self.offene_posten = defaultdict(float)

        # Historie für Detailanzeige: {belegfeld1: [(betrag, sh, typ, datum, text)]}
        self.op_historie = defaultdict(list)

        # Buchungen ohne OP-Zuordnung (kein Belegfeld 1)
        self.ohne_op = []

    def _build_source_file_list(self, current_file):
        """Liefert aktuelle DATEV-Datei + passende History-Snapshots"""
        files = []
        history_dir = current_file.parent / ".history"
        if history_dir.exists():
            pattern = f"{current_file.stem}_*{current_file.suffix}"
            files.extend(sorted(history_dir.glob(pattern)))

        if current_file.exists():
            files.append(current_file)

        return files

    def _iter_datev_rows(self, filepath):
        """Iteriert über DATEV-Datenzeilen (ohne EXTF-Zeile)"""
        with open(filepath, "r", encoding="utf-8") as f:
            f.readline()  # EXTF-Kopfzeile
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                yield row

    def parse_amount(self, amount_str):
        """Konvertiert Betrag mit Komma zu float"""
        try:
            return float(str(amount_str).replace(",", "."))
        except:
            return 0.0

    def load_belege(self, filepath):
        """Lädt Bestell-Exports (aktuell + History) und erstellt OP-Konten"""
        source_files = self._build_source_file_list(filepath)
        print(f"📄 Lade Belege: {len(source_files)} Datei(en)...")

        zeilen = 0
        seen_rows = set()

        for source_file in source_files:
            for row in self._iter_datev_rows(source_file):
                belegfeld1 = row.get("Belegfeld 1", "").strip()

                # Nur Zeilen mit Belegfeld 1 sind OP-relevant
                if not belegfeld1:
                    continue

                # Dedupliziere über fachlich relevante Felder
                row_key = (
                    belegfeld1,
                    row.get("Umsatz (ohne Soll/Haben-Kz)", "").strip(),
                    row.get("Soll/Haben-Kennzeichen", "").strip(),
                    row.get("Konto", "").strip(),
                    row.get("Gegenkonto (ohne BU-Schlüssel)", "").strip(),
                    row.get("Belegdatum", "").strip(),
                    row.get("Buchungstext", "").strip(),
                )
                if row_key in seen_rows:
                    continue
                seen_rows.add(row_key)

                umsatz = self.parse_amount(row.get("Umsatz (ohne Soll/Haben-Kz)", 0))
                sh_kz = row.get("Soll/Haben-Kennzeichen", "S").strip()
                datum = row.get("Belegdatum", "").strip()
                buchungstext = row.get("Buchungstext", "").strip()

                # OP-Berechnung aus Sicht Debitorenkonto:
                # S (Soll auf Debitor) = Forderung entsteht -> OP steigt (+)
                # H (Haben auf Debitor) = Forderung gemindert -> OP sinkt (-)
                betrag = umsatz if sh_kz == "S" else -umsatz

                self.offene_posten[belegfeld1] += betrag
                self.op_historie[belegfeld1].append((betrag, sh_kz, "BELEG", datum, buchungstext))
                zeilen += 1

        print(f"   -> {zeilen} OP-Buchungen geladen")
        print(f"   -> {len(self.offene_posten)} offene Posten angelegt\n")

    def load_zahlungen(self, filepath):
        """Lädt Zahlungs-Exports (aktuell + History) und bucht gegen OPs"""
        source_files = self._build_source_file_list(filepath)
        print(f"💳 Lade Zahlungen: {len(source_files)} Datei(en)...")

        zeilen = 0
        op_buchungen = 0
        ignoriert = 0
        seen_rows = set()

        for source_file in source_files:
            for row in self._iter_datev_rows(source_file):
                belegfeld1 = row.get("Belegfeld 1", "").strip()
                gegenkonto = row.get("Gegenkonto (ohne BU-Schlüssel)", "").strip()

                row_key = (
                    belegfeld1,
                    row.get("Umsatz (ohne Soll/Haben-Kz)", "").strip(),
                    row.get("Soll/Haben-Kennzeichen", "").strip(),
                    row.get("Konto", "").strip(),
                    gegenkonto,
                    row.get("Belegdatum", "").strip(),
                    row.get("Buchungstext", "").strip(),
                )
                if row_key in seen_rows:
                    continue
                seen_rows.add(row_key)

                umsatz = self.parse_amount(row.get("Umsatz (ohne Soll/Haben-Kz)", 0))
                sh_kz = row.get("Soll/Haben-Kennzeichen", "S").strip()
                datum = row.get("Belegdatum", "").strip()
                buchungstext = row.get("Buchungstext", "").strip()

                zeilen += 1

                # Nur Buchungen mit Gegenkonto = Debitor sind OP-relevant
                if gegenkonto != "10012000":
                    ignoriert += 1
                    # Buchungen ohne OP-Relevanz (z.B. Transfer, Gebühren an Aufwandskonto)
                    if not belegfeld1:
                        self.ohne_op.append({
                            "betrag": umsatz,
                            "sh_kz": sh_kz,
                            "datum": datum,
                            "text": buchungstext,
                        })
                    continue

                # OP-Berechnung aus Sicht Debitorenkonto:
                # S (Bank Soll, Debitor Haben) -> Forderung sinkt -> OP reduziert (-)
                # H (Bank Haben, Debitor Soll) -> Forderung steigt -> OP steigt (+)
                betrag = -umsatz if sh_kz == "S" else umsatz

                if belegfeld1:
                    self.offene_posten[belegfeld1] += betrag
                    self.op_historie[belegfeld1].append((betrag, sh_kz, "ZAHLUNG", datum, buchungstext))
                    op_buchungen += 1
                else:
                    # Sollte nicht vorkommen, aber für Robustheit
                    self.ohne_op.append({
                        "betrag": umsatz,
                        "sh_kz": sh_kz,
                        "datum": datum,
                        "text": buchungstext,
                    })

        print(f"   -> {zeilen} Zahlungs-Buchungen geladen")
        print(f"   -> {op_buchungen} gegen OPs gebucht")
        print(f"   -> {ignoriert} ignoriert (kein Debitor-Gegenkonto)")
        print(f"   -> {len(self.ohne_op)} ohne OP-Zuordnung\n")

    def export_markdown(self, filepath, ausgeglichen, nicht_ausgeglichen):
        """Exportiert Analyse als Markdown-Datei"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# DATEV OP-Buchungs-Simulation\n\n")
            f.write(f"**Datum:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n")

            # Zusammenfassung
            f.write("## Zusammenfassung\n\n")
            f.write(f"- Ausgeglichene OPs: {len(ausgeglichen)}\n")
            f.write(f"- Nicht ausgeglichene OPs: {len(nicht_ausgeglichen)}\n")
            f.write(f"- Buchungen ohne OP-Zuordnung: {len(self.ohne_op)}\n\n")

            gesamt_offen = sum(saldo for _, saldo in nicht_ausgeglichen)
            f.write(f"**Gesamt-Saldo nicht ausgeglichener OPs:** {gesamt_offen:.2f} EUR\n\n")

            # Nicht ausgeglichene OPs
            if nicht_ausgeglichen:
                f.write("## Nicht ausgeglichene Offene Posten\n\n")

                for belegfeld1, saldo in nicht_ausgeglichen:
                    f.write(f"### {belegfeld1}\n\n")
                    f.write(f"**Saldo:** {saldo:.2f} EUR\n\n")
                    f.write("| Datum | Typ | S/H | Betrag | Buchungstext |\n")
                    f.write("|-------|-----|-----|--------|---------------|\n")

                    for betrag, sh_kz, typ, datum, text in self.op_historie[belegfeld1]:
                        vorzeichen = "+" if betrag > 0 else ""
                        f.write(f"| {datum:>6} | {typ:>8} | {sh_kz} | {vorzeichen}{betrag:>10.2f} | {text} |\n")

                    f.write("\n")

            # Buchungen ohne OP
            if self.ohne_op:
                f.write("## Buchungen ohne OP-Zuordnung\n\n")
                f.write("| Datum | S/H | Betrag | Buchungstext |\n")
                f.write("|-------|-----|--------|---------------|\n")

                for buchung in self.ohne_op:
                    f.write(f"| {buchung['datum']:>6} | {buchung['sh_kz']} | {buchung['betrag']:>10.2f} | {buchung['text']} |\n")

        print(f"\n💾 Markdown-Export: {filepath}")

    def export_csv(self, filepath, nicht_ausgeglichen):
        """Exportiert nicht ausgeglichene OPs als CSV"""
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Belegfeld 1", "Saldo (EUR)", "Anzahl Buchungen"])

            for belegfeld1, saldo in nicht_ausgeglichen:
                anzahl_buchungen = len(self.op_historie[belegfeld1])
                writer.writerow([belegfeld1, f"{saldo:.2f}".replace(".", ","), anzahl_buchungen])

        print(f"💾 CSV-Export: {filepath}")

    def analyze(self):
        """Analysiert OPs und zeigt nicht ausgeglichene Posten"""
        print("=" * 80)
        print("ANALYSE DER OFFENEN POSTEN")
        print("=" * 80)

        ausgeglichen = []
        nicht_ausgeglichen_positiv = []  # Bestellungen ohne Zahlung
        nicht_ausgeglichen_negativ = []  # Zahlungen ohne Bestellung

        for belegfeld1, saldo in sorted(self.offene_posten.items()):
            if abs(saldo) < 0.01:  # Rundungstolerant (< 1 Cent)
                ausgeglichen.append(belegfeld1)
            elif saldo > 0:
                nicht_ausgeglichen_positiv.append((belegfeld1, saldo))
            else:
                nicht_ausgeglichen_negativ.append((belegfeld1, saldo))

        print(f"\nAusgeglichene OPs: {len(ausgeglichen)}")
        print(f"Bestellungen ohne Zahlung: {len(nicht_ausgeglichen_positiv)}")
        print(f"Zahlungen ohne Bestellung: {len(nicht_ausgeglichen_negativ)} (Bestelldatei fehlt)")
        print(f"Buchungen ohne OP-Zuordnung: {len(self.ohne_op)}")

        # Kombiniere für weitere Verarbeitung
        nicht_ausgeglichen = nicht_ausgeglichen_positiv + nicht_ausgeglichen_negativ

        # BESTELLUNGEN OHNE ZAHLUNG
        if nicht_ausgeglichen_positiv:
            print("\n" + "=" * 80)
            print("BESTELLUNGEN OHNE ZAHLUNG (positive Salden)")
            print("=" * 80)

            for belegfeld1, saldo in nicht_ausgeglichen_positiv:
                print(f"\n{belegfeld1} -> Saldo: {saldo:>10.2f} EUR")
                print("   " + "-" * 76)

                for betrag, sh_kz, typ, datum, text in self.op_historie[belegfeld1]:
                    vorzeichen = "+" if betrag > 0 else ""
                    print(f"   {datum:>6} | {typ:>8} | {sh_kz} | {vorzeichen}{betrag:>10.2f} EUR | {text}")

        # ZAHLUNGEN OHNE BESTELLUNG
        if nicht_ausgeglichen_negativ:
            print("\n" + "=" * 80)
            print("ZAHLUNGEN OHNE BESTELLUNG (negative Salden)")
            print("   -> Bestelldatei für diesen Zeitraum fehlt noch")
            print("=" * 80)

            gesamt_unbekannt = sum(abs(saldo) for _, saldo in nicht_ausgeglichen_negativ)
            print(f"\nGesamt: {len(nicht_ausgeglichen_negativ)} Zahlungen -> {gesamt_unbekannt:.2f} EUR\n")

            print("Bestellnummern (erste 20):")
            for belegfeld1, saldo in nicht_ausgeglichen_negativ[:20]:
                print(f"   {belegfeld1:50} -> {abs(saldo):>10.2f} EUR")

            if len(nicht_ausgeglichen_negativ) > 20:
                weitere = len(nicht_ausgeglichen_negativ) - 20
                weitere_summe = sum(abs(saldo) for _, saldo in nicht_ausgeglichen_negativ[20:])
                print(f"   ... und {weitere} weitere -> {weitere_summe:.2f} EUR")

        # BUCHUNGEN OHNE OP
        if self.ohne_op:
            print("\n" + "=" * 80)
            print("BUCHUNGEN OHNE OP-ZUORDNUNG (kein Belegfeld 1)")
            print("=" * 80)

            for buchung in self.ohne_op:
                betrag_str = f"{buchung['betrag']:.2f}"
                print(f"   {buchung['datum']:>6} | {buchung['sh_kz']} | {betrag_str:>10} EUR | {buchung['text']}")

        # ZUSAMMENFASSUNG
        print("\n" + "=" * 80)
        print("ZUSAMMENFASSUNG")
        print("=" * 80)

        gesamt_offen_positiv = sum(saldo for _, saldo in nicht_ausgeglichen_positiv)
        gesamt_offen_negativ = sum(abs(saldo) for _, saldo in nicht_ausgeglichen_negativ)

        print(f"   Bestellungen ohne Zahlung: {gesamt_offen_positiv:>10.2f} EUR ({len(nicht_ausgeglichen_positiv)} OPs)")
        print(f"   Zahlungen ohne Bestellung: {gesamt_offen_negativ:>10.2f} EUR ({len(nicht_ausgeglichen_negativ)} OPs)")

        if len(nicht_ausgeglichen_positiv) == 0:
            print("\n   Alle bekannten Bestellungen sind bezahlt!")
        else:
            print(f"\n   {len(nicht_ausgeglichen_positiv)} Bestellungen warten noch auf Zahlung")

        return ausgeglichen, nicht_ausgeglichen


def main():
    """Hauptprogramm"""
    datev_belege = OUTPUT_BESTELLUNGEN
    temu_zahlung = OUTPUT_ZAHLUNGEN

    if not datev_belege.exists():
        print(f"Fehler: {datev_belege} nicht gefunden")
        print("Führe zuerst temu_to_datev.py aus!")
        return None

    if not temu_zahlung.exists():
        print(f"Fehler: {temu_zahlung} nicht gefunden")
        print("Führe zuerst temu_to_datev.py aus!")
        return None

    simulator = OPSimulator()
    simulator.load_belege(datev_belege)
    simulator.load_zahlungen(temu_zahlung)
    ausgeglichen, nicht_ausgeglichen = simulator.analyze()

    print()
    simulator.export_markdown(OUTPUT_DIR / "OP_Analyse.md", ausgeglichen, nicht_ausgeglichen)
    simulator.export_csv(OUTPUT_DIR / "OP_Nicht_Ausgeglichen.csv", nicht_ausgeglichen)

    nicht_ausgeglichen_positiv = [(b, s) for b, s in nicht_ausgeglichen if s > 0]
    nicht_ausgeglichen_negativ = [(b, s) for b, s in nicht_ausgeglichen if s < 0]

    return {
        "ausgeglichen_count": len(ausgeglichen),
        "bestellungen_ohne_zahlung": len(nicht_ausgeglichen_positiv),
        "zahlungen_ohne_bestellung": len(nicht_ausgeglichen_negativ),
        "gesamt_offen_eur": round(sum(s for _, s in nicht_ausgeglichen_positiv), 2),
        "ohne_op_count": len(simulator.ohne_op),
        "top_offen": [
            {"belegfeld1": b, "saldo": round(s, 2)}
            for b, s in nicht_ausgeglichen_positiv[:20]
        ],
    }


if __name__ == "__main__":
    main()
