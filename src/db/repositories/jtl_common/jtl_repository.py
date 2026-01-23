"""JTL Repository - SQLAlchemy + Raw SQL"""

from typing import Optional, Dict, List
from sqlalchemy import text
from src.services.logger import app_logger
from config.settings import DB_JTL

class JtlRepository:
    """Data Access Layer - ONLY JTL DB Operations"""
    
    def __init__(self, connection=None):
        """Optionale Injektierte Connection (für Pooling)"""
        self._conn = connection
    
    def _get_conn(self):
        """Hole Connection"""
        if self._conn:
            return self._conn
        from src.db.connection import get_engine
        return get_db_connection(DB_JTL)
    
    def insert_xml_import(self, xml_string: str) -> bool:
        """Importiere XML in JTL tXMLBestellImport Tabelle"""
        try:
            if self._conn:
                self._conn.execute(text("""
                    INSERT INTO [dbo].[tXMLBestellImport] (cText, nPlattform, nRechnung)
                    VALUES (:xml_string, 5, 0)
                """), {"xml_string": xml_string})
            else:
                with get_engine(DB_JTL).connect() as conn:
                    conn.execute(text("""
                        INSERT INTO [dbo].[tXMLBestellImport] (cText, nPlattform, nRechnung)
                        VALUES (:xml_string, 5, 0)
                    """), {"xml_string": xml_string})
                    conn.commit()
            return True
        except Exception as e:
            app_logger.error(f"JTL insert_xml_import: {e}", exc_info=True)
            return False
    
    def get_imported_orders(self) -> Dict[str, bool]:
        """Hole Orders die schon importiert wurden"""
        try:
            conn = self._get_conn()
            result = conn.execute(text("""
                SELECT DISTINCT [cBestellungInetBestellNr]
                FROM [dbo].[tXMLBestellImport]
                WHERE nPlattform = 5
                AND [cBestellungInetBestellNr] IS NOT NULL
            """))
            return {row[0]: True for row in result.all()}
        except Exception as e:
            app_logger.error(f"JTL get_imported_orders: {e}", exc_info=True)
            return {}
    
    def get_xml_import_status(self, bestell_id: str) -> Optional[str]:
        """Hole Import Status für eine Bestellung"""
        try:
            conn = self._get_conn()
            result = conn.execute(text("""
                SELECT TOP 1 [dErstellt], [dZugelesen]
                FROM [dbo].[tXMLBestellImport]
                WHERE [cBestellungInetBestellNr] = :bestell_id
                ORDER BY [kXMLBestellImport] DESC
            """), {"bestell_id": bestell_id})
            row = result.first()
            
            if not row:
                return 'pending'
            
            _, zugelesen = row
            return 'imported' if zugelesen else 'processing'
        except Exception as e:
            app_logger.error(f"JTL get_xml_import_status: {e}", exc_info=True)
            return None
    
    def get_import_errors(self, bestell_id: str = None) -> Dict[str, str]:
        """Hole Import Fehler aus JTL"""
        try:
            conn = self._get_conn()
            
            if bestell_id:
                result = conn.execute(text("""
                    SELECT [cBestellungInetBestellNr], [cFehlerText]
                    FROM [dbo].[tXMLBestellImport]
                    WHERE nPlattform = 5
                    AND [cBestellungInetBestellNr] = :bestell_id
                    AND [cFehlerText] IS NOT NULL
                    AND [cFehlerText] != ''
                """), {"bestell_id": bestell_id})
            else:
                result = conn.execute(text("""
                    SELECT [cBestellungInetBestellNr], [cFehlerText]
                    FROM [dbo].[tXMLBestellImport]
                    WHERE nPlattform = 5
                    AND [cFehlerText] IS NOT NULL
                    AND [cFehlerText] != ''
                """))
            
            return {row[0]: row[1] for row in result.all()}
        except Exception as e:
            app_logger.error(f"JTL get_import_errors: {e}", exc_info=True)
            return {}
    
    def get_article_id_by_sku(self, sku: str) -> Optional[int]:
        """Hole JTL Artikel-ID per SKU"""
        try:
            conn = self._get_conn()
            result = conn.execute(text("""
                SELECT TOP 1 [kArtikel]
                FROM [dbo].[tArtikel]
                WHERE [cArtikelnummer] = :sku
            """), {"sku": sku})
            row = result.first()
            return int(row[0]) if row else None
        except Exception as e:
            app_logger.error(f"JTL get_article_id_by_sku: {e}", exc_info=True)
            return None
    
    def get_stock_by_article_id(self, article_id: int) -> int:
        """Hole Bestand aus JTL pro Artikel-ID"""
        try:
            conn = self._get_conn()
            result = conn.execute(text("""
                SELECT TOP 1 [fLagerbestand]
                FROM [dbo].[tArtikelLagerbestand]
                WHERE [kArtikel] = :article_id
            """), {"article_id": article_id})
            row = result.first()
            return int(row[0]) if row else 0
        except Exception as e:
            app_logger.error(f"JTL get_stock_by_article_id: {e}", exc_info=True)
            return 0
    
    def get_tracking_from_lieferschein(self, bestell_id: str) -> Optional[Dict]:
        """Hole Tracking aus JTL Lieferscheindaten"""
        try:
            conn = self._get_conn()
            result = conn.execute(text("""
                SELECT TOP 1 [cTracking], [cVersandart]
                FROM [dbo].[tVersand]
                WHERE [cBestellungInetBestellNr] = :bestell_id
                AND [cTracking] IS NOT NULL
                AND [cTracking] != ''
            """), {"bestell_id": bestell_id})
            row = result.first()
            
            if not row:
                return None
            
            return {
                "tracking_number": row[0],
                "carrier": row[1]
            }
        except Exception as e:
            app_logger.error(f"JTL get_tracking_from_lieferschein: {e}", exc_info=True)
            return None
