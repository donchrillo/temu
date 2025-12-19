"""JTL Repository - Data Access Layer für JTL Datenbank"""

from typing import Optional, Dict, List
from src.db.connection import get_db_connection
from src.services.logger import app_logger
from config.settings import DB_JTL

class JtlRepository:
    """Data Access Layer - ONLY JTL DB Operations"""
    
    def __init__(self, connection=None):
        """Optionale Injektierte Connection (für Pooling)"""
        self._conn = connection
    
    def _get_conn(self):
        """Hole Connection (gepooled oder neu)"""
        if self._conn:
            return self._conn
        return get_db_connection(DB_JTL)
    
    def insert_xml_import(self, xml_string: str) -> bool:
        """
        Importiere XML in JTL tXMLBestellImport Tabelle
        
        Args:
            xml_string: Komplette XML als String (ISO-8859-1)
        
        Returns:
            bool: True wenn erfolgreich
        """
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO [dbo].[tXMLBestellImport] (cText, nPlattform, nRechnung)
                VALUES (?, 5, 0)
            """, xml_string)
            
            # AutoCommit ist aktiv - keine commit() nötig!
            
            return True
        
        except Exception as e:
            app_logger.error(f"JTL Insert Fehler: {e}", exc_info=True)
            return False
    
    def get_imported_orders(self) -> Dict[str, bool]:
        """
        Hole Orders die schon importiert wurden
        
        Returns:
            dict: {bestell_id: True}
        """
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT 
                    [cBestellungInetBestellNr]
                FROM [dbo].[tXMLBestellImport]
                WHERE nPlattform = 5
                AND [cBestellungInetBestellNr] IS NOT NULL
            """)
            
            rows = cursor.fetchall()
            
            return {row[0]: True for row in rows}
        
        except Exception as e:
            app_logger.error(f"JTL Query Fehler: {e}", exc_info=True)
            return {}
    
    def get_xml_import_status(self, bestell_id: str) -> Optional[str]:
        """
        Hole Import Status für eine Bestellung
        
        Args:
            bestell_id: TEMU Bestellnummer
        
        Returns:
            str: Status ('pending', 'imported', 'processing') oder None
        """
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT TOP 1 
                    [dErstellt],
                    [dZugelesen]
                FROM [dbo].[tXMLBestellImport]
                WHERE [cBestellungInetBestellNr] = ?
                ORDER BY [kXMLBestellImport] DESC
            """, bestell_id)
            
            row = cursor.fetchone()
            
            if not row:
                return 'pending'  # Nicht importiert
            
            erstellt, zugelesen = row
            
            if zugelesen:
                return 'imported'  # Erfolgreich importiert
            else:
                return 'processing'  # Wird gerade verarbeitet
        
        except Exception as e:
            app_logger.error(f"JTL Status Query Fehler: {e}", exc_info=True)
            return None
    
    def get_import_errors(self, bestell_id: str = None) -> Dict[str, str]:
        """
        Hole Import Fehler aus JTL
        
        Args:
            bestell_id: Optional - nur Fehler für diese Bestellung
        
        Returns:
            dict: {bestell_id: error_message}
        """
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            if bestell_id:
                cursor.execute("""
                    SELECT 
                        [cBestellungInetBestellNr],
                        [cFehlerText]
                    FROM [dbo].[tXMLBestellImport]
                    WHERE nPlattform = 5
                    AND [cBestellungInetBestellNr] = ?
                    AND [cFehlerText] IS NOT NULL
                    AND [cFehlerText] != ''
                """, bestell_id)
            else:
                cursor.execute("""
                    SELECT 
                        [cBestellungInetBestellNr],
                        [cFehlerText]
                    FROM [dbo].[tXMLBestellImport]
                    WHERE nPlattform = 5
                    AND [cFehlerText] IS NOT NULL
                    AND [cFehlerText] != ''
                """)
            
            rows = cursor.fetchall()
            
            return {row[0]: row[1] for row in rows}
        
        except Exception as e:
            app_logger.error(f"JTL Error Query Fehler: {e}", exc_info=True)
            return {}
    
    def get_tracking_from_lieferschein(self, bestell_id: str) -> Optional[Dict]:
        """
        Hole Tracking aus JTL Lieferschein
        WICHTIG: Ermittle auch die korrekte TEMU Carrier ID!
        
        Args:
            bestell_id: TEMU Bestellnummer (z.B. PO-076-...)
        
        Returns:
            dict mit:
            - tracking_number: Tracking Nummer
            - carrier: Carrier Name (z.B. "DHL Paket")
            - carrier_id: TEMU Carrier ID (ermittelt aus Carrier Name!)
        """
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Hole aus JTL Lieferschein
            cursor.execute("""
                SELECT 
                    [cBestellungInetBestellNr],
                    [cVersandartName],
                    CAST([cTrackingId] AS VARCHAR(100))
                FROM [Versand].[lvLieferschein]
                LEFT JOIN [Versand].[lvLieferscheinpaket]
                    ON [Versand].[lvLieferscheinpaket].kLieferschein = 
                       [Versand].[lvLieferschein].kLieferschein
                WHERE [cBestellungInetBestellNr] = ?
            """, bestell_id)
            
            row = cursor.fetchone()
            
            if row:
                bestellnr, carrier_name, tracking_id = row
                
                # **WICHTIG:** Mapping von JTL Carrier Name zu TEMU Carrier ID
                # JTL kann haben: "DHL Paket", "DPD Paket", "DP Warenpost DE", etc.
                # Wir müssen Partial Match machen (case-insensitive)
                
                TEMU_CARRIER_MAPPING = {
                    'dhl': 141252268,           # TEMU ID für DHL
                    'dpd': 998264853,           # TEMU ID für DPD
                    'ups': 960246690,           # TEMU ID für UPS
                    'hermes': 123456789,        # TEMU ID für Hermes
                    'default': 141252268        # Fallback: DHL
                }
                
                # Partial Match (case-insensitive)
                carrier_id = TEMU_CARRIER_MAPPING['default']
                
                if carrier_name:
                    carrier_lower = carrier_name.lower()
                    for key in TEMU_CARRIER_MAPPING.keys():
                        if key in carrier_lower:  # "DHL Paket" enthält "dhl"
                            carrier_id = TEMU_CARRIER_MAPPING[key]
                            break
                
                return {
                    'bestell_id': bestellnr,
                    'carrier': carrier_name or 'DHL',
                    'carrier_id': carrier_id,
                    'tracking_number': tracking_id or ''
                }
            
            return None
        
        except Exception as e:
            app_logger.error(f"JTL Lieferschein Query Fehler: {e}", exc_info=True)
            return None
    
    def get_article_id_by_sku(self, sku: str) -> int:
        """
        Hole JTL Artikel-ID per SKU (cArtNr).
        
        Args:
            sku: Artikel-Numer (SKU)
        
        Returns:
            kArtikel (int) oder None wenn nicht gefunden
        """
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT kArtikel
                FROM eazybusiness.dbo.tArtikel
                WHERE cArtNr = ?
            """, sku)
            
            row = cursor.fetchone()
            return row[0] if row else None
        
        except Exception as e:
            app_logger.error(f"JTL Article ID Query Fehler: {e}", exc_info=True)
            return None
    
    def get_stock_by_article_id(self, article_id: int) -> int:
        """
        Hole verfügbaren Bestand aus JTL per Artikel-ID.
        
        Args:
            article_id: kArtikel aus tArtikel
        
        Returns:
            fVerfuegbar (int) oder 0 wenn nicht gefunden
        """
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT fVerfuegbar
                FROM eazybusiness.dbo.tlagerbestand
                WHERE kArtikel = ?
            """, article_id)
            
            row = cursor.fetchone()
            return int(row[0]) if row and row[0] else 0
        
        except Exception as e:
            app_logger.error(f"JTL Stock Query Fehler: {e}", exc_info=True)
            return 0
