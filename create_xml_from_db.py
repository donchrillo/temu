import pyodbc
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
from dotenv import load_dotenv

load_dotenv()

# --- EINSTELLUNGEN ---
SQL_SERVER = os.getenv('SQL_SERVER')
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')

# Datenbanknamen (fest im Code)
DB_TOCI = 'toci'
DB_JTL = 'eazybusiness'

TABLE_ORDERS = os.getenv('TABLE_ORDERS', 'temu_orders')
TABLE_ORDER_ITEMS = os.getenv('TABLE_ORDER_ITEMS', 'temu_order_items')
TABLE_XML_EXPORT = os.getenv('TABLE_XML_EXPORT', 'temu_xml_export')

WAEHRUNG = os.getenv('JTL_WAEHRUNG', 'EUR')
SPRACHE = os.getenv('JTL_SPRACHE', 'ger')
K_BENUTZER = os.getenv('JTL_K_BENUTZER', '1')
K_FIRMA = os.getenv('JTL_K_FIRMA', '1')

XML_OUTPUT_PATH = os.getenv('XML_OUTPUT_PATH', 'jtl_temu_bestellungen.xml')

def get_db_connection(database=DB_TOCI):
    """Erstellt SQL Server Verbindung zu einer bestimmten Datenbank."""
    # Verfügbare Treiber in Priorität
    drivers = [
        'ODBC Driver 18 for SQL Server',
        'ODBC Driver 17 for SQL Server',
        'ODBC Driver 13 for SQL Server',
        'SQL Server Native Client 11.0',
        'SQL Server'
    ]
    
    # Installierten Treiber finden
    available_drivers = [d for d in pyodbc.drivers() if 'SQL Server' in d]
    
    driver = None
    for d in drivers:
        if d in available_drivers:
            driver = d
            break
    
    if not driver and available_drivers:
        driver = available_drivers[0]
    
    if not driver:
        raise Exception("Kein SQL Server ODBC-Treiber gefunden!")
    
    conn_str = (
        f'DRIVER={{{driver}}};'
        f'SERVER={SQL_SERVER};'
        f'DATABASE={database};'
        f'UID={SQL_USERNAME};'
        f'PWD={SQL_PASSWORD};'
        f'TrustServerCertificate=yes;'
    )
    return pyodbc.connect(conn_str)

def _prettify_xml(elem):
    """Formatiert XML schön."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string).toprettyxml(indent="  ", encoding="ISO-8859-1")
    return reparsed.decode("ISO-8859-1")

def create_xml_for_orders():
    """Erstellt XML für alle Bestellungen mit status='importiert'."""
    
    print("=" * 60)
    print("XML-Export für JTL erstellen")
    print("=" * 60)
    
    # Verbindung zur TOCI Datenbank (wo TEMU Orders liegen)
    conn = get_db_connection(DB_TOCI)
    cursor = conn.cursor()
    print(f"✓ {DB_TOCI} Datenbankverbindung hergestellt")
    
    # JTL Datenbankverbindung für direkten XML-Import
    try:
        conn_jtl = get_db_connection(DB_JTL)
        cursor_jtl = conn_jtl.cursor()
        print(f"✓ {DB_JTL} Datenbankverbindung hergestellt")
    except Exception as e:
        print(f"⚠ WARNUNG: JTL-Verbindung fehlgeschlagen: {e}")
        print("  XML wird nur in Datei gespeichert")
        conn_jtl = None
        cursor_jtl = None
    
    # Bestellungen aus TOCI holen die noch nicht verarbeitet wurden
    # WICHTIG: Stornierte Bestellungen NICHT exportieren!
    cursor.execute(f"""
        SELECT * FROM {TABLE_ORDERS} 
        WHERE status = 'importiert' 
          AND xml_erstellt = 0
          AND bestellstatus != 'Storniert'
    """)
    
    orders = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    
    if not orders:
        print("✓ Keine neuen Bestellungen zum Verarbeiten")
        # Prüfen ob stornierte Bestellungen vorhanden sind
        cursor.execute(f"""
            SELECT COUNT(*) FROM {TABLE_ORDERS} 
            WHERE status = 'storniert' AND xml_erstellt = 0
        """)
        storniert_count = cursor.fetchone()[0]
        if storniert_count > 0:
            print(f"  ⚠ {storniert_count} stornierte Bestellungen werden übersprungen")
        cursor.close()
        conn.close()
        if conn_jtl:
            cursor_jtl.close()
            conn_jtl.close()
        return True
    
    print(f"✓ {len(orders)} Bestellungen gefunden")
    
    # XML Root erstellen für Datei-Export
    root = ET.Element('tBestellungen')
    processed_count = 0
    jtl_import_count = 0
    
    for order_row in orders:
        order = dict(zip(columns, order_row))
        order_id = order['bestell_id']
        order_db_id = order['id']
        
        # Artikel aus TOCI holen
        cursor.execute(f"""
            SELECT * FROM {TABLE_ORDER_ITEMS}
            WHERE order_id = ?
        """, order_db_id)
        
        items = cursor.fetchall()
        item_columns = [column[0] for column in cursor.description]
        
        # Bestellung-XML erstellen
        bestellung = ET.SubElement(root, 'tBestellung', kFirma=K_FIRMA, kBenutzer=K_BENUTZER)
        
        ET.SubElement(bestellung, 'cSprache').text = SPRACHE
        ET.SubElement(bestellung, 'cWaehrung').text = WAEHRUNG
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
        
        # XML für diese einzelne Bestellung erstellen (für JTL Import)
        single_root = ET.Element('tBestellungen')
        single_root.append(bestellung)
        xml_string = _prettify_xml(single_root)
        
        # In eigene Export-Tabelle in TOCI speichern
        cursor.execute(f"""
            INSERT INTO {TABLE_XML_EXPORT} (bestell_id, xml_content, status)
            VALUES (?, ?, 'pending')
        """, order_id, xml_string)
        
        # ID des eingefügten Export-Eintrags holen
        cursor.execute("SELECT @@IDENTITY")
        xml_export_id = cursor.fetchone()[0]
        
        # Direkt in JTL eazybusiness Import-Tabelle schreiben
        jtl_import_success = False
        if conn_jtl and cursor_jtl:
            try:
                cursor_jtl.execute("""
                    INSERT INTO [dbo].[tXMLBestellImport] 
                    (cText, nPlattform, nRechnung)
                    VALUES (?, 5, 0)
                """, xml_string)
                jtl_import_count += 1
                jtl_import_success = True
                print(f"  ✓ {order_id} in JTL importiert")
            except Exception as e:
                print(f"  ⚠ {order_id}: JTL-Import fehlgeschlagen: {e}")
        
        # XML Export Status aktualisieren wenn JTL Import erfolgreich
        if jtl_import_success:
            cursor.execute(f"""
                UPDATE {TABLE_XML_EXPORT}
                SET status = 'imported',
                    verarbeitet = 1,
                    processed_at = GETDATE()
                WHERE id = ?
            """, xml_export_id)
        
        # Status in TOCI aktualisieren
        cursor.execute(f"""
            UPDATE {TABLE_ORDERS}
            SET xml_erstellt = 1, status = 'xml_erstellt', updated_at = GETDATE()
            WHERE id = ?
        """, order_db_id)
        
        processed_count += 1
    
    # Gesamte XML-Datei speichern
    xml_output = _prettify_xml(root)
    with open(XML_OUTPUT_PATH, 'w', encoding='ISO-8859-1') as f:
        f.write(xml_output)
    
    # TOCI Transaktion abschließen
    conn.commit()
    cursor.close()
    conn.close()
    
    # JTL Transaktion abschließen
    if conn_jtl:
        conn_jtl.commit()
        cursor_jtl.close()
        conn_jtl.close()
    
    print(f"\n{'='*60}")
    print(f"✓ XML-Export erfolgreich!")
    print(f"  Verarbeitete Bestellungen: {processed_count}")
    print(f"  In JTL importiert: {jtl_import_count}")
    print(f"  XML-Datei: {XML_OUTPUT_PATH}")
    print(f"{'='*60}\n")
    
    return True

if __name__ == "__main__":
    create_xml_for_orders()
