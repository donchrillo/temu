"""Report Service - Generierung von Excel-Berichten"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

from modules.shared import log_service


class ReportService:
    """Service für Excel-Report-Generierung"""
    
    def __init__(self, reports_dir: Path):
        """
        Args:
            reports_dir: Verzeichnis für Report-Output
        """
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_processing_report(self, 
                                  job_id: str,
                                  validation_result: Dict,
                                  replacement_stats: Dict,
                                  input_file: str,
                                  output_file: Optional[str] = None,
                                  duration_seconds: Optional[float] = None) -> Optional[Path]:
        """
        Generiert Excel-Report über Verarbeitungsergebnisse.
        
        Args:
            job_id: Job ID
            validation_result: Validierungsergebnisse (von ValidationService)
            replacement_stats: Ersetzungsstatistiken (von ReplacementService)
            input_file: Name der Input-Datei
            output_file: Name der Output-Datei (optional)
            duration_seconds: Verarbeitungsdauer in Sekunden (optional)
            
        Returns:
            Path: Pfad zum generierten Report oder None bei Fehler
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f"report_{job_id}_{timestamp}.xlsx"
            report_path = self.reports_dir / report_filename
            
            log_service.log(job_id, "csv_report", "INFO", 
                          f"→ Generiere Report: {report_filename}")
            
            # Excel Writer erstellen
            with pd.ExcelWriter(report_path, engine='openpyxl') as writer:
                
                # Sheet 1: Zusammenfassung
                summary_data = self._create_summary_data(
                    job_id, input_file, output_file, duration_seconds,
                    validation_result, replacement_stats
                )
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Zusammenfassung', index=False)
                
                # Sheet 2: Validierungsfehler
                if validation_result.get('errors'):
                    df_errors = pd.DataFrame(validation_result['errors'])
                    df_errors.to_excel(writer, sheet_name='Validierungsfehler', index=False)
                
                # Sheet 3: Warnungen
                if validation_result.get('warnings'):
                    df_warnings = pd.DataFrame(validation_result['warnings'])
                    df_warnings.to_excel(writer, sheet_name='Warnungen', index=False)
                
                # Sheet 4: Statistiken
                stats_data = self._create_statistics_data(validation_result, replacement_stats)
                df_stats = pd.DataFrame(stats_data)
                df_stats.to_excel(writer, sheet_name='Statistiken', index=False)
            
            log_service.log(job_id, "csv_report", "INFO", 
                          f"✓ Report erstellt: {report_filename}")
            
            return report_path
            
        except Exception as e:
            log_service.log(job_id, "csv_report", "ERROR", 
                          f"❌ Fehler bei Report-Generierung: {str(e)}")
            return None
    
    def _create_summary_data(self, job_id: str, input_file: str, 
                           output_file: Optional[str], duration_seconds: Optional[float],
                           validation_result: Dict, replacement_stats: Dict) -> List[Dict]:
        """
        Erstellt Zusammenfassungsdaten für Report.
        
        Returns:
            List[Dict]: Daten für Zusammenfassungs-Sheet
        """
        return [
            {'Feld': 'Job ID', 'Wert': job_id},
            {'Feld': 'Zeitstempel', 'Wert': datetime.now().strftime('%d.%m.%Y %H:%M:%S')},
            {'Feld': 'Input-Datei', 'Wert': input_file},
            {'Feld': 'Output-Datei', 'Wert': output_file or 'N/A'},
            {'Feld': 'Verarbeitungsdauer (Sekunden)', 'Wert': f"{duration_seconds:.2f}" if duration_seconds else 'N/A'},
            {'Feld': '', 'Wert': ''},  # Leerzeile
            {'Feld': '=== VALIDIERUNG ===', 'Wert': ''},
            {'Feld': 'Valide Zeilen', 'Wert': validation_result.get('valid_rows', 0)},
            {'Feld': 'Ungültige OrderID-Patterns', 'Wert': validation_result.get('invalid_pattern', 0)},
            {'Feld': 'Kritische Konten (0-20)', 'Wert': validation_result.get('critical_accounts', 0)},
            {'Feld': 'Validierungsfehler', 'Wert': len(validation_result.get('errors', []))},
            {'Feld': 'Warnungen', 'Wert': len(validation_result.get('warnings', []))},
            {'Feld': '', 'Wert': ''},  # Leerzeile
            {'Feld': '=== ERSETZUNG ===', 'Wert': ''},
            {'Feld': 'Zeilen verarbeitet', 'Wert': replacement_stats.get('total', 0)},
            {'Feld': 'Erfolgreich ersetzt', 'Wert': replacement_stats.get('success', 0)},
            {'Feld': 'Ersetzung fehlgeschlagen', 'Wert': replacement_stats.get('failed', 0)},
            {'Feld': 'Kritische Konten übersprungen', 'Wert': replacement_stats.get('skipped_critical', 0)},
            {'Feld': 'Ungültige OrderIDs übersprungen', 'Wert': replacement_stats.get('skipped_invalid', 0)},
            {'Feld': '', 'Wert': ''},  # Leerzeile
            {'Feld': '=== ERFOLG ===', 'Wert': ''},
            {'Feld': 'Status', 'Wert': 'ERFOLGREICH' if validation_result.get('success') else 'MIT FEHLERN'}
        ]
    
    def _create_statistics_data(self, validation_result: Dict, 
                               replacement_stats: Dict) -> List[Dict]:
        """
        Erstellt Statistikdaten für Report.
        
        Returns:
            List[Dict]: Daten für Statistik-Sheet
        """
        total_validation = validation_result.get('valid_rows', 0) + \
                          validation_result.get('invalid_pattern', 0) + \
                          validation_result.get('critical_accounts', 0)
        
        stats = [
            {'Kategorie': 'Validierung', 'Metrik': 'Gesamt geprüft', 'Wert': total_validation},
            {'Kategorie': 'Validierung', 'Metrik': 'Valide', 'Wert': validation_result.get('valid_rows', 0)},
            {'Kategorie': 'Validierung', 'Metrik': 'Ungültiges Pattern', 'Wert': validation_result.get('invalid_pattern', 0)},
            {'Kategorie': 'Validierung', 'Metrik': 'Kritische Konten', 'Wert': validation_result.get('critical_accounts', 0)},
            {'Kategorie': '', 'Metrik': '', 'Wert': ''},
            {'Kategorie': 'Ersetzung', 'Metrik': 'Gesamt verarbeitet', 'Wert': replacement_stats.get('total', 0)},
            {'Kategorie': 'Ersetzung', 'Metrik': 'Erfolgreich', 'Wert': replacement_stats.get('success', 0)},
            {'Kategorie': 'Ersetzung', 'Metrik': 'Fehlgeschlagen', 'Wert': replacement_stats.get('failed', 0)},
            {'Kategorie': 'Ersetzung', 'Metrik': 'Übersprungen (kritische Konten)', 'Wert': replacement_stats.get('skipped_critical', 0)},
            {'Kategorie': 'Ersetzung', 'Metrik': 'Übersprungen (ungültige OrderIDs)', 'Wert': replacement_stats.get('skipped_invalid', 0)},
        ]
        
        # Prozentwerte berechnen
        if total_validation > 0:
            valid_pct = (validation_result.get('valid_rows', 0) / total_validation) * 100
            stats.append({'Kategorie': '', 'Metrik': '', 'Wert': ''})
            stats.append({'Kategorie': 'Erfolgsrate', 'Metrik': 'Validierung', 'Wert': f"{valid_pct:.1f}%"})
        
        if replacement_stats.get('total', 0) > 0:
            success_pct = (replacement_stats.get('success', 0) / replacement_stats.get('total', 0)) * 100
            stats.append({'Kategorie': 'Erfolgsrate', 'Metrik': 'Ersetzung', 'Wert': f"{success_pct:.1f}%"})
        
        return stats
    
    def generate_error_report(self, job_id: str, error_message: str, 
                            input_file: Optional[str] = None) -> Optional[Path]:
        """
        Generiert Fehler-Report bei kritischen Fehlern.
        
        Args:
            job_id: Job ID
            error_message: Fehlermeldung
            input_file: Name der Input-Datei (optional)
            
        Returns:
            Path: Pfad zum generierten Report oder None bei Fehler
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f"error_report_{job_id}_{timestamp}.xlsx"
            report_path = self.reports_dir / report_filename
            
            error_data = [
                {'Feld': 'Job ID', 'Wert': job_id},
                {'Feld': 'Zeitstempel', 'Wert': datetime.now().strftime('%d.%m.%Y %H:%M:%S')},
                {'Feld': 'Input-Datei', 'Wert': input_file or 'N/A'},
                {'Feld': 'Status', 'Wert': 'FEHLER'},
                {'Feld': '', 'Wert': ''},
                {'Feld': 'Fehlermeldung', 'Wert': error_message}
            ]
            
            df_error = pd.DataFrame(error_data)
            
            with pd.ExcelWriter(report_path, engine='openpyxl') as writer:
                df_error.to_excel(writer, sheet_name='Fehler', index=False)
            
            log_service.log(job_id, "csv_report", "INFO", 
                          f"✓ Fehler-Report erstellt: {report_filename}")
            
            return report_path
            
        except Exception as e:
            log_service.log(job_id, "csv_report", "ERROR", 
                          f"❌ Fehler bei Fehler-Report-Generierung: {str(e)}")
            return None
    
    def list_reports(self, job_id: Optional[str] = None) -> List[Dict]:
        """
        Listet alle verfügbaren Reports auf.
        
        Args:
            job_id: Optional - Filter nach Job ID
            
        Returns:
            List[Dict]: Liste von Report-Informationen
        """
        reports = []
        
        try:
            for report_file in self.reports_dir.glob("*.xlsx"):
                # Parse Dateiname: report_{job_id}_{timestamp}.xlsx
                name_parts = report_file.stem.split('_')
                
                # Job ID Filter
                if job_id and len(name_parts) >= 2:
                    file_job_id = name_parts[1]
                    if file_job_id != job_id:
                        continue
                
                # Dateiinfo sammeln
                stat = report_file.stat()
                reports.append({
                    'filename': report_file.name,
                    'path': str(report_file),
                    'size_bytes': stat.st_size,
                    'size_kb': round(stat.st_size / 1024, 2),
                    'created_at': datetime.fromtimestamp(stat.st_ctime).strftime('%d.%m.%Y %H:%M:%S'),
                    'modified_at': datetime.fromtimestamp(stat.st_mtime).strftime('%d.%m.%Y %H:%M:%S')
                })
            
            # Sortiere nach Erstellungsdatum (neueste zuerst)
            reports.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            log_service.log("SYSTEM", "csv_report", "ERROR", 
                          f"❌ Fehler beim Auflisten von Reports: {str(e)}")
        
        return reports
    
    def cleanup_old_reports(self, days: int = 30) -> int:
        """
        Löscht Reports älter als X Tage.
        
        Args:
            days: Anzahl Tage (Standard: 30)
            
        Returns:
            int: Anzahl gelöschter Reports
        """
        deleted_count = 0
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        try:
            for report_file in self.reports_dir.glob("*.xlsx"):
                if report_file.stat().st_mtime < cutoff_time:
                    report_file.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                log_service.log("SYSTEM", "csv_report", "INFO", 
                              f"✓ {deleted_count} alte Reports gelöscht (älter als {days} Tage)")
        
        except Exception as e:
            log_service.log("SYSTEM", "csv_report", "ERROR", 
                          f"❌ Fehler beim Löschen alter Reports: {str(e)}")
        
        return deleted_count
