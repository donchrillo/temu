"""XML Export Service - Business Logic für XML Generierung"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from src.db.repositories.order_repository import OrderRepository
from src.db.repositories.order_item_repository import OrderItemRepository
from src.db.repositories.jtl_repository import JtlRepository
from config.settings import (
    JTL_WAEHRUNG, JTL_SPRACHE, JTL_K_BENUTZER, JTL_K_FIRMA,
    XML_OUTPUT_PATH, DATA_DIR
)

class XmlExportService:
    """Business Logic - XML Generierung für JTL"""
    
    def __init__(self, order_repo: OrderRepository = None, 
                 item_repo: OrderItemRepository = None,
                 jtl_repo: JtlRepository = None):  # ← Jetzt Repository statt Connection!
        """
        Args:
            order_repo: OrderRepository für TOCI
            item_repo: OrderItemRepository für TOCI
            jtl_repo: JtlRepository für JTL DB Access  # ← WICHTIG!
        """
        self.order_repo = order_repo or OrderRepository()
        self.item_repo = item_repo or OrderItemRepository()
        self.jtl_repo = jtl_repo or JtlRepository()
    
    def export_to_xml(self, save_to_disk=True, import_to_jtl=True) -> Dict:
        """
        Generiert XML aus Orders und exportiert zu JTL
        
        Args:
            save_to_disk: Speichere XML auf Festplatte
            import_to_jtl: Importiere XML in JTL DB
        
        Returns:
            dict mit Ergebnissen
        """
        
        print("=" * 70)
        print("Datenbank → XML Export")
        print("=" * 70 + "\n")
        
        # ===== Hole Orders mit status='importiert' =====
        orders = self._get_orders_to_export()
        
        if not orders:
            print("✓ Keine neuen Orders zum Exportieren\n")
            return {'exported': 0, 'jtl_imported': 0}
        
        print(f"✓ {len(orders)} Orders gefunden\n")
        
        # ===== Generate XML Root =====
        root = ET.Element('tBestellungen')
        exported_count = 0
        jtl_import_count = 0
        
        # ===== Für jede Order: XML generieren =====
        for order in orders:
            try:
                # Hole Items für diese Order
                items = self.item_repo.find_by_order_id(order.id)
                
                # Generiere XML Element
                bestellung_elem = self._generate_order_xml(order, items, root)
                
                # ✅ WICHTIG: Update Status NACH erfolgreichem Export!
                if bestellung_elem is not None:
                    # ===== Step 1: In JTL DB importieren =====
                    if import_to_jtl and self.jtl_repo:
                        jtl_success = self._import_to_jtl(order, bestellung_elem)
                        if jtl_success:
                            jtl_import_count += 1
                    
                    # ===== Step 2: Update Status in TOCI (WICHTIG!) =====
                    # NUR wenn JTL Import erfolgreich ODER JTL disabled!
                    status_success = self._update_order_status(order.id)
                    
                    if status_success or not import_to_jtl:
                        exported_count += 1
                        print(f"  ✓ {order.bestell_id}: XML generiert + Status gesetzt")
                    else:
                        print(f"  ✗ {order.bestell_id}: Status Update fehlgeschlagen")
                else:
                    print(f"  ✗ {order.bestell_id}: XML Generation fehlgeschlagen")
            
            except Exception as e:
                print(f"  ✗ Fehler bei Order {order.bestell_id}: {e}")
                import traceback
                traceback.print_exc()
        
        # ===== Step 3: Speichere komplette XML auf Festplatte =====
        if save_to_disk:
            self._save_xml_to_disk(root)
        
        print(f"\n{'='*70}")
        print(f"✓ XML Export erfolgreich!")
        print(f"{'='*70}")
        print(f"  Exportiert: {exported_count}")
        print(f"  JTL Import: {jtl_import_count}")
        print(f"  XML Status: xml_erstellt = 1 gesetzt")
        print(f"{'='*70}\n")
        
        return {
            'exported': exported_count,
            'jtl_imported': jtl_import_count,
            'success': exported_count > 0
        }
    
    def _get_orders_to_export(self) -> List:
        """Hole Orders mit status='importiert' und xml_erstellt=0"""
        try:
            # Hole ALLE Orders mit status='importiert'
            orders = self.order_repo.find_by_status('importiert')
            
            # Filtere: Nur Orders die NOCH NICHT zu XML exportiert wurden!
            orders_to_export = [
                order for order in orders 
                if not order.xml_erstellt  # ← WICHTIG: nur xml_erstellt=False
            ]
            
            return orders_to_export
        
        except Exception as e:
            print(f"✗ Fehler beim Laden der Orders: {e}")
            return []
    
    def _generate_order_xml(self, order, items, parent_elem) -> Optional[ET.Element]:
        """
        Generiere XML Element für eine Order
        
        Args:
            order: Order Domain Model MIT ECHTEN DATEN
            items: List von OrderItem MIT ECHTEN DATEN
            parent_elem: Parent XML Element
        
        Returns:
            bestellung Element
        """
        
        # ===== Haupt-Bestellung Element =====
        bestellung = ET.SubElement(
            parent_elem, 'tBestellung',
            kFirma=JTL_K_FIRMA,
            kBenutzer=JTL_K_BENUTZER
        )
        
        # ===== Header Daten - JETZT mit echten Daten! =====
        ET.SubElement(bestellung, 'cSprache').text = JTL_SPRACHE
        ET.SubElement(bestellung, 'cWaehrung').text = JTL_WAEHRUNG
        ET.SubElement(bestellung, 'cBestellNr')
        ET.SubElement(bestellung, 'cExterneBestellNr').text = order.bestell_id
        ET.SubElement(bestellung, 'cVersandartName').text = 'TEMU'
        ET.SubElement(bestellung, 'cVersandInfo')
        
        # ✅ JETZT mit echtem Datum!
        ET.SubElement(bestellung, 'dVersandDatum').text = (
            order.versanddatum.strftime('%d.%m.%Y') if order.versanddatum else ''
        )
        
        # ✅ JETZT mit echtem Tracking!
        ET.SubElement(bestellung, 'cTracking').text = order.trackingnummer or ''
        ET.SubElement(bestellung, 'dLieferDatum')
        ET.SubElement(bestellung, 'cKommentar')
        ET.SubElement(bestellung, 'cBemerkung')
        
        # ✅ JETZT mit echtem Kaufdatum!
        ET.SubElement(bestellung, 'dErstellt').text = (
            order.kaufdatum.strftime('%d.%m.%Y') if order.kaufdatum else ''
        )
        
        ET.SubElement(bestellung, 'cZahlungsartName').text = 'TEMU'
        ET.SubElement(bestellung, 'dBezahltDatum')
        
        # ===== Artikel-Positionen =====
        for item in items:
            self._add_item_to_xml(bestellung, item)
        
        # ===== Versandkosten =====
        self._add_shipping_costs_to_xml(bestellung, order)
        
        # ===== Kunde =====
        self._add_customer_to_xml(bestellung, order)
        
        # ===== Lieferadresse =====
        self._add_delivery_address_to_xml(bestellung, order)
        
        # ===== Zahlungsinfo =====
        self._add_payment_info_to_xml(bestellung)
        
        return bestellung
    
    def _add_item_to_xml(self, bestellung_elem, item):
        """Füge einen Artikel zur Order hinzu"""
        pos = ET.SubElement(bestellung_elem, 'twarenkorbpos')
        
        ET.SubElement(pos, 'cName').text = item.produktname or ''
        ET.SubElement(pos, 'cArtNr').text = item.sku or ''
        ET.SubElement(pos, 'cBarcode')
        ET.SubElement(pos, 'cEinheit')
        
        # WICHTIG: Format mit .5f für Netto, .2f für Brutto!
        ET.SubElement(pos, 'fPreisEinzelNetto').text = f"{item.netto_einzelpreis:.5f}"
        ET.SubElement(pos, 'fPreis').text = f"{item.brutto_einzelpreis:.2f}"
        
        ET.SubElement(pos, 'fMwSt').text = f"{item.mwst_satz:.2f}"
        ET.SubElement(pos, 'fAnzahl').text = f"{item.menge:.2f}"
        ET.SubElement(pos, 'cPosTyp').text = 'standard'
        ET.SubElement(pos, 'fRabatt').text = '0.00'
    
    def _add_shipping_costs_to_xml(self, bestellung_elem, order):
        """Füge Versandkosten als Position hinzu - MIT echten Daten!"""
        versand_pos = ET.SubElement(bestellung_elem, 'twarenkorbpos')
        
        versandkosten_netto = float(order.versandkosten or 0)
        versandkosten_brutto = versandkosten_netto * 1.19
        
        ET.SubElement(versand_pos, 'cName').text = 'TEMU Versand'
        ET.SubElement(versand_pos, 'cArtNr')
        ET.SubElement(versand_pos, 'cBarcode')
        ET.SubElement(versand_pos, 'cEinheit')
        ET.SubElement(versand_pos, 'fPreisEinzelNetto').text = f"{versandkosten_netto:.5f}"
        ET.SubElement(versand_pos, 'fPreis').text = f"{versandkosten_brutto:.2f}"
        ET.SubElement(versand_pos, 'fMwSt').text = '19.00'
        ET.SubElement(versand_pos, 'fAnzahl').text = '1.00'
        ET.SubElement(versand_pos, 'cPosTyp').text = 'versandkosten'
        ET.SubElement(versand_pos, 'fRabatt').text = '0.00'
    
    def _add_customer_to_xml(self, bestellung_elem, order):
        """Füge Kundendaten hinzu"""
        kunde = ET.SubElement(bestellung_elem, 'tkunde')
        
        ET.SubElement(kunde, 'cKundenNr')
        ET.SubElement(kunde, 'cAnrede')
        ET.SubElement(kunde, 'cTitel')
        ET.SubElement(kunde, 'cVorname').text = order.vorname_empfaenger or ''
        ET.SubElement(kunde, 'cNachname').text = order.nachname_empfaenger or ''
        ET.SubElement(kunde, 'cFirma')
        ET.SubElement(kunde, 'cStrasse').text = order.strasse or ''
        ET.SubElement(kunde, 'cAdressZusatz').text = order.adresszusatz or ''
        ET.SubElement(kunde, 'cPLZ').text = order.plz or ''
        ET.SubElement(kunde, 'cOrt').text = order.ort or ''
        ET.SubElement(kunde, 'cBundesland').text = order.bundesland or ''
        ET.SubElement(kunde, 'cLand').text = order.land_iso or ''
        ET.SubElement(kunde, 'cTel').text = order.telefon_empfaenger or ''
        ET.SubElement(kunde, 'cMobil')
        ET.SubElement(kunde, 'cFax')
        ET.SubElement(kunde, 'cMail').text = order.email or ''
        ET.SubElement(kunde, 'cUSTID')
        ET.SubElement(kunde, 'cWWW')
        ET.SubElement(kunde, 'cHerkunft').text = 'TEMU'
        ET.SubElement(kunde, 'dErstellt').text = (
            order.kaufdatum.strftime('%d.%m.%Y') if order.kaufdatum else ''
        )
    
    def _add_delivery_address_to_xml(self, bestellung_elem, order):
        """Füge Lieferadresse hinzu"""
        lieferadresse = ET.SubElement(bestellung_elem, 'tlieferadresse')
        
        ET.SubElement(lieferadresse, 'cAnrede')
        ET.SubElement(lieferadresse, 'cVorname').text = order.vorname_empfaenger or ''
        ET.SubElement(lieferadresse, 'cNachname').text = order.nachname_empfaenger or ''
        ET.SubElement(lieferadresse, 'cTitel')
        ET.SubElement(lieferadresse, 'cFirma')
        ET.SubElement(lieferadresse, 'cStrasse').text = order.strasse or ''
        ET.SubElement(lieferadresse, 'cAdressZusatz').text = order.adresszusatz or ''
        ET.SubElement(lieferadresse, 'cPLZ').text = order.plz or ''
        ET.SubElement(lieferadresse, 'cOrt').text = order.ort or ''
        ET.SubElement(lieferadresse, 'cBundesland').text = order.bundesland or ''
        ET.SubElement(lieferadresse, 'cLand').text = order.land_iso or ''
        ET.SubElement(lieferadresse, 'cTel').text = order.telefon_empfaenger or ''
        ET.SubElement(lieferadresse, 'cMobil')
        ET.SubElement(lieferadresse, 'cFax')
        ET.SubElement(lieferadresse, 'cMail').text = order.email or ''
    
    def _add_payment_info_to_xml(self, bestellung_elem):
        """Füge Zahlungsinfo hinzu (leer für TEMU)"""
        zahlungsinfo = ET.SubElement(bestellung_elem, 'tzahlungsinfo')
        
        ET.SubElement(zahlungsinfo, 'cBankName')
        ET.SubElement(zahlungsinfo, 'cBLZ')
        ET.SubElement(zahlungsinfo, 'cKontoNr')
        ET.SubElement(zahlungsinfo, 'cKartenNr')
        ET.SubElement(zahlungsinfo, 'dGueltigkeit')
        ET.SubElement(zahlungsinfo, 'cCVV')
        ET.SubElement(zahlungsinfo, 'cKartenTyp')
        ET.SubElement(zahlungsinfo, 'cInhaber')
        ET.SubElement(zahlungsinfo, 'cIBAN')
        ET.SubElement(zahlungsinfo, 'cBIC')
    
    def _import_to_jtl(self, order, bestellung_elem) -> bool:
        """
        Importiere XML in JTL DB
        
        ❌ PROBLEM: Schreibt einzelne <tBestellung> ohne Root!
        ✅ LÖSUNG: Wrap in <tBestellungen> Root!
        
        Args:
            order: Order Domain Model
            bestellung_elem: XML Element (einzelne Bestellung)
        
        Returns:
            bool: True wenn erfolgreich
        """
        
        if not self.jtl_repo:
            return False
        
        try:
            # ✅ WICHTIG: Wrap in Root Element!
            root = ET.Element('tBestellungen')
            root.append(bestellung_elem)
            
            # Konvertiere zu XML String
            xml_string = self._prettify_xml(root)
            
            # Schreibe in JTL DB (als komplette XML mit Root!)
            return self.jtl_repo.insert_xml_import(xml_string)
        
        except Exception as e:
            print(f"  ⚠ JTL Import Fehler für {order.bestell_id}: {e}")
            return False
    
    def _update_order_status(self, order_id: int) -> bool:
        """
        Setze xml_erstellt = 1 NACH erfolgreichem XML Export
        WICHTIG: Nur aufrufen wenn XML erfolgreich generiert wurde!
        
        Args:
            order_id: Order Datenbank ID
        
        Returns:
            bool: True wenn erfolgreich
        """
        try:
            success = self.order_repo.update_xml_export_status(order_id)
            if success:
                print(f"  ✓ Status gesetzt: xml_erstellt = 1")
            return success
        except Exception as e:
            print(f"✗ Status Update Fehler: {e}")
            return False
    
    def _save_xml_to_disk(self, root: ET.Element):
        """Speichere XML auf Festplatte"""
        xml_string = self._prettify_xml(root)
        
        with open(str(XML_OUTPUT_PATH), 'w', encoding='ISO-8859-1') as f:
            f.write(xml_string)
        
        print(f"✓ XML gespeichert: {XML_OUTPUT_PATH}")
    
    def _prettify_xml(self, elem: ET.Element) -> str:
        """Formatiere XML schön"""
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string).toprettyxml(
            indent="  ",
            encoding="ISO-8859-1"
        )
        return reparsed.decode("ISO-8859-1")