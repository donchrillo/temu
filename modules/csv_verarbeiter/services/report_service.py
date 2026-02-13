"""
Report Service - Excel-Reports für CSV-Verarbeitung

Basiert auf: tmp/csv_verarbeiter_original/src/report_collector.py

Erstellt Excel-Reports mit 4 Sheets:
1. Mini-Report: Übersicht pro Datei
2. Änderungen: Erfolgreiche OrderID-Ersetzungen
3. Nicht gefunden: OrderIDs ohne Match in JTL
4. Fehler: Fehlerhafte Dateien/Zeilen
"""

import os
import pandas as pd
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Optional

from modules.shared import log_service, app_logger


class ReportCollector:
    """
    Sammelt alle Verarbeitungsergebnisse und erstellt Excel-Report.
    
    Kompatibel mit Original-Code aus csv_verarbeiter.
    """
    
    def __init__(self):
        """Initialisiert leere Listen für alle Report-Daten"""
        self.aenderungen = []
        self.mini_report = []
        self.nicht_gefunden = []
        self.fehler_liste = []
    
    def log_aenderung(self, dateiname: str, zeilennummer: int, 
                     alte_order_id: str, neue_kundennummer: str):
        """
        Protokolliert erfolgreiche OrderID-Ersetzung.
        
        Args:
            dateiname: Name der CSV-Datei
            zeilennummer: Zeilennummer (inkl. Metazeile + Header)
            alte_order_id: Amazon OrderID vor Ersetzung
            neue_kundennummer: JTL Kundennummer nach Ersetzung
        """
        self.aenderungen.append({
            "Datei": dateiname,
            "Zeile": zeilennummer,
            "Amazon-Order-ID": alte_order_id,
            "Neue Kundennummer": neue_kundennummer
        })
    
    def log_nicht_gefunden(self, dateiname: str, zeilennummer: int, order_id: str):
        """
        Protokolliert nicht gefundene OrderID.
        
        Args:
            dateiname: Name der CSV-Datei
            zeilennummer: Zeilennummer
            order_id: Amazon OrderID ohne Match in JTL
        """
        self.nicht_gefunden.append({
            "Datei": dateiname,
            "Zeile": zeilennummer,
            "Amazon-Order-ID": order_id
        })
    
    def log_fehler(self, dateiname: str, fehlermeldung: str):
        """
        Protokolliert Fehler bei der Verarbeitung.
        
        Args:
            dateiname: Name der CSV-Datei
            fehlermeldung: Beschreibung des Fehlers
        """
        self.fehler_liste.append({
            "Datei": dateiname,
            "Fehler": fehlermeldung,
            "Datum": date.today().isoformat()
        })
    
    def log_report(self, dateiname: str, ersetzt: int, offen: int, 
                   hat_kritisches_konto: bool, pruefmarke_gesetzt: bool):
        """
        Fügt Eintrag zum Mini-Report hinzu (Übersicht pro Datei).
        
        Args:
            dateiname: Name der CSV-Datei
            ersetzt: Anzahl ersetzter OrderIDs
            offen: Anzahl nicht gefundener OrderIDs
            hat_kritisches_konto: True wenn kritisches Gegenkonto (0-20) vorhanden
            pruefmarke_gesetzt: True wenn Prüfmarken gesetzt wurden
        """
        self.mini_report.append({
            "Datei": dateiname,
            "Ersetzungen": ersetzt,
            "Offene Order-IDs": offen,
            "Kritisches Gegenkonto": "✅" if hat_kritisches_konto else "❌",
            "Prüfmarke gesetzt": "✅" if pruefmarke_gesetzt else "❌",
            "Verarbeitung OK": "❌" if any(f["Datei"] == dateiname for f in self.fehler_liste) else "✅",
            "Letzter Lauf": date.today().isoformat()
        })
    
    def speichere(self, report_dir: Path) -> Optional[str]:
        """
        Speichert gesammelten Report als Excel-Datei mit 4 Sheets.
        
        Dateiname: auswertung_YYYY-MM-DD_HHMM.xlsx
        
        Sheets:
        1. Mini-Report: Datei-Übersicht
        2. Änderungen: Erfolgreiche Ersetzungen
        3. Nicht gefunden: Nicht gefundene OrderIDs
        4. Fehler: Fehlerhafte Verarbeitungen
        
        Args:
            report_dir: Verzeichnis für Report-Dateien
            
        Returns:
            Pfad zur Report-Datei oder None wenn keine Daten
        """
        # Prüfe ob überhaupt Daten vorhanden sind
        if not self.aenderungen and not self.mini_report and not self.nicht_gefunden and not self.fehler_liste:
            log_service.log("report", "speichere", "WARN", 
                          "⚠️ Keine Report-Daten vorhanden, überspringe Excel-Erstellung")
            return None
        
        try:
            # Erstelle Dateinamen mit Timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
            report_pfad = report_dir / f"auswertung_{timestamp}.xlsx"
            
            # Erstelle Excel mit 4 Sheets
            with pd.ExcelWriter(report_pfad, engine="openpyxl", mode="w") as writer:
                # Sheet 1: Mini-Report (Übersicht)
                if self.mini_report:
                    df_mini = pd.DataFrame(self.mini_report)
                    df_mini.to_excel(writer, sheet_name="Mini-Report", index=False)
                
                # Sheet 2: Änderungen (erfolgreiche Ersetzungen)
                if self.aenderungen:
                    df_aenderungen = pd.DataFrame(self.aenderungen)
                    df_aenderungen.to_excel(writer, sheet_name="Änderungen", index=False)
                
                # Sheet 3: Nicht gefunden
                if self.nicht_gefunden:
                    df_nicht_gefunden = pd.DataFrame(self.nicht_gefunden)
                    df_nicht_gefunden.to_excel(writer, sheet_name="Nicht gefunden", index=False)
                
                # Sheet 4: Fehler
                if self.fehler_liste:
                    df_fehler = pd.DataFrame(self.fehler_liste)
                    df_fehler.to_excel(writer, sheet_name="Fehler", index=False)
            
            log_service.log("report", "speichere", "INFO", 
                          f"✓ Report gespeichert: {report_pfad.name}")
            
            return str(report_pfad)
            
        except Exception as e:
            log_service.log("report", "speichere", "ERROR", 
                          f"❌ Fehler beim Speichern des Reports: {str(e)}")
            return None
    
    def get_zusammenfassung(self) -> Dict:
        """
        Gibt Zusammenfassung der gesammelten Daten zurück.
        
        Returns:
            Dict mit Statistiken
        """
        return {
            "aenderungen_count": len(self.aenderungen),
            "nicht_gefunden_count": len(self.nicht_gefunden),
            "fehler_count": len(self.fehler_liste),
            "dateien_count": len(self.mini_report),
            "hat_daten": bool(self.aenderungen or self.mini_report or self.nicht_gefunden or self.fehler_liste)
        }


class ReportService:
    """
    Wrapper-Service für ReportCollector mit zusätzlichen Utility-Funktionen.
    """
    
    def __init__(self, report_dir: Path):
        """
        Args:
            report_dir: Verzeichnis für Report-Dateien
        """
        self.report_dir = report_dir
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    def create_collector(self) -> ReportCollector:
        """
        Erstellt neuen ReportCollector für einen Verarbeitungsdurchlauf.
        
        Returns:
            Neue ReportCollector-Instanz
        """
        return ReportCollector()
    
    def list_reports(self) -> List[Dict]:
        """
        Listet alle vorhandenen Report-Dateien auf.
        
        Returns:
            Liste von Dicts mit Report-Informationen
        """
        reports = []
        
        try:
            for file in sorted(self.report_dir.glob("auswertung_*.xlsx"), reverse=True):
                reports.append({
                    "filename": file.name,
                    "path": str(file),
                    "created_at": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
                    "size": file.stat().st_size
                })
        except Exception as e:
            log_service.log("report", "list_reports", "ERROR", 
                          f"❌ Fehler beim Auflisten der Reports: {str(e)}")
        
        return reports
    
    def cleanup_old_reports(self, days: int = 30) -> int:
        """
        Löscht Reports älter als X Tage.
        
        Args:
            days: Anzahl Tage (Reports älter als dieser Wert werden gelöscht)
            
        Returns:
            Anzahl gelöschter Reports
        """
        deleted = 0
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        try:
            for file in self.report_dir.glob("auswertung_*.xlsx"):
                if file.stat().st_mtime < cutoff_time:
                    file.unlink()
                    deleted += 1
            
            log_service.log("report", "cleanup_old_reports", "INFO", 
                          f"✓ {deleted} alte Reports gelöscht (älter als {days} Tage)")
            
        except Exception as e:
            log_service.log("report", "cleanup_old_reports", "ERROR", 
                          f"❌ Fehler beim Cleanup: {str(e)}")
        
        return deleted
