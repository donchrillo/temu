"""XML Generator Service - erstellt JTL-XML aus Datenbank"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from db.connection import get_db_connection
from config.settings import (
    TABLE_ORDERS, TABLE_ORDER_ITEMS, TABLE_XML_EXPORT,
    DB_TOCI, DB_JTL, JTL_WAEHRUNG, JTL_SPRACHE, 
    JTL_K_BENUTZER, JTL_K_FIRMA, XML_OUTPUT_PATH
)

def _prettify_xml(elem):
    """Formatiert XML schön"""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string).toprettyxml(indent="  ", encoding="ISO-8859-1")
    return reparsed.decode("ISO-8859-1")

def generate_xml_for_orders():
    """Generiert XML für alle Bestellungen mit status='importiert'"""
    
    print("=" * 60)
    print("XML-Generierung für JTL")
    print("=" * 60)
    
    # Verbindung zu TOCI
    conn = get_db_connection(DB_TOCI)
    cursor = conn.cursor()
    print(f"✓ {DB_TOCI} Verbindung hergestellt")
    
    # JTL Verbindung für direkten Import
    try:
        conn_jtl = get_db_connection(DB_JTL)
        cursor_jtl = conn_jtl.cursor()
        print(f"✓ {DB_JTL} Verbindung hergestellt")
    except Exception as e:
        print(f"⚠ JTL-Verbindung fehlgeschlagen: {e}")
        conn_jtl = None
        cursor_jtl = None
    
    # Bestellungen holen (status='importiert', nicht storniert)
    cursor.execute(f"""
        SELECT * FROM {TABLE_ORDERS} 
        WHERE status = 'importiert' 
          AND xml_erstellt = 0
          AND bestellstatus != 'Storniert'
    """)
    
    orders = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    
    if not orders:
        print("✓ Keine neuen Bestellungen")
        cursor.close()
        conn.close()
        if conn_jtl:
            cursor_jtl.close()
            conn_jtl.close()
        return True
    
    print(f"✓ {len(orders)} Bestellungen gefunden")
    
    # XML Root
    root = ET.Element('tBestellungen')
    processed_count = 0
    jtl_import_count = 0
    
    for order_row in orders:
        order = dict(zip(columns, order_row))
        order_id = order['bestell_id']
        order_db_id = order['id']
        
        # Artikel holen
        cursor.execute(f"SELECT * FROM {TABLE_ORDER_ITEMS} WHERE order_id = ?", order_db_id)
        items = cursor.fetchall()
        item_columns = [column[0] for column in cursor.description]
        
        # XML Bestellung erstellen
        bestellung = ET.SubElement(root, 'tBestellung', kFirma=JTL_K_FIRMA, kBenutzer=JTL_K_BENUTZER)
        
        ET.SubElement(bestellung, 'cSprache').text = JTL_SPRACHE
        ET.SubElement(bestellung, 'cWaehrung').text = JTL_WAEHRUNG
        ET.SubElement(bestellung, 'cBestellNr')
        ET.SubElement(bestellung, 'cExterneBestellNr').text = order_id
        ET.SubElement(bestellung, 'cVersandartName').text = 'TEMU'
        ET.SubElement(bestellung, 'cVersandInfo')
        ET.SubElement(bestellung, 'dVersandDatum')
        ET.SubElement(bestellung, 'cTracking')
        ET.SubElement(bestellung, 'dLieferDatum')
        ET.SubElement(bestellung, 'cKommentar')
        ET.SubElement(bestellung, 'cBemerkung')
        ET.SubElement(bestellung, 'dErstellt').text = order['kaufdatum'].strftime('%d.%m.%Y')
        ET.SubElement(bestellung, 'cZahlungsartName').text = 'TEMU'
        ET.SubElement(bestellung, 'dBezahltDatum')
        
        # Artikel-Positionen
        for item_row in items:
            item = dict(zip(item_columns, item_row))
            
            pos = ET.SubElement(bestellung, 'twarenkorbpos')
            ET.SubElement(pos, 'cName').text = item['produktname']
            ET.SubElement(pos, 'cArtNr').text = item['sku']
            ET.SubElement(pos, 'cBarcode')
            ET.SubElement(pos, 'cEinheit')
            ET.SubElement(pos, 'fPreisEinzelNetto').text = f"{item['netto_einzelpreis']:.5f}"
            ET.SubElement(pos, 'fPreis').text = f"{item['brutto_einzelpreis']:.2f}"
            ET.SubElement(pos, 'fMwSt').text = f"{item['mwst_satz']:.2f}"
            ET.SubElement(pos, 'fAnzahl').text = f"{item['menge']:.2f}"
            ET.SubElement(pos, 'cPosTyp').text = 'standard'
            ET.SubElement(pos, 'fRabatt').text = '0.00'
        
        # Versandkosten
        versand_pos = ET.SubElement(bestellung, 'twarenkorbpos')
        versandkosten_netto = float(order['versandkosten'])
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
        
        # Kunde
        kunde = ET.SubElement(bestellung, 'tkunde')
        ET.SubElement(kunde, 'cKundenNr')
        ET.SubElement(kunde, 'cAnrede')
        ET.SubElement(kunde, 'cTitel')
        ET.SubElement(kunde, 'cVorname').text = order['vorname_empfaenger'] or ''
        ET.SubElement(kunde, 'cNachname').text = order['nachname_empfaenger'] or ''
        ET.SubElement(kunde, 'cFirma')
        ET.SubElement(kunde, 'cStrasse').text = order['strasse'] or ''
        ET.SubElement(kunde, 'cAdressZusatz')
        ET.SubElement(kunde, 'cPLZ').text = order['plz'] or ''
        ET.SubElement(kunde, 'cOrt').text = order['ort'] or ''
        ET.SubElement(kunde, 'cBundesland').text = order['bundesland'] or ''
        ET.SubElement(kunde, 'cLand').text = order['land_iso'] or ''
        ET.SubElement(kunde, 'cTel').text = order['telefon_empfaenger'] or ''
        ET.SubElement(kunde, 'cMobil')
        ET.SubElement(kunde, 'cFax')
        ET.SubElement(kunde, 'cMail').text = order['email'] or ''
        ET.SubElement(kunde, 'cUSTID')
        ET.SubElement(kunde, 'cWWW')
        ET.SubElement(kunde, 'cHerkunft').text = 'TEMU'
        ET.SubElement(kunde, 'dErstellt').text = order['kaufdatum'].strftime('%d.%m.%Y')
        
        # Lieferadresse
        lieferadresse = ET.SubElement(bestellung, 'tlieferadresse')
        ET.SubElement(lieferadresse, 'cAnrede')
        ET.SubElement(lieferadresse, 'cVorname').text = order['vorname_empfaenger'] or ''
        ET.SubElement(lieferadresse, 'cNachname').text = order['nachname_empfaenger'] or ''
        ET.SubElement(lieferadresse, 'cTitel')
        ET.SubElement(lieferadresse, 'cFirma')
        ET.SubElement(lieferadresse, 'cStrasse').text = order['strasse'] or ''
        ET.SubElement(lieferadresse, 'cAdressZusatz')
        ET.SubElement(lieferadresse, 'cPLZ').text = order['plz'] or ''
        ET.SubElement(lieferadresse, 'cOrt').text = order['ort'] or ''
        ET.SubElement(lieferadresse, 'cBundesland').text = order['bundesland'] or ''
        ET.SubElement(lieferadresse, 'cLand').text = order['land_iso'] or ''
        ET.SubElement(lieferadresse, 'cTel').text = order['telefon_empfaenger'] or ''
        ET.SubElement(lieferadresse, 'cMobil')
        ET.SubElement(lieferadresse, 'cFax')
        ET.SubElement(lieferadresse, 'cMail').text = order['email'] or ''
        
        # Zahlungsinfo
        zahlungsinfo = ET.SubElement(bestellung, 'tzahlungsinfo')
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
        
        # Einzelne Bestellung als XML
        single_root = ET.Element('tBestellungen')
        single_root.append(bestellung)
        xml_string = _prettify_xml(single_root)
        
        # In TOCI Export-Tabelle speichern
        cursor.execute(f"""
            INSERT INTO {TABLE_XML_EXPORT} (bestell_id, xml_content, status)
            VALUES (?, ?, 'pending')
        """, order_id, xml_string)
        
        cursor.execute("SELECT @@IDENTITY")
        xml_export_id = cursor.fetchone()[0]
        
        # In JTL Import-Tabelle schreiben
        jtl_import_success = False
        if conn_jtl and cursor_jtl:
            try:
                cursor_jtl.execute("""
                    INSERT INTO [dbo].[tXMLBestellImport] (cText, nPlattform, nRechnung)
                    VALUES (?, 5, 0)
                """, xml_string)
                jtl_import_count += 1
                jtl_import_success = True
                print(f"  ✓ {order_id} → JTL")
            except Exception as e:
                print(f"  ⚠ {order_id}: {e}")
        
        # Status aktualisieren
        if jtl_import_success:
            cursor.execute(f"""
                UPDATE {TABLE_XML_EXPORT}
                SET status = 'imported', verarbeitet = 1, processed_at = GETDATE()
                WHERE id = ?
            """, xml_export_id)
        
        cursor.execute(f"""
            UPDATE {TABLE_ORDERS}
            SET xml_erstellt = 1, status = 'xml_erstellt', updated_at = GETDATE()
            WHERE id = ?
        """, order_db_id)
        
        processed_count += 1
    
    # Gesamte XML-Datei speichern
    xml_output = _prettify_xml(root)
    with open(str(XML_OUTPUT_PATH), 'w', encoding='ISO-8859-1') as f:
        f.write(xml_output)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    if conn_jtl:
        conn_jtl.commit()
        cursor_jtl.close()
        conn_jtl.close()
    
    print(f"\n{'='*70}")
    print(f"✓ XML-Generierung erfolgreich!")
    print(f"  Bestellungen: {processed_count}")
    print(f"  JTL-Import: {jtl_import_count}")
    print(f"{'='*70}\n")
    
    return True