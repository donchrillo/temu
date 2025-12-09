"""Order Repository - Data Access Layer für Orders"""

from typing import Optional, List, Dict
from datetime import datetime
from src.database.connection import get_db_connection
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
        self.adresszusatz = adresszusatz  # 🆕
        self.plz = plz
        self.ort = ort
        self.bundesland = bundesland
        self.land = land
        self.land_iso = land_iso
        self.email = email
        self.telefon_empfaenger = telefon_empfaenger
        self.versandkosten = versandkosten
        self.status = status
        self.xml_erstellt = xml_erstellt  # 🆕
        self.trackingnummer = trackingnummer  # 🆕
        self.versanddienstleister = versanddienstleister  # 🆕
        self.versanddatum = versanddatum  # 🆕

class OrderRepository:
    """Data Access Layer - ONLY DB Operations"""
    
    def __init__(self, connection=None):
        """Optionale Injektierte Connection (für Pooling)"""
        self._conn = connection
    
    def _get_conn(self):
        """Hole Connection (gepooled oder neu)"""
        if self._conn:
            return self._conn
        return get_db_connection(DB_TOCI)
    
    def find_by_bestell_id(self, bestell_id: str) -> Optional[Order]:
        """Hole Order aus DB"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute(f"""
                SELECT id, bestell_id, bestellstatus, kaufdatum,
                       vorname_empfaenger, nachname_empfaenger,
                       strasse, plz, ort, bundesland, land, land_iso,
                       email, telefon_empfaenger, versandkosten, status
                FROM {TABLE_ORDERS}
                WHERE bestell_id = ?
            """, bestell_id)
            row = cursor.fetchone()
            
            # ❌ NICHT conn.close() bei gepoolter Connection!
            # ✅ Connection bleibt offen für nächsten Request
            
            return self._map_to_order(row) if row else None
        except Exception as e:
            print(f"✗ DB Fehler bei find_by_bestell_id: {e}")
            return None
    
    def save(self, order: Order) -> int:
        """INSERT oder UPDATE Order"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            if order.id:
                # UPDATE
                cursor.execute(f"""
                    UPDATE {TABLE_ORDERS} SET
                        bestellstatus = ?,
                        kaufdatum = ?,
                        vorname_empfaenger = ?,
                        nachname_empfaenger = ?,
                        strasse = ?,
                        plz = ?,
                        ort = ?,
                        bundesland = ?,
                        land = ?,
                        land_iso = ?,
                        email = ?,
                        telefon_empfaenger = ?,
                        versandkosten = ?,
                        status = ?,
                        updated_at = GETDATE()
                    WHERE id = ?
                """, order.bestellstatus, order.kaufdatum,
                    order.vorname_empfaenger, order.nachname_empfaenger,
                    order.strasse, order.plz, order.ort, order.bundesland,
                    order.land, order.land_iso, order.email,
                    order.telefon_empfaenger, order.versandkosten,
                    order.status, order.id)
                
                # ❌ NICHT conn.commit() bei gepoolter Connection!
                # ✅ AutoCommit ist schon aktiv
                return order.id
            else:
                # INSERT
                cursor.execute(f"""
                    INSERT INTO {TABLE_ORDERS} (
                        bestell_id, bestellstatus, kaufdatum,
                        vorname_empfaenger, nachname_empfaenger,
                        strasse, plz, ort, bundesland, land, land_iso,
                        email, telefon_empfaenger, versandkosten, status,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
                """, order.bestell_id, order.bestellstatus, order.kaufdatum,
                    order.vorname_empfaenger, order.nachname_empfaenger,
                    order.strasse, order.plz, order.ort, order.bundesland,
                    order.land, order.land_iso, order.email,
                    order.telefon_empfaenger, order.versandkosten, order.status)
                
                cursor.execute("SELECT @@IDENTITY")
                new_id = cursor.fetchone()[0]
                
                # ❌ NICHT conn.commit() bei gepoolter Connection!
                # ✅ AutoCommit ist schon aktiv
                return int(new_id)
        
        except Exception as e:
            print(f"✗ DB Fehler bei save: {e}")
            return 0
    
    def find_by_status(self, status: str) -> List[Order]:
        """Hole alle Orders mit bestimmtem Status"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute(f"""
                SELECT id, bestell_id, bestellstatus, kaufdatum,
                       vorname_empfaenger, nachname_empfaenger,
                       strasse, adresszusatz, plz, ort, bundesland, land, land_iso,
                       email, telefon_empfaenger, versandkosten, status, xml_erstellt,
                       trackingnummer, versanddienstleister
                FROM {TABLE_ORDERS}
                WHERE status = ?
                ORDER BY created_at DESC
            """, status)
            
            rows = cursor.fetchall()
            
            return [self._map_to_order(row) for row in rows]
        
        except Exception as e:
            print(f"✗ DB Fehler bei find_by_status: {e}")
            return []
    
    def update_order_tracking(self, order_id: int, tracking_number: str, 
                              versanddienstleister: str, status: str) -> bool:
        """Update Tracking-Daten in Order"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute(f"""
                UPDATE {TABLE_ORDERS} SET
                    trackingnummer = ?,
                    versanddienstleister = ?,
                    versanddatum = GETDATE(),
                    status = ?,
                    updated_at = GETDATE()
                WHERE id = ?
            """, tracking_number, versanddienstleister, status, order_id)
            
            return True
        
        except Exception as e:
            print(f"✗ DB Fehler bei update_order_tracking: {e}")
            return False
    
    def get_orders_for_tracking_export(self) -> List[Dict]:
        """
        Hole Orders mit Tracking die noch nicht zu TEMU gemeldet wurden
        
        Returns für jeden Order alle Items mit Tracking:
        [
            {
                'order_id': 1,
                'bestell_id': 'PO-076-...',
                'trackingnummer': 'DHL123456',
                'versanddienstleister': 'DHL',
                'items': [
                    {'bestellartikel_id': 'SO-001', 'menge': 2},
                    {'bestellartikel_id': 'SO-002', 'menge': 1}
                ]
            }
        ]
        """
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Hole Orders mit Tracking
            cursor.execute(f"""
                SELECT id, bestell_id, trackingnummer, versanddienstleister
                FROM {TABLE_ORDERS}
                WHERE status = 'versendet'
                  AND trackingnummer IS NOT NULL
                  AND trackingnummer != ''
                  AND temu_gemeldet = 0
                ORDER BY versanddatum DESC
            """)
            
            orders = cursor.fetchall()
            result = []
            
            for order in orders:
                order_id, bestell_id, tracking_number, carrier = order
                
                # Hole Items für diese Order
                cursor.execute(f"""
                    SELECT bestellartikel_id, menge
                    FROM {TABLE_ORDER_ITEMS}
                    WHERE order_id = ?
                """, order_id)
                
                items = cursor.fetchall()
                
                result.append({
                    'order_id': order_id,
                    'bestell_id': bestell_id,
                    'trackingnummer': tracking_number,
                    'versanddienstleister': carrier,
                    'items': [
                        {
                            'bestellartikel_id': item[0],
                            'menge': int(item[1])
                        }
                        for item in items
                    ]
                })
            
            return result
        
        except Exception as e:
            print(f"✗ DB Fehler bei get_orders_for_tracking_export: {e}")
            return []
    
    def update_temu_tracking_status(self, order_id: int) -> bool:
        """
        Markiere Order als zu TEMU gemeldet (nach erfolgreichem Upload)
        
        Args:
            order_id: Order DB ID
        
        Returns:
            bool: True wenn erfolgreich
        """
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute(f"""
                UPDATE {TABLE_ORDERS} SET
                    temu_gemeldet = 1,
                    updated_at = GETDATE()
                WHERE id = ?
            """, order_id)
            
            return True
        
        except Exception as e:
            print(f"✗ DB Fehler bei update_temu_tracking_status: {e}")
            return False

    def update_xml_export_status(self, order_id: int) -> bool:
        """
        Setze xml_erstellt = 1 und status = 'xml_erstellt'
        NACH erfolgreichem XML Export
        
        Args:
            order_id: Order DB ID
        
        Returns:
            bool: True wenn erfolgreich
        """
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute(f"""
                UPDATE {TABLE_ORDERS} SET
                    xml_erstellt = 1,
                    status = 'xml_erstellt',
                    updated_at = GETDATE()
                WHERE id = ?
            """, order_id)
            
            return True
        
        except Exception as e:
            print(f"✗ DB Fehler bei update_xml_export_status: {e}")
            return False

    def find_orders_for_tracking(self) -> List[Order]:
        """
        Hole Orders die TRACKING benötigen
        
        Query:
        - xml_erstellt = 1 (XML wurde exportiert)
        - trackingnummer IS NULL ODER = '' (Kein Tracking)
        - Status ist EGAL!
        
        Returns:
            List[Order]
        """
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute(f"""
                SELECT id, bestell_id, bestellstatus, kaufdatum,
                       vorname_empfaenger, nachname_empfaenger,
                       strasse, adresszusatz, plz, ort, bundesland, land, land_iso,
                       email, telefon_empfaenger, versandkosten, status, xml_erstellt,
                       trackingnummer, versanddienstleister, versanddatum
                FROM {TABLE_ORDERS}
                WHERE xml_erstellt = 1
                  AND (trackingnummer IS NULL OR trackingnummer = '')
                ORDER BY created_at DESC
            """)
            
            rows = cursor.fetchall()
            
            return [self._map_to_order(row) for row in rows]
        
        except Exception as e:
            print(f"✗ DB Fehler bei find_orders_for_tracking: {e}")
            return []

    def _map_to_order(self, row) -> Order:
        """Konvertiere DB Row zu Order Object"""
        if not row:
            return None
        
        return Order(
            id=row[0],
            bestell_id=row[1],
            bestellstatus=row[2],
            kaufdatum=row[3],
            vorname_empfaenger=row[4],
            nachname_empfaenger=row[5],
            strasse=row[6],
            adresszusatz=row[7],  # 🆕
            plz=row[8],
            ort=row[9],
            bundesland=row[10],
            land=row[11],
            land_iso=row[12],
            email=row[13],
            telefon_empfaenger=row[14],
            versandkosten=row[15],
            status=row[16],
            xml_erstellt=bool(row[17]) if len(row) > 17 else False,
            trackingnummer=row[18] if len(row) > 18 else None,  # 🆕
            versanddienstleister=row[19] if len(row) > 19 else None,  # 🆕
            versanddatum=row[20] if len(row) > 20 else None  # 🆕
        )
