"""
Replacement Service - Ersetzung von Amazon OrderIDs durch JTL Kundennummern

Basiert auf: tmp/csv_verarbeiter_original/src/verarbeitung_logik.py

WICHTIG: Bei erfolgreicher Ersetzung werden Zusatzfelder gesetzt:
- "Zusatzinformation - Art 1" = "Prüfung"
- "Zusatzinformation- Inhalt 1" = "AmazonOrderID-Check durchgeführt am DATUM"
"""

import pandas as pd
from datetime import date
from typing import Dict, List, Tuple
from functools import lru_cache

from modules.shared import log_service, app_logger
from modules.shared.database.repositories.jtl_common.jtl_repository import JtlRepository


class ReplacementService:
    """Service für OrderID-Ersetzung mit Zusatzfeld-Markierung"""
    
    def __init__(self):
        """Initialisiert Service mit JTL Repository"""
        self.jtl_repo = JtlRepository()
        self._cache = {}  # Cache für wiederholte OrderIDs
    
    @lru_cache(maxsize=1024)
    def hole_kundennummer_cached(self, order_id: str) -> str:
        """
        Cached version der JTL-Abfrage.
        
        Args:
            order_id: Amazon OrderID (z.B. "306-1234567-8910111")
            
        Returns:
            Kundennummer oder None
        """
        try:
            result = self.jtl_repo.get_customer_number_by_order_id(order_id.strip())
            return result if result else None
        except Exception as e:
            log_service.log("replacement", "hole_kundennummer", "ERROR", 
                          f"❌ Fehler bei SQL-Abfrage für {order_id}: {str(e)}")
            return None
    
    def initialisiere_zusatzfelder(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ergänzt Zusatzspalten für Prüfmarken, falls sie fehlen.
        
        Diese Felder werden verwendet, um Verarbeitungsvermerke in der Datei zu hinterlassen.
        
        Args:
            df: Eingelesene CSV-Daten
            
        Returns:
            DataFrame mit garantierten Zusatzspalten
        """
        if "Zusatzinformation - Art 1" not in df.columns:
            df["Zusatzinformation - Art 1"] = ""
        if "Zusatzinformation- Inhalt 1" not in df.columns:
            df["Zusatzinformation- Inhalt 1"] = ""
        
        return df
    
    def ersetze_amazon_order_ids(
        self, 
        df: pd.DataFrame, 
        dateiname: str,
        skip_critical_accounts: bool = True
    ) -> Dict:
        """
        Ersetzt Amazon OrderIDs durch JTL Kundennummern und setzt Prüfmarken.
        
        WICHTIG: Bei erfolgreicher Ersetzung werden folgende Felder gesetzt:
        - "Zusatzinformation - Art 1" = "Prüfung"
        - "Zusatzinformation- Inhalt 1" = "AmazonOrderID-Check durchgeführt am DATUM"
        
        Args:
            df: DataFrame mit CSV-Daten
            dateiname: Name der Datei (für Logging)
            skip_critical_accounts: Konten 0-20 überspringen
            
        Returns:
            Dict mit Statistiken:
            {
                "ersetzt": int,           # Erfolgreich ersetzt
                "nicht_gefunden": int,     # OrderID nicht in DB
                "gesamt": int,             # Gesamt verarbeitet
                "aenderungen": List[Dict], # Details der Änderungen
                "nicht_gefunden_liste": List[Dict]  # Details nicht gefundener IDs
            }
        """
        heute = date.today().isoformat()
        
        result = {
            "ersetzt": 0,
            "nicht_gefunden": 0,
            "gesamt": 0,
            "aenderungen": [],
            "nicht_gefunden_liste": []
        }
        
        # Sicherstellen, dass Zusatzfelder existieren
        df = self.initialisiere_zusatzfelder(df)
        
        # Prüfe ob Spalte "Belegfeld 1" existiert
        if "Belegfeld 1" not in df.columns:
            log_service.log("replacement", "ersetze_amazon_order_ids", "ERROR", 
                          f"❌ Spalte 'Belegfeld 1' nicht gefunden in {dateiname}")
            return result
        
       # Import der Validierung
        from .validation_service import ValidationService
        validator = ValidationService()
        
        # Iteriere über alle Zeilen mit Amazon OrderID
        for idx, row in df.iterrows():
            beleg = str(row["Belegfeld 1"]).strip()
            
            # Prüfe ob es eine Amazon OrderID ist
            if not validator.ist_amazon_bestellnummer(beleg):
                continue
            
            result["gesamt"] += 1
            
            try:
                # Hole Kundennummer aus JTL
                kundennr = self.hole_kundennummer_cached(beleg)
                
                if kundennr:
                    # ✅ Erfolgreiche Ersetzung
                    df.at[idx, "Belegfeld 1"] = kundennr
                    df.at[idx, "Zusatzinformation - Art 1"] = "Prüfung"
                    df.at[idx, "Zusatzinformation- Inhalt 1"] = f"AmazonOrderID-Check durchgeführt am {heute}"
                    
                    result["ersetzt"] += 1
                    result["aenderungen"].append({
                        "datei": dateiname,
                        "zeile": idx + 3,  # +3 wegen Metazeile + Header + 0-basiert
                        "alte_order_id": beleg,
                        "neue_kundennummer": kundennr
                    })
                    
                    log_service.log("replacement", "ersetze_amazon_order_ids", "INFO", 
                                  f"✓ Zeile {idx + 3}: {beleg} → {kundennr}")
                
                else:
                    # ❌ Nicht gefunden
                    result["nicht_gefunden"] += 1
                    result["nicht_gefunden_liste"].append({
                        "datei": dateiname,
                        "zeile": idx + 3,
                        "order_id": beleg
                    })
                    
                    log_service.log("replacement", "ersetze_amazon_order_ids", "WARN", 
                                  f"⚠️ Zeile {idx + 3}: OrderID {beleg} nicht gefunden")
                    
            except Exception as e:
                log_service.log("replacement", "ersetze_amazon_order_ids", "ERROR", 
                              f"❌ Fehler bei Zeile {idx + 3}: {str(e)}")
        
        # Zusammenfassung
        log_service.log("replacement", "ersetze_amazon_order_ids", "INFO", 
                      f"📊 {dateiname}: {result['ersetzt']} ersetzt, " +
                      f"{result['nicht_gefunden']} nicht gefunden, " +
                      f"{result['gesamt']} gesamt")
        
        return result
    
    def get_dateiname_mit_praefix(self, dateiname: str, hat_kritisches_konto: bool) -> str:
        """
        Gibt Dateinamen mit "#_" Präfix zurück, wenn kritisches Gegenkonto vorhanden.
        
        Args:
            dateiname: Original-Dateiname
            hat_kritisches_konto: True wenn kritisches Konto (0-20) vorhanden
            
        Returns:
            Dateiname mit oder ohne "#_" Präfix
        """
        if hat_kritisches_konto:
            if not dateiname.startswith("#_"):
                return f"#_{dateiname}"
        return dateiname
