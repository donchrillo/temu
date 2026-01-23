"""Order Repository - SQLAlchemy + Raw SQL (FIXED)"""

from typing import Optional, List, Dict
from sqlalchemy import text
from sqlalchemy.engine import Connection
from src.services.logger import app_logger
from src.db.connection import get_engine
from config.settings import TABLE_ORDERS, TABLE_ORDER_ITEMS, DB_TOCI

class Order:
    """Domain Model für Order"""
    def __init__(self, id=None, bestell_id=None, bestellstatus=None, 
                 kaufdatum=None, vorname_empfaenger=None, nachname_empfaenger=None,
                 strasse=None, adresszusatz=None, plz=None, ort=None, bundesland=None, land=None,
                 land_iso=None, email=None, telefon_empfaenger=None, 
                 versandkosten=None, status=None, xml_erstellt=False,
                 trackingnummer=None, versanddienstleister=None, versanddatum=None):
        self.id = id
        self.bestell_id = bestell_id
        self.bestellstatus = bestellstatus
        self.kaufdatum = kaufdatum
        self.vorname_empfaenger = vorname_empfaenger
        self.nachname_empfaenger = nachname_empfaenger
        self.strasse = strasse
        self.adresszusatz = adresszusatz
        self.plz = plz
        self.ort = ort
        self.bundesland = bundesland
        self.land = land
        self.land_iso = land_iso
        self.email = email
        self.telefon_empfaenger = telefon_empfaenger
        self.versandkosten = versandkosten
        self.status = status
        self.xml_erstellt = xml_erstellt
        self.trackingnummer = trackingnummer
        self.versanddienstleister = versanddienstleister
        self.versanddatum = versanddatum

class OrderRepository:
    """Data Access Layer - ONLY DB Operations"""
    
    def __init__(self, connection: Optional[Connection] = None):
        """
        Injektierte Connection (aus db_connect ContextManager).
        Falls None → Repo holt sich selbst temporäre Connection + Commit.
        """
        self._conn = connection
    
    def find_by_bestell_id(self, bestell_id: str) -> Optional[Order]:
        """Hole Order aus DB"""
        try:
            if self._conn:
                result = self._conn.execute(text(f"""
                    SELECT id, bestell_id, bestellstatus, kaufdatum,
                           vorname_empfaenger, nachname_empfaenger,
                           strasse, adresszusatz, plz, ort, bundesland, land, land_iso,
                           email, telefon_empfaenger, versandkosten, status, xml_erstellt,
                           trackingnummer, versanddienstleister, versanddatum
                    FROM {TABLE_ORDERS}
                    WHERE bestell_id = :bestell_id
                """), {"bestell_id": bestell_id})
                row = result.first()
            else:
                # Standalone: brauchen keine Commit für SELECT, aber mit Statement
                with get_engine(DB_TOCI).connect() as conn:
                    result = conn.execute(text(f"""
                        SELECT id, bestell_id, bestellstatus, kaufdatum,
                               vorname_empfaenger, nachname_empfaenger,
                               strasse, adresszusatz, plz, ort, bundesland, land, land_iso,
                               email, telefon_empfaenger, versandkosten, status, xml_erstellt,
                               trackingnummer, versanddienstleister, versanddatum
                        FROM {TABLE_ORDERS}
                        WHERE bestell_id = :bestell_id
                    """), {"bestell_id": bestell_id})
                    row = result.first()
            
            return self._map_to_order(row) if row else None
        except Exception as e:
            app_logger.error(f"OrderRepository find_by_bestell_id: {e}", exc_info=True)
            return None
    
    def save(self, order: Order) -> int:
        """INSERT oder UPDATE Order - mit automatischem Commit bei Standalone"""
        try:
            if order.id:
                # UPDATE
                sql = f"""
                    UPDATE {TABLE_ORDERS} SET
                        bestellstatus = :bestellstatus,
                        kaufdatum = :kaufdatum,
                        vorname_empfaenger = :vorname_empfaenger,
                        nachname_empfaenger = :nachname_empfaenger,
                        strasse = :strasse,
                        plz = :plz,
                        ort = :ort,
                        bundesland = :bundesland,
                        land = :land,
                        land_iso = :land_iso,
                        email = :email,
                        telefon_empfaenger = :telefon_empfaenger,
                        versandkosten = :versandkosten,
                        status = :status,
                        updated_at = GETDATE()
                    WHERE id = :id
                """
                params = {
                    "bestellstatus": order.bestellstatus,
                    "kaufdatum": order.kaufdatum,
                    "vorname_empfaenger": order.vorname_empfaenger,
                    "nachname_empfaenger": order.nachname_empfaenger,
                    "strasse": order.strasse,
                    "plz": order.plz,
                    "ort": order.ort,
                    "bundesland": order.bundesland,
                    "land": order.land,
                    "land_iso": order.land_iso,
                    "email": order.email,
                    "telefon_empfaenger": order.telefon_empfaenger,
                    "versandkosten": order.versandkosten,
                    "status": order.status,
                    "id": order.id
                }
                
                if self._conn:
                    # Injizierte Connection: Service macht Commit
                    self._conn.execute(text(sql), params)
                else:
                    # Standalone: Wir machen Commit
                    with get_engine(DB_TOCI).connect() as conn:
                        conn.execute(text(sql), params)
                        conn.commit()
                
                return order.id
            else:
                # INSERT - brauchen @@IDENTITY zurück
                sql = f"""
                    INSERT INTO {TABLE_ORDERS} (
                        bestell_id, bestellstatus, kaufdatum,
                        vorname_empfaenger, nachname_empfaenger,
                        strasse, plz, ort, bundesland, land, land_iso,
                        email, telefon_empfaenger, versandkosten, status,
                        created_at, updated_at
                    ) VALUES (
                        :bestell_id, :bestellstatus, :kaufdatum,
                        :vorname_empfaenger, :nachname_empfaenger,
                        :strasse, :plz, :ort, :bundesland, :land, :land_iso,
                        :email, :telefon_empfaenger, :versandkosten, :status,
                        GETDATE(), GETDATE()
                    );
                    SELECT @@IDENTITY AS new_id;
                """
                params = {
                    "bestell_id": order.bestell_id,
                    "bestellstatus": order.bestellstatus,
                    "kaufdatum": order.kaufdatum,
                    "vorname_empfaenger": order.vorname_empfaenger,
                    "nachname_empfaenger": order.nachname_empfaenger,
                    "strasse": order.strasse,
                    "plz": order.plz,
                    "ort": order.ort,
                    "bundesland": order.bundesland,
                    "land": order.land,
                    "land_iso": order.land_iso,
                    "email": order.email,
                    "telefon_empfaenger": order.telefon_empfaenger,
                    "versandkosten": order.versandkosten,
                    "status": order.status
                }
                
                if self._conn:
                    result = self._conn.execute(text(sql), params)
                    row = result.first()
                    return int(row[0]) if row else 0
                else:
                    with get_engine(DB_TOCI).connect() as conn:
                        result = conn.execute(text(sql), params)
                        row = result.first()
                        conn.commit()  # Commit NACH Fetch, vor Return
                        return int(row[0]) if row else 0
        
        except Exception as e:
            app_logger.error(f"OrderRepository save: {e}", exc_info=True)
            return 0
    
    def find_by_status(self, status: str) -> List[Order]:
        """Hole alle Orders mit bestimmtem Status"""
        try:
            if self._conn:
                result = self._conn.execute(text(f"""
                    SELECT id, bestell_id, bestellstatus, kaufdatum,
                           vorname_empfaenger, nachname_empfaenger,
                           strasse, adresszusatz, plz, ort, bundesland, land, land_iso,
                           email, telefon_empfaenger, versandkosten, status, xml_erstellt,
                           trackingnummer, versanddienstleister, versanddatum
                    FROM {TABLE_ORDERS}
                    WHERE status = :status
                    ORDER BY created_at DESC
                """), {"status": status})
                return [self._map_to_order(row) for row in result.all()]
            else:
                with get_engine(DB_TOCI).connect() as conn:
                    result = conn.execute(text(f"""
                        SELECT id, bestell_id, bestellstatus, kaufdatum,
                               vorname_empfaenger, nachname_empfaenger,
                               strasse, adresszusatz, plz, ort, bundesland, land, land_iso,
                               email, telefon_empfaenger, versandkosten, status, xml_erstellt,
                               trackingnummer, versanddienstleister, versanddatum
                        FROM {TABLE_ORDERS}
                        WHERE status = :status
                        ORDER BY created_at DESC
                    """), {"status": status})
                    return [self._map_to_order(row) for row in result.all()]
        except Exception as e:
            app_logger.error(f"OrderRepository find_by_status: {e}", exc_info=True)
            return []
    
    def update_order_tracking(self, order_id: int, tracking_number: str, 
                              versanddienstleister: str, status: str) -> bool:
        """Update Tracking-Daten in Order"""
        try:
            sql = f"""
                UPDATE {TABLE_ORDERS} SET
                    trackingnummer = :tracking_number,
                    versanddienstleister = :versanddienstleister,
                    versanddatum = GETDATE(),
                    status = :status,
                    updated_at = GETDATE()
                WHERE id = :order_id
            """
            params = {
                "tracking_number": tracking_number,
                "versanddienstleister": versanddienstleister,
                "status": status,
                "order_id": order_id
            }
            
            if self._conn:
                self._conn.execute(text(sql), params)
            else:
                with get_engine(DB_TOCI).connect() as conn:
                    conn.execute(text(sql), params)
                    conn.commit()
            
            return True
        except Exception as e:
            app_logger.error(f"OrderRepository update_order_tracking: {e}", exc_info=True)
            return False
    
    def get_orders_for_tracking_export(self) -> List[Dict]:
        """Hole Orders mit Tracking für TEMU Export"""
        try:
            if self._conn:
                conn = self._conn
                close_conn = False
            else:
                conn = get_engine(DB_TOCI).connect()
                close_conn = True
            
            try:
                result = conn.execute(text(f"""
                    SELECT id, bestell_id, trackingnummer, versanddienstleister
                    FROM {TABLE_ORDERS}
                    WHERE status = 'versendet'
                      AND trackingnummer IS NOT NULL
                      AND trackingnummer != ''
                      AND temu_gemeldet = 0
                    ORDER BY versanddatum DESC
                """))
                
                result_list = []
                for row in result.all():
                    order_id, bestell_id, tracking_number, carrier = row
                    
                    items_result = conn.execute(text(f"""
                        SELECT bestellartikel_id, menge
                        FROM {TABLE_ORDER_ITEMS}
                        WHERE order_id = :order_id
                    """), {"order_id": order_id})
                    
                    items = [
                        {
                            "bestellartikel_id": item[0],
                            "menge": int(item[1])
                        }
                        for item in items_result.all()
                    ]
                    
                    result_list.append({
                        "order_id": order_id,
                        "bestell_id": bestell_id,
                        "trackingnummer": tracking_number,
                        "versanddienstleister": carrier,
                        "items": items
                    })
                
                return result_list
            finally:
                if close_conn:
                    conn.close()
        
        except Exception as e:
            app_logger.error(f"OrderRepository get_orders_for_tracking_export: {e}", exc_info=True)
            return []
    
    def update_temu_tracking_status(self, order_id: int) -> bool:
        """Markiere Order als zu TEMU gemeldet"""
        try:
            sql = f"""
                UPDATE {TABLE_ORDERS} SET
                    temu_gemeldet = 1,
                    updated_at = GETDATE()
                WHERE id = :order_id
            """
            params = {"order_id": order_id}
            
            if self._conn:
                self._conn.execute(text(sql), params)
            else:
                with get_engine(DB_TOCI).connect() as conn:
                    conn.execute(text(sql), params)
                    conn.commit()
            
            return True
        except Exception as e:
            app_logger.error(f"OrderRepository update_temu_tracking_status: {e}", exc_info=True)
            return False

    def update_xml_export_status(self, order_id: int) -> bool:
        """Setze xml_erstellt = 1"""
        try:
            sql = f"""
                UPDATE {TABLE_ORDERS} SET
                    xml_erstellt = 1,
                    status = 'xml_erstellt',
                    updated_at = GETDATE()
                WHERE id = :order_id
            """
            params = {"order_id": order_id}
            
            if self._conn:
                self._conn.execute(text(sql), params)
            else:
                with get_engine(DB_TOCI).connect() as conn:
                    conn.execute(text(sql), params)
                    conn.commit()
            
            return True
        except Exception as e:
            app_logger.error(f"OrderRepository update_xml_export_status: {e}", exc_info=True)
            return False

    def find_orders_for_tracking(self) -> List[Order]:
        """Hole Orders für Tracking-Abgleich"""
        try:
            if self._conn:
                result = self._conn.execute(text(f"""
                    SELECT id, bestell_id, bestellstatus, kaufdatum,
                           vorname_empfaenger, nachname_empfaenger,
                           strasse, adresszusatz, plz, ort, bundesland, land, land_iso,
                           email, telefon_empfaenger, versandkosten, status, xml_erstellt,
                           trackingnummer, versanddienstleister, versanddatum
                    FROM {TABLE_ORDERS}
                    WHERE xml_erstellt = 1
                      AND (trackingnummer IS NULL OR trackingnummer = '')
                    ORDER BY created_at DESC
                """))
                return [self._map_to_order(row) for row in result.all()]
            else:
                with get_engine(DB_TOCI).connect() as conn:
                    result = conn.execute(text(f"""
                        SELECT id, bestell_id, bestellstatus, kaufdatum,
                               vorname_empfaenger, nachname_empfaenger,
                               strasse, adresszusatz, plz, ort, bundesland, land, land_iso,
                               email, telefon_empfaenger, versandkosten, status, xml_erstellt,
                               trackingnummer, versanddienstleister, versanddatum
                        FROM {TABLE_ORDERS}
                        WHERE xml_erstellt = 1
                          AND (trackingnummer IS NULL OR trackingnummer = '')
                        ORDER BY created_at DESC
                    """))
                    return [self._map_to_order(row) for row in result.all()]
        except Exception as e:
            app_logger.error(f"OrderRepository find_orders_for_tracking: {e}", exc_info=True)
            return []

    def _map_to_order(self, row) -> Order:
        """Konvertiere DB Row zu Order Object"""
        if not row:
            return None
        return Order(
            id=row[0], bestell_id=row[1], bestellstatus=row[2], kaufdatum=row[3],
            vorname_empfaenger=row[4], nachname_empfaenger=row[5],
            strasse=row[6], adresszusatz=row[7], plz=row[8], ort=row[9],
            bundesland=row[10], land=row[11], land_iso=row[12],
            email=row[13], telefon_empfaenger=row[14], versandkosten=row[15],
            status=row[16], xml_erstellt=bool(row[17]),
            trackingnummer=row[18], versanddienstleister=row[19]
        )
