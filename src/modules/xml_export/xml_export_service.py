"""XML Export Service - Business Logic für XML Generierung"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from src.db.repositories.temu.order_repository import OrderRepository
from src.db.repositories.temu.order_item_repository import OrderItemRepository
from src.db.repositories.jtl_common.jtl_repository import JtlRepository
from src.services.log_service import log_service
from config.settings import JTL_WAEHRUNG, JTL_SPRACHE, JTL_K_BENUTZER, JTL_K_FIRMA
from src.modules.temu.config import XML_OUTPUT_PATH, TEMU_EXPORT_DIR

class XmlExportService:
    """Business Logic - XML Generierung für JTL"""
    
    def __init__(self, order_repo: OrderRepository = None, 
                 item_repo: OrderItemRepository = None,
                 jtl_repo: JtlRepository = None):
        """
        Args:
            order_repo: OrderRepository für TOCI
            item_repo: OrderItemRepository für TOCI
            jtl_repo: JtlRepository für JTL DB Access
        """
        self.order_repo = order_repo or OrderRepository()
        self.item_repo = item_repo or OrderItemRepository()
        self.jtl_repo = jtl_repo or JtlRepository()
        self._customer_nr_cache = {}  # Cache Kundennummern pro Email
    
    def export_to_xml(self, save_to_disk=True, import_to_jtl=True, save_to_db=True, job_id: Optional[str] = None) -> Dict:
        """
        Generiert XML aus Orders und exportiert zu JTL
        
        Args:
            save_to_disk: Speichere XML auf Festplatte
            import_to_jtl: Importiere XML in JTL DB
            save_to_db: Speichere XML in TOCI DB (temu_xml_export)
            job_id: Optional - für strukturiertes Logging
        
        Returns:
            dict mit Ergebnissen
        """
        
        try:

            log_service.log(job_id, "xml_export", "INFO", 
                              "→ Generiere XML aus Orders")
            
            # ===== Hole Orders mit status='importiert' =====
            orders = self._get_orders_to_export(job_id)
            
            if not orders:

                log_service.log(job_id, "xml_export", "INFO", 
                                  "✓ Keine neuen Orders zum Exportieren")
                return {'exported': 0, 'jtl_imported': 0, 'success': False}
            

            else:
                log_service.log(job_id, "xml_export", "INFO", 
                              f"  {len(orders)} Orders zum Exportieren gefunden")
            
            # ===== Generate XML Root (für gesamt-export) =====
            root = ET.Element('tBestellungen')
            exported_count = 0
            jtl_import_count = 0
            
            # ===== Für jede Order: XML generieren =====
            for order in orders:
                try:
                    # Hole Items für diese Order - versuche zuerst order_id, dann bestell_id
                    items = self.item_repo.find_by_order_id(order.id)
                    
                    # Fallback: Wenn keine Items gefunden, versuche über bestell_id
                    if not items:
                        items = self.item_repo.find_by_bestell_id(order.bestell_id)
                        if items:
                            log_service.log(job_id, "xml_export", "WARNING", 
                                              f"  ⚠ {order.bestell_id}: Items via bestell_id gefunden (nicht over order_id)")
                    
                    # DEBUG: Logge Items
                    log_service.log(job_id, "xml_export", "DEBUG", 
                                      f"  Order {order.bestell_id} (ID={order.id}): {len(items)} Items gefunden")
                    
                    # Generiere XML Element
                    bestellung_elem = self._generate_order_xml(order, items, root)
                    
                    if bestellung_elem is not None:
                        # ===== Step 0: Speichere Einzelne XML in TOCI DB =====
                        if save_to_db:
                            self._save_xml_to_db(order.bestell_id, bestellung_elem, job_id)
                        
                        # ===== Step 0b: Archiviere Einzel-XML in docs/exports =====
                        if save_to_disk:
                            self._archive_order_to_docs(order.bestell_id, bestellung_elem, job_id)

                        # ===== Step 1: In JTL DB importieren =====
                        if import_to_jtl and self.jtl_repo:
                            jtl_success = self._import_to_jtl(order, bestellung_elem, job_id)
                            if jtl_success:
                                jtl_import_count += 1
                                # Markiere Archiv-Eintrag als verarbeitet
                                self.order_repo.mark_xml_export_processed(order.bestell_id)
                        
                        # ===== Step 2: Update Status in TOCI =====
                        status_success = self._update_order_status(order.id, job_id)
                        
                        if status_success or not import_to_jtl:
                            exported_count += 1

                            log_service.log(job_id, "xml_export", "INFO", 
                                              f"  ✓ {order.bestell_id}: XML generiert")

                        else:

                            log_service.log(job_id, "xml_export", "WARNING", 
                                              f"  ⚠ {order.bestell_id}: Status Update fehlgeschlagen")
                    else:

                        log_service.log(job_id, "xml_export", "WARNING", 
                                          f"  ⚠ {order.bestell_id}: XML Generation fehlgeschlagen")
                
                except Exception as e:
                    import traceback
                    error_trace = traceback.format_exc()

                    log_service.log(job_id, "xml_export", "ERROR", 
                                      f"  ✗ Fehler bei Order {order.bestell_id}: {str(e)}")
                    log_service.log(job_id, "xml_export", "ERROR", error_trace)

            
            # ===== Step 3: Speichere komplette XML auf Festplatte =====
            if save_to_disk:
                self._save_xml_to_disk(root, job_id)
            

            log_service.log(job_id, "xml_export", "INFO", 
                              f"✓ XML Export erfolgreich: {exported_count} exportiert, {jtl_import_count} JTL importiert")
            
            return {
                'exported': exported_count,
                'jtl_imported': jtl_import_count,
                'success': exported_count > 0,
                'message': f'{exported_count} Orders exportiert'
            }
        
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()

            log_service.log(job_id, "xml_export", "ERROR", 
                              f"✗ XML Export Fehler: {str(e)}")
            log_service.log(job_id, "xml_export", "ERROR", error_trace)

            
            return {'exported': 0, 'jtl_imported': 0, 'success': False}
    
    def _get_orders_to_export(self, job_id: Optional[str] = None) -> List:
        """Hole Orders mit status='importiert' und xml_erstellt=0"""
        try:
            orders = self.order_repo.find_by_status('importiert')
            orders_to_export = [
                order for order in orders 
                if not order.xml_erstellt
            ]
            
            return orders_to_export
        
        except Exception as e:

            log_service.log(job_id, "xml_export", "ERROR", 
                              f"✗ Fehler beim Laden der Orders: {str(e)}")
            return []
    
    def _generate_order_xml(self, order, items, parent_elem) -> Optional[ET.Element]:
        """Generiere XML Element für eine Order"""
        
        # ===== Haupt-Bestellung Element =====
        bestellung = ET.SubElement(
            parent_elem, 'tBestellung',
            kFirma=JTL_K_FIRMA,
            kBenutzer=JTL_K_BENUTZER
        )
        
        # ===== Header Daten =====
        ET.SubElement(bestellung, 'cSprache').text = JTL_SPRACHE
        ET.SubElement(bestellung, 'cWaehrung').text = JTL_WAEHRUNG
        ET.SubElement(bestellung, 'cBestellNr')
        ET.SubElement(bestellung, 'cExterneBestellNr').text = order.bestell_id
        ET.SubElement(bestellung, 'cVersandartName').text = 'TEMU'
        ET.SubElement(bestellung, 'cVersandInfo')
        
        ET.SubElement(bestellung, 'dVersandDatum').text = (
            order.versanddatum.strftime('%d.%m.%Y') if order.versanddatum else ''
        )
        
        ET.SubElement(bestellung, 'cTracking').text = order.trackingnummer or ''
        ET.SubElement(bestellung, 'dLieferDatum')
        ET.SubElement(bestellung, 'cKommentar')
        ET.SubElement(bestellung, 'cBemerkung')
        
        ET.SubElement(bestellung, 'dErstellt').text = (
            order.kaufdatum.strftime('%d.%m.%Y') if order.kaufdatum else ''
        )
        
        ET.SubElement(bestellung, 'cZahlungsartName').text = 'TEMU'
        ET.SubElement(bestellung, 'dBezahltDatum')
        
        # ===== KORREKTE REIHENFOLGE: Artikel ZUERST, dann Kunde =====
        # ===== Artikel-Positionen =====
        for item in items:
            self._add_item_to_xml(bestellung, item)
        
        # ===== Versandkosten =====
        self._add_shipping_costs_to_xml(bestellung, order)
        
        # ===== Hole Kundennummer aus JTL (falls Email existiert) =====
        kunden_nr = self._get_jtl_customer_number(order.email)
        
        # ===== Kunde =====
        self._add_customer_to_xml(bestellung, order, kunden_nr)
        
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
        
        ET.SubElement(pos, 'fPreisEinzelNetto').text = f"{item.netto_einzelpreis:.5f}"
        ET.SubElement(pos, 'fPreis').text = f"{item.brutto_einzelpreis:.2f}"
        
        ET.SubElement(pos, 'fMwSt').text = f"{item.mwst_satz:.2f}"
        ET.SubElement(pos, 'fAnzahl').text = f"{item.menge:.2f}"
        ET.SubElement(pos, 'cPosTyp').text = 'standard'
        ET.SubElement(pos, 'fRabatt').text = '0.00'
    
    def _add_shipping_costs_to_xml(self, bestellung_elem, order):
        """Füge Versandkosten als Position hinzu"""
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
    
    def _add_customer_to_xml(self, bestellung_elem, order, kunden_nr: str = ''):
        """Füge Kundendaten hinzu"""
        kunde = ET.SubElement(bestellung_elem, 'tkunde')
        
        ET.SubElement(kunde, 'cKundenNr').text = kunden_nr or ''
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

    def _get_jtl_customer_number(self, email: str) -> str:
        """Hole JTL Kundennummer per E-Mail (mit einfachem Cache)."""
        if not email:
            return ''
        key = email.strip().lower()
        if not key:
            return ''

        if key in self._customer_nr_cache:
            return self._customer_nr_cache[key]

        if not self.jtl_repo:
            return ''

        try:
            kunden_nr = self.jtl_repo.get_customer_number_by_email(key) or ''
            self._customer_nr_cache[key] = kunden_nr
            return kunden_nr
        except Exception:
            # Kein hartes Fail: bei Fehlern leeres Feld -> JTL legt neuen Kunden an
            return ''
    
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
    
    def _import_to_jtl(self, order, bestellung_elem, job_id: Optional[str] = None) -> bool:
        """
        Importiere XML in JTL DB
        
        Args:
            order: Order Domain Model
            bestellung_elem: XML Element (einzelne Bestellung)
            job_id: Optional - für strukturiertes Logging
        
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
            
            # Schreibe in JTL DB
            return self.jtl_repo.insert_xml_import(xml_string)
        
        except Exception as e:

            log_service.log(job_id, "xml_export", "WARNING", 
                              f"  ⚠ JTL Import Fehler für {order.bestell_id}: {str(e)}")

            return False
    
    def _update_order_status(self, order_id: int, job_id: Optional[str] = None) -> bool:
        """
        Setze xml_erstellt = 1 NACH erfolgreichem XML Export
        
        Args:
            order_id: Order Datenbank ID
            job_id: Optional - für strukturiertes Logging
        
        Returns:
            bool: True wenn erfolgreich
        """
        try:
            success = self.order_repo.update_xml_export_status(order_id)
            return success
        except Exception as e:

            log_service.log(job_id, "xml_export", "ERROR", 
                              f"✗ Status Update Fehler: {str(e)}")

            return False
    
    def _save_xml_to_disk(self, root: ET.Element, job_id: Optional[str] = None):
        """Speichere komplette XML auf Festplatte mit Zeitstempel"""
        try:
            xml_string = self._prettify_xml(root)
            
            # Generiere Dateinamen mit Zeitstempel: jtl_temu_bestellungen_YYYYMMDD_HHMMSS.xml
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"jtl_temu_bestellungen_{timestamp}.xml"
            # XML_OUTPUT_PATH ist bereits ein Path Objekt, daher direkt .parent verwenden
            filepath = XML_OUTPUT_PATH.parent / filename
            
            # Stelle sicher, dass das Verzeichnis existiert
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(str(filepath), 'w', encoding='ISO-8859-1') as f:
                f.write(xml_string)
            

            log_service.log(job_id, "xml_export", "INFO", 
                              f"  ✓ XML gespeichert: {filepath}")

        
        except Exception as e:

            log_service.log(job_id, "xml_export", "ERROR", 
                              f"✗ XML Speicher-Fehler: {str(e)}")
    
    def _archive_order_to_docs(self, bestell_id: str, bestellung_elem: ET.Element, job_id: Optional[str] = None) -> None:
        """Speichere Einzel-XML pro Bestellung in data/temu/export mit Zeitstempel und Bestell-ID."""
        try:
            root = ET.Element('tBestellungen')
            root.append(bestellung_elem)
            xml_string = self._prettify_xml(root)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            TEMU_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            archive_file = TEMU_EXPORT_DIR / f"temu_order_{bestell_id}_{timestamp}.xml"

            with open(str(archive_file), 'w', encoding='ISO-8859-1') as f:
                f.write(xml_string)

            log_service.log(job_id, "xml_export", "INFO", 
                              f"  ↳ Einzel-XML archiviert (data/temu/export): {archive_file}")
        
        except Exception as e:
            log_service.log(job_id, "xml_export", "WARNING", 
                              f"  ⚠ Einzel-XML Archiv-Fehler für {bestell_id}: {str(e)}")

    def _save_xml_to_db(self, bestell_id: str, bestellung_elem: ET.Element, job_id: Optional[str] = None) -> bool:
        """Speichere einzelne XML in TOCI DB (temu_xml_export Tabelle)"""
        try:
            # Wrap Element in Root für valides XML
            root = ET.Element('tBestellungen')
            # Kopiere das Element
            root.append(bestellung_elem)
            
            xml_string = self._prettify_xml(root)
            
            # Speichere in TOCI Datenbank
            return self.order_repo.insert_xml_export(bestell_id, xml_string)
        
        except Exception as e:
            log_service.log(job_id, "xml_export", "WARNING", 
                              f"  ⚠ XML DB Speicher-Fehler für {bestell_id}: {str(e)}")
            return False

    
    def _prettify_xml(self, elem: ET.Element) -> str:
        """Formatiere XML schön"""
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string).toprettyxml(
            indent="  ",
            encoding="ISO-8859-1"
        )
        return reparsed.decode("ISO-8859-1")