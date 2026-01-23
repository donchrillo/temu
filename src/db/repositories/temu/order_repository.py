"""Order Repository - SQLAlchemy + Raw SQL"""

from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy import text
from src.services.logger import app_logger
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
    
    def __init__(self, connection=None):
        """Optionale Injektierte Connection (für Pooling)"""
        self._conn = connection
    
    def _get_conn(self):
        """Hole Connection"""
        if self._conn:
            return self._conn
        from src.db.connection import get_db_connection
        return get_db_connection(DB_TOCI)
    
    def find_by_bestell_id(self, bestell_id: str) -> Optional[Order]:
        """Hole Order aus DB"""
        try:
            conn = self._get_conn()
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
        """INSERT oder UPDATE Order"""
        try:
            conn = self._get_conn()
            
            if order.id:
                # UPDATE
                conn.execute(text(f"""
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
                """), {
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
                })
                return order.id
            else:
                # INSERT
                result = conn.execute(text(f"""
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
                """), {
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
                })
                new_id_row = result.first()
                return int(new_id_row[0]) if new_id_row else 0
        except Exception as e:
            app_logger.error(f"OrderRepository save: {e}", exc_info=True)
            return 0
    
    def find_by_status(self, status: str) -> List[Order]:
        """Hole alle Orders mit bestimmtem Status"""
        try:
            conn = self._get_conn()
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
            conn = self._get_conn()
            conn.execute(text(f"""
                UPDATE {TABLE_ORDERS} SET
                    trackingnummer = :tracking_number,
                    versanddienstleister = :versanddienstleister,
                    versanddatum = GETDATE(),
                    status = :status,
                    updated_at = GETDATE()
                WHERE id = :order_id
            """), {
                "tracking_number": tracking_number,
                "versanddienstleister": versanddienstleister,
                "status": status,
                "order_id": order_id
            })
            return True
        except Exception as e:
            app_logger.error(f"OrderRepository update_order_tracking: {e}", exc_info=True)
            return False
    
    def get_orders_for_tracking_export(self) -> List[Dict]:
        """Hole Orders mit Tracking für TEMU Export"""
        try:
            conn = self._get_conn()
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
                
                # Hole Items für diese Order
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
        except Exception as e:
            app_logger.error(f"OrderRepository get_orders_for_tracking_export: {e}", exc_info=True)
            return []
    
    def update_temu_tracking_status(self, order_id: int) -> bool:
        """Markiere Order als zu TEMU gemeldet"""
        try:
            conn = self._get_conn()
            conn.execute(text(f"""
                UPDATE {TABLE_ORDERS} SET
                    temu_gemeldet = 1,
                    updated_at = GETDATE()
                WHERE id = :order_id
            """), {"order_id": order_id})
            return True
        except Exception as e:
            app_logger.error(f"OrderRepository update_temu_tracking_status: {e}", exc_info=True)
            return False

    def update_xml_export_status(self, order_id: int) -> bool:
        """Setze xml_erstellt = 1"""
        try:
            conn = self._get_conn()
            conn.execute(text(f"""
                UPDATE {TABLE_ORDERS} SET
                    xml_erstellt = 1,
                    status = 'xml_erstellt',
                    updated_at = GETDATE()
                WHERE id = :order_id
            """), {"order_id": order_id})
            return True
        except Exception as e:
            app_logger.error(f"OrderRepository update_xml_export_status: {e}", exc_info=True)
            return False

    def find_orders_for_tracking(self) -> List[Order]:
        """Hole Orders für Tracking-Abgleich"""
        try:
            conn = self._get_conn()
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
