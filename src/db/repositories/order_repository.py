"""Order Repository - Data Access Layer"""

from typing import List, Optional
from datetime import datetime
from db.connection import get_db_connection
from config.settings import TABLE_ORDERS, DB_TOCI

class Order:
    """Order Domain Model"""
    def __init__(self, id=None, bestell_id=None, bestellstatus=None, kaufdatum=None,
                 vorname_empfaenger=None, nachname_empfaenger=None, strasse=None,
                 plz=None, ort=None, bundesland=None, land=None, land_iso=None,
                 email=None, telefon_empfaenger=None, versandkosten=None,
                 trackingnummer=None, versanddienstleister=None,
                 status=None, temu_gemeldet=0):
        self.id = id
        self.bestell_id = bestell_id
        self.bestellstatus = bestellstatus
        self.kaufdatum = kaufdatum
        self.vorname_empfaenger = vorname_empfaenger
        self.nachname_empfaenger = nachname_empfaenger
        self.strasse = strasse
        self.plz = plz
        self.ort = ort
        self.bundesland = bundesland
        self.land = land
        self.land_iso = land_iso
        self.email = email
        self.telefon_empfaenger = telefon_empfaenger
        self.versandkosten = versandkosten
        self.trackingnummer = trackingnummer
        self.versanddienstleister = versanddienstleister
        self.status = status
        self.temu_gemeldet = temu_gemeldet

class OrderRepository:
    """Repository für Order-Operationen"""
    
    def __init__(self, db_name=DB_TOCI):
        self.db_name = db_name
    
    def find_by_bestell_id(self, bestell_id: str) -> Optional[Order]:
        """Hole einzelne Order nach bestell_id"""
        conn = get_db_connection(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT id, bestell_id, bestellstatus, kaufdatum,
                   vorname_empfaenger, nachname_empfaenger, strasse,
                   plz, ort, bundesland, land, land_iso,
                   email, telefon_empfaenger, versandkosten,
                   trackingnummer, versanddienstleister, status, temu_gemeldet
            FROM {TABLE_ORDERS}
            WHERE bestell_id = ?
        """, bestell_id)
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not row:
            return None
        
        return self._map_to_order(row)
    
    def find_by_status(self, status: str) -> List[Order]:
        """Hole alle Orders mit bestimmtem Status"""
        conn = get_db_connection(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT id, bestell_id, bestellstatus, kaufdatum,
                   vorname_empfaenger, nachname_empfaenger, strasse,
                   plz, ort, bundesland, land, land_iso,
                   email, telefon_empfaenger, versandkosten,
                   trackingnummer, versanddienstleister, status, temu_gemeldet
            FROM {TABLE_ORDERS}
            WHERE status = ?
        """, status)
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [self._map_to_order(row) for row in rows]
    
    def find_for_tracking_export(self) -> List[Order]:
        """Hole Orders mit Tracking, die noch nicht zu TEMU exportiert wurden"""
        conn = get_db_connection(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT id, bestell_id, bestellstatus, kaufdatum,
                   vorname_empfaenger, nachname_empfaenger, strasse,
                   plz, ort, bundesland, land, land_iso,
                   email, telefon_empfaenger, versandkosten,
                   trackingnummer, versanddienstleister, status, temu_gemeldet
            FROM {TABLE_ORDERS}
            WHERE trackingnummer IS NOT NULL 
              AND trackingnummer != ''
              AND temu_gemeldet = 0
              AND status = 'versendet'
        """)
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [self._map_to_order(row) for row in rows]
    
    def save(self, order: Order) -> int:
        """INSERT oder UPDATE Order"""
        conn = get_db_connection(self.db_name)
        cursor = conn.cursor()
        
        if order.id:
            # UPDATE
            cursor.execute(f"""
                UPDATE {TABLE_ORDERS}
                SET bestellstatus = ?, kaufdatum = ?,
                    vorname_empfaenger = ?, nachname_empfaenger = ?,
                    strasse = ?, plz = ?, ort = ?, bundesland = ?,
                    land = ?, land_iso = ?, email = ?, telefon_empfaenger = ?,
                    versandkosten = ?, status = ?, updated_at = GETDATE()
                WHERE id = ?
            """, order.bestellstatus, order.kaufdatum,
                order.vorname_empfaenger, order.nachname_empfaenger,
                order.strasse, order.plz, order.ort, order.bundesland,
                order.land, order.land_iso, order.email, order.telefon_empfaenger,
                order.versandkosten, order.status, order.id)
            result = order.id
        else:
            # INSERT
            cursor.execute(f"""
                INSERT INTO {TABLE_ORDERS} (
                    bestell_id, bestellstatus, kaufdatum,
                    vorname_empfaenger, nachname_empfaenger,
                    strasse, plz, ort, bundesland, land, land_iso,
                    email, telefon_empfaenger, versandkosten, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, order.bestell_id, order.bestellstatus, order.kaufdatum,
                order.vorname_empfaenger, order.nachname_empfaenger,
                order.strasse, order.plz, order.ort, order.bundesland,
                order.land, order.land_iso, order.email, order.telefon_empfaenger,
                order.versandkosten, order.status)
            
            cursor.execute("SELECT @@IDENTITY")
            result = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return result
    
    def mark_exported(self, order_id: int) -> bool:
        """Markiere Order als zu TEMU exportiert"""
        conn = get_db_connection(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            UPDATE {TABLE_ORDERS}
            SET temu_gemeldet = 1, updated_at = GETDATE()
            WHERE id = ?
        """, order_id)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
    
    def update_tracking(self, order_id: int, trackingnummer: str, 
                       versanddienstleister: str) -> bool:
        """Update Tracking-Daten"""
        conn = get_db_connection(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            UPDATE {TABLE_ORDERS}
            SET trackingnummer = ?, versanddienstleister = ?,
                versanddatum = GETDATE(), status = 'versendet',
                updated_at = GETDATE()
            WHERE id = ?
        """, trackingnummer, versanddienstleister, order_id)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
    
    def _map_to_order(self, row) -> Order:
        """Konvertiere DB-Row zu Order-Objekt"""
        return Order(
            id=row[0],
            bestell_id=row[1],
            bestellstatus=row[2],
            kaufdatum=row[3],
            vorname_empfaenger=row[4],
            nachname_empfaenger=row[5],
            strasse=row[6],
            plz=row[7],
            ort=row[8],
            bundesland=row[9],
            land=row[10],
            land_iso=row[11],
            email=row[12],
            telefon_empfaenger=row[13],
            versandkosten=row[14],
            trackingnummer=row[15],
            versanddienstleister=row[16],
            status=row[17],
            temu_gemeldet=row[18]
        )
