"""Validation Service - Validierung von OrderIDs und Konten"""

import re
from typing import Dict, List, Tuple
import pandas as pd

from modules.shared import log_service


class ValidationService:
    """Service für CSV-Datenvalidierung (Amazon DATEV Exporte)"""
    
    # Pattern für Amazon OrderIDs (z.B. 306-1234567-8910111)
    # Format: XXX-XXXXXXX-XXXXXXX (3 Ziffern - 7 Ziffern - 7 Ziffern)
    ORDER_ID_PATTERN = re.compile(r'^\d{3}-\d{7}-\d{7}$')
    
    # Kritische Konten (0-20) die NICHT ersetzt werden dürfen
    CRITICAL_ACCOUNTS = set(range(0, 21))
    
    def __init__(self):
        """Initialisiere Validation Service"""
        self.validation_errors: List[Dict] = []
        self.validation_warnings: List[Dict] = []
    
    def reset_validation_results(self):
        """Setzt Validierungsergebnisse zurück"""
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_order_id_pattern(self, order_id: str) -> bool:
        """
        Prüft ob OrderID dem erwarteten Amazon-Pattern entspricht.
        Amazon Format: XXX-XXXXXXX-XXXXXXX (z.B. 306-1234567-8910111)
        
        Args:
            order_id: OrderID String
            
        Returns:
            bool: True wenn Pattern stimmt
        """
        if not order_id or pd.isna(order_id):
            return False
        
        return bool(self.ORDER_ID_PATTERN.match(str(order_id).strip()))
    
    def is_critical_account(self, account: str) -> bool:
        """
        Prüft ob Konto in kritischem Bereich (0-20) liegt.
        
        Args:
            account: Kontonummer als String
            
        Returns:
            bool: True wenn kritisches Konto
        """
        try:
            account_num = int(str(account).strip())
            return account_num in self.CRITICAL_ACCOUNTS
        except (ValueError, AttributeError):
            return False
    
    def validate_csv_structure(self, df: pd.DataFrame, job_id: str,
                              required_columns: List[str] = None) -> Tuple[bool, List[str]]:
        """
        Validiert CSV-Struktur (erforderliche Spalten für DATEV Export).
        
        Args:
            df: DataFrame zu validieren
            job_id: Job ID für Logging
            required_columns: Liste erforderlicher Spaltennamen
            
        Returns:
            Tuple[bool, List[str]]: (Erfolg, Liste fehlender Spalten)
        """
        if required_columns is None:
            # DATEV Standard-Spalten für Amazon Export
            required_columns = [
                'Belegfeld 1',  # Amazon OrderID
                'Gegenkonto (ohne BU-Schlüssel)'  # Kritische Konten-Prüfung
            ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            log_service.log(job_id, "csv_validation", "ERROR", 
                          f"❌ Fehlende Spalten: {', '.join(missing_columns)}")
            self.validation_errors.append({
                'type': 'MISSING_COLUMNS',
                'columns': missing_columns,
                'message': f"Erforderliche Spalten fehlen: {', '.join(missing_columns)}"
            })
            return False, missing_columns
        
        log_service.log(job_id, "csv_validation", "INFO", 
                       "✓ CSV-Struktur valid - alle erforderlichen Spalten vorhanden")
        return True, []
    
    def validate_dataframe(self, df: pd.DataFrame, job_id: str, 
                          beleg_column: str = 'Belegfeld 1',
                          gegenkonto_column: str = 'Gegenkonto (ohne BU-Schlüssel)') -> Dict:
        """
        Führt umfassende Validierung eines DataFrames durch.
        
        Args:
            df: DataFrame zu validieren
            beleg_column: Name der OrderID-Spalte (Standard: 'Belegfeld 1' für DATEV)
            gegenkonto_column: Name der Gegenkonto-Spalte
            
        Returns:
            Dict mit Validierungsergebnissen:
                - valid_rows: Anzahl valider Zeilen
                - invalid_pattern: Anzahl ungültiger OrderID-Patterns
                - critical_accounts: Anzahl kritischer Gegenkonten
                - errors: Liste von Fehlern
                - warnings: Liste von Warnungen
        """
        self.reset_validation_results()
        
        log_service.log(job_id, "csv_validation", "INFO", 
                       f"→ Starte Validierung von {len(df)} Zeilen...")
        
        valid_rows = 0
        invalid_pattern_count = 0
        critical_account_count = 0
        
        # Prüfe ob erforderliche Spalten vorhanden sind
        if beleg_column not in df.columns:
            self.validation_errors.append({
                'type': 'MISSING_COLUMN',
                'column': beleg_column,
                'message': f"OrderID-Spalte '{beleg_column}' nicht gefunden"
            })
            log_service.log(job_id, "csv_validation", "ERROR", 
                          f"❌ OrderID-Spalte '{beleg_column}' nicht gefunden")
            return self._build_validation_result(0, 0, 0)
        
        # Validiere jede Zeile
        for idx, row in df.iterrows():
            order_id = str(row.get(beleg_column, '')).strip()
            gegenkonto = str(row.get(gegenkonto_column, '')).strip() if gegenkonto_column in df.columns else ''
            
            # OrderID Pattern Validierung
            if not self.validate_order_id_pattern(order_id):
                invalid_pattern_count += 1
                self.validation_warnings.append({
                    'type': 'INVALID_PATTERN',
                    'row': idx + 2,  # +2 wegen 0-Index, Header und Metazeile
                    'order_id': order_id,
                    'message': f"Zeile {idx + 2}: Ungültiges Amazon OrderID Pattern: '{order_id}'"
                })
                continue
            
            # Kritische Gegenkonten Prüfung
            if gegenkonto and self.is_critical_account(gegenkonto):
                critical_account_count += 1
                self.validation_warnings.append({
                    'type': 'CRITICAL_ACCOUNT',
                    'row': idx + 2,
                    'account': gegenkonto,
                    'message': f"Zeile {idx + 2}: Kritisches Gegenkonto '{gegenkonto}' (0-20)"
                })
                continue
            
            valid_rows += 1
        
        # Logging
        log_service.log(job_id, "csv_validation", "INFO", 
                       f"✓ Validierung abgeschlossen:")
        log_service.log(job_id, "csv_validation", "INFO", 
                       f"  • {valid_rows} valide Zeilen")
        
        if invalid_pattern_count > 0:
            log_service.log(job_id, "csv_validation", "WARNING", 
                           f"  ⚠ {invalid_pattern_count} ungültige Amazon OrderID Patterns")
        
        if critical_account_count > 0:
            log_service.log(job_id, "csv_validation", "WARNING", 
                           f"  ⚠ {critical_account_count} kritische Gegenkonten (0-20)")
        
        return self._build_validation_result(valid_rows, invalid_pattern_count, critical_account_count)
    
    def _build_validation_result(self, valid_rows: int, 
                                invalid_pattern: int, 
                                critical_accounts: int) -> Dict:
        """
        Erstellt Validierungsergebnis-Dictionary.
        
        Returns:
            Dict mit Validierungsergebnissen
        """
        return {
            'valid_rows': valid_rows,
            'invalid_pattern': invalid_pattern,
            'critical_accounts': critical_accounts,
            'errors': self.validation_errors.copy(),
            'warnings': self.validation_warnings.copy(),
            'success': len(self.validation_errors) == 0
        }
    
    def check_data_integrity(self, df: pd.DataFrame, job_id: str) -> bool:
        """
        Prüft grundlegende Datenintegrität (Keine Null-Werte in Schlüsselspalten).
        DATEV Standard: Belegfeld 1 & Gegenkonto dürfen nicht leer sein.
        
        Args:
            df: DataFrame zu prüfen
            job_id: Job ID für Logging
            
        Returns:
            bool: True wenn Datenintegrität OK
        """
        key_columns = ['Belegfeld 1', 'Gegenkonto (ohne BU-Schlüssel)']
        
        integrity_ok = True
        
        for col in key_columns:
            if col in df.columns:
                null_count = df[col].isna().sum()
                if null_count > 0:
                    log_service.log(job_id, "csv_validation", "WARNING", 
                                   f"⚠ {null_count} NULL-Werte in Spalte '{col}'")
                    integrity_ok = False
        
        if integrity_ok:
            log_service.log(job_id, "csv_validation", "INFO", 
                           "✓ Datenintegrität OK - keine NULL-Werte in Schlüsselspalten")
        
        return integrity_ok
