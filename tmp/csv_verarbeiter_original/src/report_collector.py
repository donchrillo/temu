# report_collector.py

import os
import pandas as pd
from datetime import datetime, date
from config import ORDNER_LOG


class ReportCollector:
    def __init__(self):
        self.aenderungen = []
        self.mini_report = []
        self.nicht_gefunden = []
        self.fehler_liste = []

    def log_aenderung(self, dateiname: str, zeilennummer: int, alte_order_id: str, neue_kundennummer: str):
        self.aenderungen.append({
            "Datei": dateiname,
            "Zeile": zeilennummer,
            "Amazon-Order-ID": alte_order_id,
            "Neue Kundennummer": neue_kundennummer
        })

    def log_nicht_gefunden(self, dateiname: str, zeilennummer: int, order_id: str):
        self.nicht_gefunden.append({
            "Datei": dateiname,
            "Zeile": zeilennummer,
            "Amazon-Order-ID": order_id
        })

    def log_fehler(self, dateiname: str, fehlermeldung: str):
        self.fehler_liste.append({
            "Datei": dateiname,
            "Fehler": fehlermeldung,
            "Datum": date.today().isoformat()
        })

    def log_report(self, dateiname: str, ersetzt: int, offen: int, hat_kritisches_konto: bool, pruefmarke_gesetzt: bool):
        self.mini_report.append({
            "Datei": dateiname,
            "Ersetzungen": ersetzt,
            "Offene Order-IDs": offen,
            "Kritisches Gegenkonto": "✅" if hat_kritisches_konto else "❌",
            "Prüfmarke gesetzt": "✅" if pruefmarke_gesetzt else "❌",
            "Verarbeitung OK": "❌" if any(f["Datei"] == dateiname for f in self.fehler_liste) else "✅",
            "Letzter Lauf": date.today().isoformat()
        })

    def speichere(self) -> str | None:
        if not self.aenderungen and not self.mini_report and not self.nicht_gefunden and not self.fehler_liste:
            return None

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        report_pfad = os.path.join(ORDNER_LOG, f"auswertung_{timestamp}.xlsx")

        with pd.ExcelWriter(report_pfad, engine="openpyxl", mode="w") as writer:
            if self.mini_report:
                pd.DataFrame(self.mini_report).to_excel(writer, sheet_name="Mini-Report", index=False)
            if self.aenderungen:
                pd.DataFrame(self.aenderungen).to_excel(writer, sheet_name="Änderungen", index=False)
            if self.nicht_gefunden:
                pd.DataFrame(self.nicht_gefunden).to_excel(writer, sheet_name="Nicht gefunden", index=False)
            if self.fehler_liste:
                pd.DataFrame(self.fehler_liste).to_excel(writer, sheet_name="Fehler", index=False)

        return report_pfad
