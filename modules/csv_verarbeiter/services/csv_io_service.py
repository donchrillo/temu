"""CSV IO Service - Lesen und Schreiben von CSV/ZIP Dateien"""

import zipfile
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
import pandas as pd
import chardet

from modules.shared import log_service


class CsvIoService:
    """Service für CSV/ZIP Datei-Operationen"""
    
    def __init__(self, data_dir: Path):
        """
        Args:
            data_dir: Basis-Verzeichnis für CSV-Daten (z.B. data/csv_verarbeiter)
        """
        self.data_dir = data_dir
        self.eingang_dir = data_dir / "eingang"
        self.ausgang_dir = data_dir / "ausgang"
        self.reports_dir = data_dir / "reports"
        
        # Erstelle Verzeichnisse falls nicht vorhanden
        self.eingang_dir.mkdir(parents=True, exist_ok=True)
        self.ausgang_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def detect_encoding(self, file_path: Path) -> str:
        """
        Erkennt die Encoding der Datei automatisch.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            str: Erkanntes Encoding (z.B. 'utf-8', 'cp1252')
        """
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            return result['encoding'] or 'utf-8'
    
    def read_csv(self, file_path: Path, job_id: str, 
                 delimiter: str = ';', encoding: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Liest CSV-Datei mit automatischer Encoding-Erkennung.
        
        Args:
            file_path: Pfad zur CSV-Datei
            job_id: Job ID für Logging
            delimiter: CSV-Trennzeichen (Standard: ';' für DATEV)
            encoding: Optional - falls bekannt, sonst automatisch erkannt
            
        Returns:
            pd.DataFrame oder None bei Fehler
        """
        try:
            if not file_path.exists():
                log_service.log(job_id, "csv_io", "ERROR", f"❌ Datei nicht gefunden: {file_path}")
                return None
            
            # Encoding erkennen falls nicht angegeben
            if encoding is None:
                encoding = self.detect_encoding(file_path)
                log_service.log(job_id, "csv_io", "INFO", f"→ Encoding erkannt: {encoding}")
            
            # CSV lesen
            df = pd.read_csv(file_path, delimiter=delimiter, encoding=encoding, dtype=str)
            
            log_service.log(job_id, "csv_io", "INFO", 
                          f"✓ CSV gelesen: {len(df)} Zeilen, {len(df.columns)} Spalten")
            
            return df
            
        except Exception as e:
            log_service.log(job_id, "csv_io", "ERROR", 
                          f"❌ Fehler beim Lesen von {file_path.name}: {str(e)}")
            return None
    
    def write_csv(self, df: pd.DataFrame, file_name: str, job_id: str,
                  delimiter: str = ';', encoding: str = 'cp1252') -> Optional[Path]:
        """
        Schreibt DataFrame als CSV in Ausgang-Ordner.
        
        Args:
            df: DataFrame zum Schreiben
            file_name: Dateiname (ohne Pfad)
            job_id: Job ID für Logging
            delimiter: CSV-Trennzeichen (Standard: ';' für DATEV)
            encoding: Encoding (Standard: 'cp1252' für DATEV)
            
        Returns:
            Path zur geschriebenen Datei oder None bei Fehler
        """
        try:
            output_path = self.ausgang_dir / file_name
            
            # Schreibe CSV
            df.to_csv(output_path, sep=delimiter, encoding=encoding, index=False)
            
            log_service.log(job_id, "csv_io", "INFO", 
                          f"✓ CSV geschrieben: {output_path.name} ({len(df)} Zeilen)")
            
            return output_path
            
        except Exception as e:
            log_service.log(job_id, "csv_io", "ERROR", 
                          f"❌ Fehler beim Schreiben von {file_name}: {str(e)}")
            return None
    
    def extract_zip(self, zip_path: Path, job_id: str) -> List[Path]:
        """
        Extrahiert ZIP-Datei in Eingang-Ordner.
        
        Args:
            zip_path: Pfad zur ZIP-Datei
            job_id: Job ID für Logging
            
        Returns:
            Liste der extrahierten CSV-Dateien
        """
        csv_files = []
        
        try:
            if not zip_path.exists():
                log_service.log(job_id, "csv_io", "ERROR", f"❌ ZIP nicht gefunden: {zip_path}")
                return csv_files
            
            log_service.log(job_id, "csv_io", "INFO", f"→ Extrahiere ZIP: {zip_path.name}")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Erstelle temporäres Extraktionsverzeichnis
                extract_dir = self.eingang_dir / f"extracted_{job_id}"
                extract_dir.mkdir(exist_ok=True)
                
                # Extrahiere alle Dateien
                zip_ref.extractall(extract_dir)
                
                # Finde alle CSV-Dateien
                csv_files = list(extract_dir.glob("*.csv"))
                csv_files.extend(list(extract_dir.glob("*.CSV")))
                
                log_service.log(job_id, "csv_io", "INFO", 
                              f"✓ {len(csv_files)} CSV-Dateien extrahiert")
            
            return csv_files
            
        except Exception as e:
            log_service.log(job_id, "csv_io", "ERROR", 
                          f"❌ Fehler beim Extrahieren von {zip_path.name}: {str(e)}")
            return csv_files
    
    def create_zip(self, csv_files: List[Path], zip_name: str, job_id: str) -> Optional[Path]:
        """
        Erstellt ZIP-Datei aus CSV-Dateien im Ausgang-Ordner.
        
        Args:
            csv_files: Liste der CSV-Dateien zum Zippen
            zip_name: Name der ZIP-Datei (ohne Pfad)
            job_id: Job ID für Logging
            
        Returns:
            Path zur ZIP-Datei oder None bei Fehler
        """
        try:
            zip_path = self.ausgang_dir / zip_name
            
            log_service.log(job_id, "csv_io", "INFO", 
                          f"→ Erstelle ZIP: {zip_name} ({len(csv_files)} Dateien)")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                for csv_file in csv_files:
                    if csv_file.exists():
                        # Füge Datei mit relativem Namen hinzu
                        zip_ref.write(csv_file, csv_file.name)
            
            log_service.log(job_id, "csv_io", "INFO", f"✓ ZIP erstellt: {zip_path.name}")
            
            return zip_path
            
        except Exception as e:
            log_service.log(job_id, "csv_io", "ERROR", 
                          f"❌ Fehler beim Erstellen von ZIP {zip_name}: {str(e)}")
            return None
    
    def cleanup_temp_files(self, job_id: str):
        """
        Löscht temporäre Extraktionsverzeichnisse.
        
        Args:
            job_id: Job ID
        """
        try:
            extract_dir = self.eingang_dir / f"extracted_{job_id}"
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
                log_service.log(job_id, "csv_io", "INFO", "✓ Temporäre Dateien gelöscht")
        except Exception as e:
            log_service.log(job_id, "csv_io", "WARNING", 
                          f"⚠ Fehler beim Löschen temporärer Dateien: {str(e)}")
    
    def get_input_files(self, extensions: List[str] = [".csv", ".zip"]) -> List[Path]:
        """
        Findet alle Input-Dateien im Eingang-Ordner.
        
        Args:
            extensions: Liste der Dateiendungen (Standard: ['.csv', '.zip'])
            
        Returns:
            Liste der gefundenen Dateien
        """
        files = []
        for ext in extensions:
            files.extend(self.eingang_dir.glob(f"*{ext}"))
            files.extend(self.eingang_dir.glob(f"*{ext.upper()}"))
        
        return sorted(files)
