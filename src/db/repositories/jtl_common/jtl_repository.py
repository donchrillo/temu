"""JTL Repository - SQLAlchemy + Raw SQL (Final)"""

from typing import Optional, Dict, List
from sqlalchemy import text, bindparam
from sqlalchemy.engine import Connection
from src.services.logger import app_logger
from config.settings import DB_JTL
from src.db.repositories.base import BaseRepository

class JtlRepository(BaseRepository):
    """Data Access Layer - ONLY JTL DB Operations"""
    
    def __init__(self, connection: Optional[Connection] = None):
        """Optionale injizierte Connection; setzt DB auf JTL."""
        super().__init__(connection, db_name=DB_JTL)

    def insert_xml_import(self, xml_string: str) -> bool:
        """Importiere XML in JTL tXMLBestellImport Tabelle"""
        try:
            self._execute_stmt("""
                INSERT INTO [dbo].[tXMLBestellImport] (cText, nPlattform, nRechnung)
                VALUES (:xml_string, 5, 0)
            """, {"xml_string": xml_string})
            return True
        except Exception as e:
            app_logger.error(f"JTL insert_xml_import: {e}", exc_info=True)
            return False
    
    def get_imported_orders(self) -> Dict[str, bool]:
        """Hole Orders die schon importiert wurden"""
        try:
            sql = """
                SELECT DISTINCT [cBestellungInetBestellNr]
                FROM [dbo].[tXMLBestellImport]
                WHERE nPlattform = 5
                AND [cBestellungInetBestellNr] IS NOT NULL
            """
            rows = self._fetch_all(sql)
            return {row[0]: True for row in rows}
        except Exception as e:
            app_logger.error(f"JTL get_imported_orders: {e}", exc_info=True)
            return {}
    
    def get_xml_import_status(self, bestell_id: str) -> Optional[str]:
        """Hole Import Status für eine Bestellung"""
        try:
            sql = """
                SELECT TOP 1 [dErstellt], [dZugelesen]
                FROM [dbo].[tXMLBestellImport]
                WHERE [cBestellungInetBestellNr] = :bestell_id
                ORDER BY [kXMLBestellImport] DESC
            """
            params = {"bestell_id": bestell_id}
            row = self._fetch_one(sql, params)
            if not row:
                return 'pending'
            
            # row[1] ist [dZugelesen]
            return 'imported' if row[1] else 'processing'

        except Exception as e:
            app_logger.error(f"JTL get_xml_import_status: {e}", exc_info=True)
            return None
    
    def get_import_errors(self, bestell_id: str = None) -> Dict[str, str]:
        """Hole Import Fehler aus JTL"""
        try:
            params = {}
            if bestell_id:
                sql = """
                    SELECT [cBestellungInetBestellNr], [cFehlerText]
                    FROM [dbo].[tXMLBestellImport]
                    WHERE nPlattform = 5
                    AND [cBestellungInetBestellNr] = :bestell_id
                    AND [cFehlerText] IS NOT NULL
                    AND [cFehlerText] != ''
                """
                params["bestell_id"] = bestell_id
            else:
                sql = """
                    SELECT [cBestellungInetBestellNr], [cFehlerText]
                    FROM [dbo].[tXMLBestellImport]
                    WHERE nPlattform = 5
                    AND [cFehlerText] IS NOT NULL
                    AND [cFehlerText] != ''
                """
            rows = self._fetch_all(sql, params)
            return {row[0]: row[1] for row in rows}
                    
        except Exception as e:
            app_logger.error(f"JTL get_import_errors: {e}", exc_info=True)
            return {}
    
    def get_article_id_by_sku(self, sku: str) -> Optional[int]:
        """Hole JTL Artikel-ID per SKU"""
        try:
            sql = """
                SELECT TOP 1 [kArtikel]
                FROM [eazybusiness].[dbo].[tArtikel]
                WHERE [cArtNr] = :sku
            """
            row = self._fetch_one(sql, {"sku": sku})
            return int(row[0]) if row else None
        except Exception as e:
            app_logger.error(f"JTL get_article_id_by_sku: {e}", exc_info=True)
            return None
    
    def get_stock_by_article_id(self, article_id: int) -> int:
        """Hole Bestand aus JTL pro Artikel-ID"""
        try:
            # Verfügbarer Bestand = fBestand - nPuffer für Lager 2, mindestens 0
            sql = """
                SELECT TOP 1 v.[fBestand], t.[nPuffer]
                FROM [eazybusiness].[dbo].[tArtikel] t
                JOIN [eazybusiness].[dbo].[vLagerbestandProLager] v
                  ON t.[kArtikel] = v.[kArtikel]
                WHERE t.[kArtikel] = :article_id
                  AND v.[kWarenlager] = 2
            """
            params = {"article_id": article_id}
            row = self._fetch_one(sql, params)
            if not row:
                return 0
            f_bestand, n_puffer = float(row[0]), int(row[1])
            available = max(0, int(f_bestand) - n_puffer)
            return available
        except Exception as e:
            app_logger.error(f"JTL get_stock_by_article_id: {e}", exc_info=True)
            return 0
    
    def get_stocks_by_article_ids(self, article_ids: List[int]) -> Dict[int, float]:
        """
        Hole Bestände für viele Artikel gleichzeitig (Batch).
        Verhindert das N+1 Problem.
        Chunking bei 1.000 IDs wegen SQL Server 2100 Parameter Limit.
        """
        if not article_ids:
            return {}
        
        # Deduplizieren
        ids = list(set(article_ids))
        result_map = {}
        chunk_size = 1000
        
        try:
            # Wir müssen die Liste stückeln, da MS SQL max 2100 Parameter erlaubt
            for i in range(0, len(ids), chunk_size):
                chunk = ids[i:i + chunk_size]
                
                # Hole Bestände und Puffer für Lager 2 pro Artikel
                # Verfügbarer Bestand = fBestand - nPuffer, min 0 (in Python berechnet)
                sql = text("""
                    SELECT t.[kArtikel], v.[fBestand], t.[nPuffer]
                    FROM [eazybusiness].[dbo].[tArtikel] t
                    JOIN [eazybusiness].[dbo].[vLagerbestandProLager] v
                      ON t.[kArtikel] = v.[kArtikel]
                    WHERE t.[kArtikel] IN :ids
                      AND v.[kWarenlager] = 2
                """).bindparams(bindparam('ids', expanding=True))
                rows = self._fetch_all(sql, {"ids": chunk})
                for row in rows:
                    k_artikel = int(row[0])
                    f_bestand = float(row[1])
                    n_puffer = int(row[2])
                    available = max(0, int(f_bestand) - n_puffer)
                    result_map[k_artikel] = float(available)
                            
            return result_map
            
        except Exception as e:
            app_logger.error(f"JTL get_stocks_by_article_ids: {e}", exc_info=True)
            return {}
    
    def get_tracking_from_lieferschein(self, bestell_id: str) -> Optional[Dict[str, str]]:
        """Hole Tracking aus JTL Lieferscheindaten"""
        try:
            # Nutzung der Versand-Views analog zum Legacy-Code
            sql = """
                SELECT TOP 1
                    ls.[cBestellungInetBestellNr],
                    lp.[cVersandartName],
                    CAST(lp.[cTrackingId] AS VARCHAR(100)) AS cTrackingId
                FROM [Versand].[lvLieferschein] ls
                LEFT JOIN [Versand].[lvLieferscheinpaket] lp
                  ON lp.[kLieferschein] = ls.[kLieferschein]
                WHERE ls.[cBestellungInetBestellNr] = :bestell_id
            """
            params = {"bestell_id": bestell_id}
            row = self._fetch_one(sql, params)
            if not row:
                return None
            
            bestellnr, carrier_name, tracking_id = row[0], row[1], row[2]
            return {
                "bestell_id": bestellnr,
                "carrier": carrier_name or "",
                "tracking_number": tracking_id or ""
            }
        except Exception as e:
            app_logger.error(f"JTL get_tracking_from_lieferschein: {e}", exc_info=True)
            return None

    def get_customer_number_by_email(self, email: str) -> Optional[str]:
        """Hole JTL Kundennummer (cKundenNr) per E-Mail-Adresse."""
        if not email:
            return None
        try:
            # Hinweis: E-Mail steht in View eazybusiness.Kunde.lvKunde als cEMail
            sql = """
                SELECT TOP 1 [cKundenNr]
                FROM [eazybusiness].[Kunde].[lvKunde]
                WHERE LOWER([cEMail]) = LOWER(:email)
                ORDER BY [kKunde] DESC
            """
            row = self._fetch_one(sql, {"email": email})
            if not row:
                return None
            kunden_nr = row[0]
            return kunden_nr if kunden_nr else None
        except Exception as e:
            app_logger.error(f"JTL get_customer_number_by_email: {e}", exc_info=True)
            return None