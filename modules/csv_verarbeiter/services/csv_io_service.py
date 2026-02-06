"""
CSV I/O Service - Lesen und Schreiben von DATEV-kompatiblen CSV-Dateien

KRITISCH: DATEV-CSV-Dateien haben eine Metazeile (erste Zeile) mit Header-Informationen,
die separat behandelt werden muss!

Basiert auf: tmp/csv_verarbeiter_original/src/verarbeitung_io.py
"""

import os
import zipfile
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
import pandas as pd
import chardet

from modules.shared import log_service, app_logger


class CsvIoService:
    """Service für CSV/ZIP Datei-Operationen mit DATEV-Metazeilen-Unterstützung"""
    
    def __init__(self, data_dir: Path):
        """
        Args:
            data_dir: Basis-Verzeichnis für CSV-Daten (z.B. data/csv_verarbeiter)
        """
        self.data_dir = data_dir
        self.eingang_dir = data_dir / "eingang"
        self.ausgang_dir = data_dir / "ausgang"
        self.reports_dir = data_dir / "reports"
        self.archive_dir = data_dir / "archive"
        
        # Erstelle Verzeichnisse falls nicht vorhanden
        for directory in [self.eingang_dir, self.ausgang_dir, self.reports_dir, self.archive_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def detect_encoding(self, file_path: Path) -> str:
        """
        Erkennt die Encoding der Datei automatisch.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            str: Erkanntes Encoding (z.B. 'utf-8', 'cp1252')
        """
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                detected = result['encoding'] or 'cp1252'
                
                log_service.log("csv_io", "detect_encoding", "INFO", 
                              f"Encoding erkannt für {file_path.name}: {detected}")
                
                return detected
        except Exception as e:
            log_service.log("csv_io", "detect_encoding", "WARN", 
                          f"Encoding-Erkennung fehlgeschlagen für {file_path.name}, verwende cp1252: {str(e)}")
            return 'cp1252'
    
    def lese_metazeile(self, file_path: Path, encoding: str = 'cp1252') -> Tuple[str, bool]:
        """
        Liest die erste Zeile (DATEV-Metadaten) einer CSV-Datei.
        
        Diese Zeile enthält systemtechnische Informationen und muss beim Speichern
        erhalten bleiben!
        
        Args:
            file_path: Pfad zur CSV-Datei
            encoding: Encoding (Standard: cp1252 für DATEV)
            
        Returns:
            Tuple[metazeile_string, success_flag]
        """
        try:
            with open(file_path, "r", encoding=encoding) as f:
                erste_zeile = f.readline().strip()
            
            log_service.log("csv_io", "lese_metazeile", "INFO", 
                          f"✓ Metazeile gelesen: {file_path.name}")
            
            return erste_zeile, True
            
        except Exception as e:
            log_service.log("csv_io", "lese_metazeile", "ERROR", 
                          f"❌ Fehler beim Lesen der Metazeile von {file_path.name}: {str(e)}")
            return "", False
    
    def lade_csv_daten(self, file_path: Path, encoding: str = 'cp1252') -> Tuple[pd.DataFrame, bool]:
        """
        Liest CSV-Datei ab Zeile 2 (überspringt DATEV-Metazeile!).
        
        WICHTIG: Die erste Zeile wird übersprungen (skiprows=1), da sie die
        DATEV-Metadaten enthält. Diese muss separat mit lese_metazeile() gelesen werden.
        
        Args:
            file_path: Pfad zur CSV-Datei
            encoding: Encoding (Standard: cp1252 für DATEV)
            
        Returns:
            Tuple[DataFrame, success_flag]
        """
        try:
            # KRITISCH: skiprows=1 überspringt die Metazeile!
            df = pd.read_csv(
                file_path,
                sep=";",
                dtype=str,
                encoding=encoding,
                skiprows=1  # Metazeile überspringen!
            )
            
            if df.empty:
                log_service.log("csv_io", "lade_csv_daten", "WARN", 
                              f"⚠️ Datei enthält keine Datenzeilen: {file_path.name}")
                return pd.DataFrame(), False
            
            log_service.log("csv_io", "lade_csv_daten", "INFO", 
                          f"✓ CSV gelesen: {file_path.name} ({len(df)} Zeilen, ohne Metazeile)")
            
            return df, True
            
        except Exception as e:
            log_service.log("csv_io", "lade_csv_daten", "ERROR", 
                          f"❌ Fehler beim Lesen von {file_path.name}: {str(e)}")
            return pd.DataFrame(), False
    
    def schreibe_csv_mit_metazeile(self, df: pd.DataFrame, metazeile: str, 
                                   file_path: Path, encoding: str = 'cp1252') -> bool:
        """
        Schreibt DataFrame in CSV-Datei MIT DATEV-Metazeile.
        
        Vorgehen:
        1. DataFrame wird temporär gespeichert (ohne Metazeile)
        2. Finale Datei wird mit Metazeile + Inhalt erstellt
        3. Temporäre Datei wird gelöscht
        
        Args:
            df: DataFrame zum Schreiben
            metazeile: DATEV-Header-Zeile (erste Zeile)
            file_path: Ziel-Pfad
            encoding: Encoding (Standard: cp1252 für DATEV)
            
        Returns:
            success_flag
        """
        try:
            # 1. Temporäre Datei ohne Metazeile erstellen
            temp_path = file_path.parent / f"temp_{file_path.name}"
            df.to_csv(
                temp_path,
                sep=";",
                index=False,
                encoding=encoding
            )
            
            # 2. Finale Datei mit Metazeile + Inhalt schreiben
            with open(temp_path, "r", encoding=encoding) as temp_file:
                inhalt = temp_file.read()
            
            with open(file_path, "w", encoding=encoding) as final_file:
                final_file.write(metazeile + "\n")
                final_file.write(inhalt)
            
            # 3. Temporäre Datei löschen
            if temp_path.exists():
                temp_path.unlink()
            
            log_service.log("csv_io", "schreibe_csv_mit_metazeile", "INFO", 
                          f"✓ CSV mit Metazeile geschrieben: {file_path.name} ({len(df)} Zeilen)")
            
            return True
            
        except Exception as e:
            log_service.log("csv_io", "schreibe_csv_mit_metazeile", "ERROR", 
                          f"❌ Fehler beim Schreiben von {file_path.name}: {str(e)}")
            return False
    
    def archiviere_datei(self, file_path: Path) -> bool:
        """
        Verschiebt verarbeitete Datei ins Archiv.
        
        Args:
            file_path: Pfad zur zu archivierenden Datei
            
        Returns:
            success_flag
        """
        try:
            if not file_path.exists():
                return False
            
            archive_path = self.archive_dir / file_path.name
            shutil.move(str(file_path), str(archive_path))
            
            log_service.log("csv_io", "archiviere_datei", "INFO", 
                          f"✓ Datei archiviert: {file_path.name}")
            
            return True
            
        except Exception as e:
            log_service.log("csv_io", "archiviere_datei", "ERROR", 
                          f"❌ Fehler beim Archivieren von {file_path.name}: {str(e)}")
            return False
    
    def extract_zip(self, zip_file: Path, target_dir: Optional[Path] = None) -> List[Path]:
        """
        Entpackt ZIP-Datei und gibt Liste der extrahierten CSV-Dateien zurück.
        
        Args:
            zip_file: Pfad zur ZIP-Datei
            target_dir: Zielverzeichnis (Standard: temporäres Verzeichnis)
            
        Returns:
            Liste der extrahierten CSV-Dateien
        """
        extracted_files = []
        
        if target_dir is None:
            target_dir = self.data_dir / "tmp"
            target_dir.mkdir(exist_ok=True)
        
        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            
            # Finde alle CSV-Dateien
            for file in target_dir.rglob("*.csv"):
                extracted_files.append(file)
            
            log_service.log("csv_io", "extract_zip", "INFO", 
                          f"✓ ZIP entpackt: {zip_file.name} ({len(extracted_files)} CSV-Dateien)")
            
            return extracted_files
            
        except Exception as e:
            log_service.log("csv_io", "extract_zip", "ERROR", 
                          f"❌ Fehler beim Entpacken von {zip_file.name}: {str(e)}")
            return []
    
    def create_zip(self, files: List[Path], zip_path: Path) -> bool:
        """
        Erstellt ZIP-Archiv aus Liste von Dateien.
        
        Args:
            files: Liste der zu packenden Dateien
            zip_path: Pfad für das ZIP-Archiv
            
        Returns:
            success_flag
        """
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in files:
                    if file.exists():
                        zipf.write(file, file.name)
            
            log_service.log("csv_io", "create_zip", "INFO", 
                          f"✓ ZIP erstellt: {zip_path.name} ({len(files)} Dateien)")
            
            return True
            
        except Exception as e:
            log_service.log("csv_io", "create_zip", "ERROR", 
                          f"❌ Fehler beim Erstellen von {zip_path.name}: {str(e)}")
            return False
