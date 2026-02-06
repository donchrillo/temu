"""Replacement Service - Ersetzung von Amazon OrderIDs mit JTL-Kundennummern"""

from typing import Dict, List, Optional
import pandas as pd

from modules.shared import log_service
from modules.shared.database.repositories.jtl_common.jtl_repository import JtlRepository


class ReplacementService:
    """Service für OrderID → Kundennummer Ersetzung"""
    
    def __init__(self, jtl_repo: Optional[JtlRepository] = None):
        """
        Args:
            jtl_repo: Optional JTL Repository (wird erstellt falls None)
        """
        self.jtl_repo = jtl_repo or JtlRepository()
        self.customer_cache: Dict[str, str] = {}  # Email -> Kundennummer Cache
        self.replacement_stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped_critical': 0,
            'skipped_invalid': 0
        }
    
    def reset_stats(self):
        """Setzt Statistiken zurück"""
        self.replacement_stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped_critical': 0,
            'skipped_invalid': 0
        }
        self.customer_cache.clear()
    
    def get_customer_number_by_amazon_order_id(self, order_id: str, job_id: str) -> Optional[str]:
        """
        Holt Kundennummer aus JTL DB via Amazon OrderID (mit Cache).
        Abfrage: SELECT cKundennr FROM tAuftrag WHERE cExterneAuftragsnummer = order_id
        
        Args:
            order_id: Amazon OrderID (z.B. 306-1234567-8910111)
            job_id: Job ID für Logging
            
        Returns:
            str: Kundennummer oder None wenn nicht gefunden
        """
        # Cache-Lookup
        if order_id in self.customer_cache:
            return self.customer_cache[order_id]
        
        # DB-Abfrage
        try:
            customer_number = self.jtl_repo.get_customer_number_by_order_id(order_id)
            
            if customer_number:
                # Im Cache speichern
                self.customer_cache[order_id] = customer_number
                return customer_number
            else:
                log_service.log(job_id, "csv_replacement", "WARNING", 
                              f"⚠ Keine Kundennummer gefunden für Amazon OrderID: {order_id}")
                return None
                
        except Exception as e:
            log_service.log(job_id, "csv_replacement", "ERROR", 
                          f"❌ DB-Fehler bei OrderID-Abfrage {order_id}: {str(e)}")
            return None
    

    
    def replace_amazon_order_ids(self, df: pd.DataFrame, job_id: str,
                                beleg_column: str = 'Belegfeld 1',
                                gegenkonto_column: str = 'Gegenkonto (ohne BU-Schlüssel)',
                                skip_critical_accounts: bool = True) -> pd.DataFrame:
        """
        Ersetzt Amazon OrderIDs mit JTL-Kundennummern im DataFrame.
        
        DATEV Standard-Spalten:
        - 'Belegfeld 1': Enthält Amazon OrderID
        - 'Gegenkonto (ohne BU-Schlüssel)': Prüfung auf kritische Konten (0-20)
        
        Args:
            df: Zu verarbeitender DataFrame
            job_id: Job ID für Logging
            beleg_column: Name der Spalte mit OrderID (Standard: 'Belegfeld 1')
            gegenkonto_column: Name der Gegenkonto-Spalte
            skip_critical_accounts: Kritische Konten (0-20) überspringen
            
        Returns:
            pd.DataFrame: Verarbeiteter DataFrame
        """
        self.reset_stats()
        
        log_service.log(job_id, "csv_replacement", "INFO", 
                       f"→ Starte Amazon OrderID-Ersetzung für {len(df)} Zeilen...")
        
        # Kopie erstellen um Original nicht zu verändern
        df_processed = df.copy()
        
        # Prüfe ob erforderliche Spalten existieren
        if beleg_column not in df_processed.columns:
            log_service.log(job_id, "csv_replacement", "ERROR", 
                          f"❌ OrderID-Spalte '{beleg_column}' nicht gefunden")
            return df_processed
        
        # Validierung Service für Konten-Prüfung
        from .validation_service import ValidationService
        validator = ValidationService()
        
        # Iteriere über DataFrame
        for idx, row in df_processed.iterrows():
            self.replacement_stats['total'] += 1
            
            order_id = str(row.get(beleg_column, '')).strip()
            gegenkonto = str(row.get(gegenkonto_column, '')).strip() if gegenkonto_column in df_processed.columns else ''
            
            # Skip: Kritische Gegenkonten
            if skip_critical_accounts and gegenkonto:
                if validator.is_critical_account(gegenkonto):
                    self.replacement_stats['skipped_critical'] += 1
                    continue
            
            # Skip: Ungültiges OrderID Pattern
            if not validator.validate_order_id_pattern(order_id):
                self.replacement_stats['skipped_invalid'] += 1
                continue
            
            # Kundennummer ermitteln via Amazon OrderID
            customer_number = self.get_customer_number_by_amazon_order_id(order_id, job_id)
            
            # Ersetzung durchführen
            if customer_number:
                df_processed.at[idx, beleg_column] = customer_number
                self.replacement_stats['success'] += 1
            else:
                self.replacement_stats['failed'] += 1
        
        # Logging
        log_service.log(job_id, "csv_replacement", "INFO", 
                       "✓ OrderID-Ersetzung abgeschlossen:")
        log_service.log(job_id, "csv_replacement", "INFO", 
                       f"  • {self.replacement_stats['total']} Zeilen verarbeitet")
        log_service.log(job_id, "csv_replacement", "INFO", 
                       f"  • {self.replacement_stats['success']} erfolgreich ersetzt")
        
        if self.replacement_stats['failed'] > 0:
            log_service.log(job_id, "csv_replacement", "WARNING", 
                           f"  ⚠ {self.replacement_stats['failed']} Ersetzungen fehlgeschlagen")
        
        if self.replacement_stats['skipped_critical'] > 0:
            log_service.log(job_id, "csv_replacement", "INFO", 
                           f"  • {self.replacement_stats['skipped_critical']} kritische Gegenkonten übersprungen")
        
        if self.replacement_stats['skipped_invalid'] > 0:
            log_service.log(job_id, "csv_replacement", "WARNING", 
                           f"  ⚠ {self.replacement_stats['skipped_invalid']} ungültige OrderIDs übersprungen")
        
        return df_processed
    
    def get_replacement_stats(self) -> Dict:
        """
        Gibt aktuelle Ersetzungsstatistiken zurück.
        
        Returns:
            Dict mit Statistiken
        """
        return self.replacement_stats.copy()
    
    def clear_cache(self):
        """Löscht den Kundennummern-Cache"""
        self.customer_cache.clear()
        log_service.log("SYSTEM", "csv_replacement", "INFO", 
                       "✓ Kundennummern-Cache geleert")
