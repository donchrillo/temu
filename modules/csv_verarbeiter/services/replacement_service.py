"""Replacement Service - Ersetzung von OrderIDs mit JTL-Kundennummern"""

from typing import Dict, List, Optional, Tuple
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
    
    def get_customer_number(self, email: str, job_id: str) -> Optional[str]:
        """
        Holt Kundennummer aus JTL DB (mit Cache).
        
        Args:
            email: E-Mail-Adresse des Kunden
            job_id: Job ID für Logging
            
        Returns:
            str: Kundennummer oder None wenn nicht gefunden
        """
        # Cache-Lookup
        if email in self.customer_cache:
            return self.customer_cache[email]
        
        # DB-Abfrage
        try:
            customer_number = self.jtl_repo.get_customer_number_by_email(email)
            
            if customer_number:
                # Im Cache speichern
                self.customer_cache[email] = customer_number
                return customer_number
            else:
                log_service.log(job_id, "csv_replacement", "WARNING", 
                              f"⚠ Keine Kundennummer gefunden für: {email}")
                return None
                
        except Exception as e:
            log_service.log(job_id, "csv_replacement", "ERROR", 
                          f"❌ DB-Fehler bei Kundennummer-Abfrage für {email}: {str(e)}")
            return None
    
    def extract_email_from_order_id(self, order_id: str) -> Optional[str]:
        """
        Extrahiert E-Mail aus OrderID (falls im Format enthalten).
        
        HINWEIS: Diese Methode ist ein Platzhalter. In der realen Implementierung
        müsste die Logik angepasst werden, wie die E-Mail-Adresse ermittelt wird:
        - Aus einer zusätzlichen Spalte im CSV
        - Aus einer separaten Mapping-Tabelle
        - Über eine andere Identifikation (z.B. über temu_orders Tabelle)
        
        Args:
            order_id: TEMU OrderID (z.B. PO-076-00176873718391408)
            
        Returns:
            str: E-Mail-Adresse oder None
        """
        # TODO: Implementierung anpassen basierend auf tatsächlicher Datenstruktur
        # Option 1: Lookup in temu_orders Tabelle via order_id
        # Option 2: E-Mail aus zusätzlicher CSV-Spalte
        # Option 3: Separates Mapping-File
        
        # Für jetzt: Platzhalter
        return None
    
    def get_customer_number_by_order_id(self, order_id: str, job_id: str,
                                       email_column_value: Optional[str] = None) -> Optional[str]:
        """
        Ermittelt Kundennummer für eine OrderID.
        
        Args:
            order_id: TEMU OrderID
            job_id: Job ID für Logging
            email_column_value: Optional - E-Mail aus CSV-Spalte
            
        Returns:
            str: Kundennummer oder None
        """
        # Strategie 1: E-Mail aus Parameter (wenn CSV eine E-Mail-Spalte hat)
        if email_column_value and pd.notna(email_column_value):
            email = str(email_column_value).strip()
            if email:
                return self.get_customer_number(email, job_id)
        
        # Strategie 2: E-Mail aus OrderID extrahieren (falls implementiert)
        email = self.extract_email_from_order_id(order_id)
        if email:
            return self.get_customer_number(email, job_id)
        
        # Strategie 3: Lookup in temu_orders Tabelle (falls verfügbar)
        # TODO: Implementierung über order_repo wenn benötigt
        
        return None
    
    def replace_order_ids_in_dataframe(self, df: pd.DataFrame, job_id: str,
                                      order_id_column: str = 'Beleg',
                                      email_column: Optional[str] = None,
                                      skip_critical_accounts: bool = True) -> pd.DataFrame:
        """
        Ersetzt OrderIDs mit JTL-Kundennummern im DataFrame.
        
        Args:
            df: Zu verarbeitender DataFrame
            job_id: Job ID für Logging
            order_id_column: Name der OrderID-Spalte (Standard: 'Beleg')
            email_column: Optional - Name der E-Mail-Spalte im CSV
            skip_critical_accounts: Kritische Konten (0-20) überspringen
            
        Returns:
            pd.DataFrame: Verarbeiteter DataFrame
        """
        self.reset_stats()
        
        log_service.log(job_id, "csv_replacement", "INFO", 
                       f"→ Starte OrderID-Ersetzung für {len(df)} Zeilen...")
        
        # Kopie erstellen um Original nicht zu verändern
        df_processed = df.copy()
        
        # Prüfe ob OrderID-Spalte existiert
        if order_id_column not in df_processed.columns:
            log_service.log(job_id, "csv_replacement", "ERROR", 
                          f"❌ OrderID-Spalte '{order_id_column}' nicht gefunden")
            return df_processed
        
        # Validierung Service für Konten-Prüfung
        from .validation_service import ValidationService
        validator = ValidationService()
        
        # Iteriere über DataFrame
        for idx, row in df_processed.iterrows():
            self.replacement_stats['total'] += 1
            
            order_id = str(row.get(order_id_column, '')).strip()
            konto = str(row.get('Konto', '')).strip()
            gegenkonto = str(row.get('Gegenkonto', '')).strip()
            
            # Skip: Kritische Konten
            if skip_critical_accounts:
                if validator.is_critical_account(konto) or validator.is_critical_account(gegenkonto):
                    self.replacement_stats['skipped_critical'] += 1
                    continue
            
            # Skip: Ungültiges OrderID Pattern
            if not validator.validate_order_id_pattern(order_id):
                self.replacement_stats['skipped_invalid'] += 1
                continue
            
            # E-Mail-Wert aus DataFrame holen (falls Spalte existiert)
            email_value = None
            if email_column and email_column in df_processed.columns:
                email_value = row.get(email_column)
            
            # Kundennummer ermitteln
            customer_number = self.get_customer_number_by_order_id(
                order_id, 
                job_id,
                email_column_value=email_value
            )
            
            # Ersetzung durchführen
            if customer_number:
                df_processed.at[idx, order_id_column] = customer_number
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
                           f"  • {self.replacement_stats['skipped_critical']} kritische Konten übersprungen")
        
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
