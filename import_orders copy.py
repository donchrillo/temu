import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import re
import csv
import io

# --- EINSTELLUNGEN ---
CSV_DATEINAME = 'order_export.csv' 
XML_DATEINAME = 'jtl_temu_bestellungen.xml'

# Allgemeine JTL-Einstellungen
WAEHRUNG = 'EUR'
SPRACHE = 'ger'
K_BENUTZER = '1'
K_FIRMA = '1'

# Benötigte Spalten für die Validierung
REQUIRED_COLS = ['Bestell-ID', 'Bestellartikel-ID', 'Beitrags-SKU', 'Gekaufte Menge', 'Kaufdatum', 
                 'Name des Empfängers', 'Vorname des Empfängers', 'Nachname des Empfängers', 'Versandadresse 1', 
                 'Versandpostleitzahl (Muss an die folgende Postleitzahl gesendet werden.)', 'Versandort', 'Versandland', 
                 'Aktivitätsbasispreis der Waren', 'Gesamteinzelhandelspreis', 'Virtuelle E-Mail']

# --- HILFSFUNKTIONEN ---

def _clean_price(price_str):
    """Konvertiert den Preis-String (z.B. "15,00€") in einen float."""
    if isinstance(price_str, str):
        cleaned_str = price_str.replace('€', '').replace('.', '').replace(',', '.').strip()
        try:
            return float(cleaned_str)
        except ValueError:
            return 0.00
    return float(price_str)

def _format_date(date_str):
    """Konvertiert das TEMU Datumsformat in das JTL-kompatible Format (DD.MM.YYYY)."""
    cleaned_date = re.sub(r'\sUhr\sCET\(UTC[+-]\d+\)', '', date_str).strip()
    try:
        dt = datetime.strptime(cleaned_date, '%d. %b. %Y, %H:%M')
        return dt.strftime('%d.%m.%Y')
    except Exception:
        try:
            dt = datetime.strptime(cleaned_date.replace('.', ''), '%d %b %Y, %H:%M')
            return dt.strftime('%d.%m.%Y')
        except:
            return datetime.now().strftime('%d.%m.%Y')

def _clean_street(address_line):
    """Versucht, die Straße und die Hausnummer zu trennen."""
    if not isinstance(address_line, str):
        return '', ''
    address_line = address_line.strip()
    
    match = re.search(r'(\s\d+[a-zA-Z]?(-|/)?\d*[a-zA-Z]?)$', address_line)
    if match:
        street = address_line[:match.start()].strip()
        number = match.group(1).strip()
        return street, number
    return address_line, '' 

def _get_country_iso(country_name):
    """Konvertiert den vollen Ländernamen (TEMU) in den ISO-Code (JTL)."""
    mapping = {
        'Germany': 'DE',
        'Austria': 'AT',
        'France': 'FR',
        'Netherlands': 'NL'
    }
    return mapping.get(country_name, country_name) 

def _prettify_xml(elem):
    """Gibt einen schön formatierten XML-String zurück."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string).toprettyxml(indent="  ", encoding="ISO-8859-1")
    return reparsed.decode("ISO-8859-1")

# --- HAUPTFUNKTION ---

def convert_temu_csv_to_jtl_xml(csv_file, xml_file):
    """Liest die TEMU CSV und konvertiert sie in das JTL XML Format."""

    df = None
    
    # 1. CSV einlesen - TEMU nutzt KOMMAS als Trennzeichen
    try:
        # Dateiinhalt direkt mit pandas einlesen (Komma-separiert)
        df = pd.read_csv(csv_file, delimiter=',', quotechar='"', encoding='utf-8-sig', dtype=str, keep_default_na=False)
        
        # Spaltennamen bereinigen
        df.columns = df.columns.str.replace('\ufeff', '', regex=False) 
        df.columns = df.columns.str.replace('\xa0', ' ', regex=False).str.strip() 
        df.columns = df.columns.str.strip() 
        
        df.replace('', pd.NA, inplace=True)
        df.fillna('', inplace=True) 
        print(f"INFO: CSV erfolgreich eingelesen. {len(df)} Zeilen gefunden.")
        print(f"INFO: Gefundene Spalten: {list(df.columns[:5])}")
        if len(df) > 0:
            print(f"INFO: Erste Bestell-ID: {df['Bestell-ID'].iloc[0]}")

    except Exception as e:
        print(f"FEHLER beim Einlesen der CSV-Datei. Ursache: {e}")
        import traceback
        traceback.print_exc()
        return None

    # 1.3 Datentypen und Preise konvertieren
    price_cols = ['Gesamteinzelhandelspreis', 'Versandkosten']
    
    for col in price_cols:
        if col not in df.columns:
            print(f"FATALER FEHLER: Die benötigte Spalte '{col}' fehlt im DataFrame.")
            print("\nGefundene Spalten (zum Debuggen):")
            print(df.columns.tolist())
            return None
        
        df[col] = df[col].apply(_clean_price)
    
    df['Gekaufte Menge'] = pd.to_numeric(df['Gekaufte Menge'], errors='coerce').fillna(0)
    
    # 1.4 Spalten-Validierung (aktualisierte Spalten)
    required_cols = ['Bestell-ID', 'Bestellartikel-ID', 'Beitrags-SKU', 'Gekaufte Menge', 'Kaufdatum', 
                     'Name des Empfängers', 'Vorname des Empfängers', 'Nachname des Empfängers', 'Versandadresse 1', 
                     'Versandpostleitzahl (Muss an die folgende Postleitzahl gesendet werden.)', 
                     'Versandort', 'Versandland', 'Gesamteinzelhandelspreis', 'Versandkosten',
                     'Virtuelle E-Mail', 'Produktname']
    
    for col in required_cols:
        if col not in df.columns:
            print(f"FATALER FEHLER: Die benötigte Spalte '{col}' fehlt trotz Bereinigung.")
            return None

    # 2. Datenvorbereitung - Preise pro Artikel berechnen
    df['Netto_Einzelpreis'] = df.apply(
        lambda row: row['Gesamteinzelhandelspreis'] / row['Gekaufte Menge'] 
        if row['Gekaufte Menge'] > 0 else 0.00,
        axis=1
    )
    
    grouped_orders = df.groupby('Bestell-ID')

    # 3. XML-Struktur aufbauen
    root = ET.Element('tBestellungen')

    for order_id, group in grouped_orders:
        
        order_data = group.iloc[0]
        
        # --- Bestellung-Tag ---
        bestellung = ET.SubElement(root, 'tBestellung', kFirma=K_FIRMA, kBenutzer=K_BENUTZER)
        
        # Basis-Informationen
        ET.SubElement(bestellung, 'cSprache').text = SPRACHE
        ET.SubElement(bestellung, 'cWaehrung').text = WAEHRUNG
        ET.SubElement(bestellung, 'cBestellNr')  # LEER - wird von JTL automatisch gesetzt
        ET.SubElement(bestellung, 'cExterneBestellNr').text = str(order_id)  # TEMU Bestell-ID
        ET.SubElement(bestellung, 'cVersandartName').text = 'TEMU'
        ET.SubElement(bestellung, 'cVersandInfo')
        ET.SubElement(bestellung, 'dVersandDatum')
        ET.SubElement(bestellung, 'cTracking')
        ET.SubElement(bestellung, 'dLieferDatum')
        ET.SubElement(bestellung, 'cKommentar')
        ET.SubElement(bestellung, 'cBemerkung')
        ET.SubElement(bestellung, 'dErstellt').text = _format_date(order_data['Kaufdatum'])
        ET.SubElement(bestellung, 'cZahlungsartName').text = 'TEMU'
        ET.SubElement(bestellung, 'dBezahltDatum')

        # --- Positionen (Artikel) ---
        for index, row in group.iterrows():
            pos = ET.SubElement(bestellung, 'twarenkorbpos')
            
            # Gesamteinzelhandelspreis ist der Netto-Preis pro Artikel
            netto_einzelpreis = row['Netto_Einzelpreis']
            mwst_satz = 19.00
            brutto_einzelpreis = netto_einzelpreis * (1 + mwst_satz / 100)
            
            ET.SubElement(pos, 'cName').text = str(row['Produktname'])
            ET.SubElement(pos, 'cArtNr').text = str(row['Beitrags-SKU'])
            ET.SubElement(pos, 'cBarcode')
            ET.SubElement(pos, 'cSeriennummer').text = str(row['Bestellartikel-ID'])  # neu: Bestellartikel-ID hier
            ET.SubElement(pos, 'cEinheit')
            ET.SubElement(pos, 'fPreisEinzelNetto').text = f"{netto_einzelpreis:.5f}"
            ET.SubElement(pos, 'fPreis').text = f"{brutto_einzelpreis:.2f}"
            ET.SubElement(pos, 'fMwSt').text = f"{mwst_satz:.2f}"
            ET.SubElement(pos, 'fAnzahl').text = f"{row['Gekaufte Menge']:.2f}"
            ET.SubElement(pos, 'cPosTyp').text = 'standard'
            ET.SubElement(pos, 'fRabatt').text = '0.00'
            # Entfernt: twarenkorbposeigenschaft / cFreifeldWert

        # Versandkosten-Position (Definition hinzugefügt)
        versandkosten_netto = float(order_data['Versandkosten'])
        versandkosten_brutto = versandkosten_netto * 1.19
        versand_pos = ET.SubElement(bestellung, 'twarenkorbpos')
        ET.SubElement(versand_pos, 'cName').text = 'TEMU Versand'
        ET.SubElement(versand_pos, 'cArtNr')
        ET.SubElement(versand_pos, 'cBarcode')
        ET.SubElement(versand_pos, 'cSeriennummer')  # leer gelassen
        ET.SubElement(versand_pos, 'cEinheit')
        ET.SubElement(versand_pos, 'fPreisEinzelNetto').text = f"{versandkosten_netto:.5f}"
        ET.SubElement(versand_pos, 'fPreis').text = f"{versandkosten_brutto:.2f}"
        ET.SubElement(versand_pos, 'fMwSt').text = '19.00'
        ET.SubElement(versand_pos, 'fAnzahl').text = '1.00'
        ET.SubElement(versand_pos, 'cPosTyp').text = 'versandkosten'
        ET.SubElement(versand_pos, 'fRabatt').text = '0.00'
        
        # Adressdaten
        strasse, hausnummer = _clean_street(str(order_data['Versandadresse 1']))
        land_iso = _get_country_iso(str(order_data['Versandland']))
        
        # Namenslogik: Wenn Vorname und Nachname leer sind, "Name des Empfängers" verwenden
        vorname = str(order_data['Vorname des Empfängers']).strip()
        nachname = str(order_data['Nachname des Empfängers']).strip()
        
        if not vorname and not nachname:
            # Beide leer -> Name des Empfängers in Nachname, Vorname bleibt leer
            vorname = ''
            nachname = str(order_data['Name des Empfängers']).strip()
        
        # --- Rechnungsadresse (tkunde) ---
        kunde = ET.SubElement(bestellung, 'tkunde')
        ET.SubElement(kunde, 'cKundenNr')  # LEER - wird von JTL automatisch ausgefüllt
        ET.SubElement(kunde, 'cAnrede')
        ET.SubElement(kunde, 'cTitel')
        ET.SubElement(kunde, 'cVorname').text = vorname
        ET.SubElement(kunde, 'cNachname').text = nachname
        ET.SubElement(kunde, 'cFirma')
        ET.SubElement(kunde, 'cStrasse').text = f"{strasse} {hausnummer}".strip()
        ET.SubElement(kunde, 'cAdressZusatz')
        ET.SubElement(kunde, 'cPLZ').text = str(order_data['Versandpostleitzahl (Muss an die folgende Postleitzahl gesendet werden.)']).strip()
        ET.SubElement(kunde, 'cOrt').text = str(order_data['Versandort'])
        ET.SubElement(kunde, 'cBundesland')
        ET.SubElement(kunde, 'cLand').text = land_iso
        ET.SubElement(kunde, 'cTel')
        ET.SubElement(kunde, 'cMobil')
        ET.SubElement(kunde, 'cFax')
        ET.SubElement(kunde, 'cMail').text = str(order_data['Virtuelle E-Mail'])
        ET.SubElement(kunde, 'cUSTID')
        ET.SubElement(kunde, 'cWWW')
        ET.SubElement(kunde, 'cHerkunft').text = 'TEMU'
        ET.SubElement(kunde, 'dErstellt').text = _format_date(order_data['Kaufdatum'])
        
        # --- Lieferadresse (tlieferadresse) - ALLE Felder müssen da sein ---
        lieferadresse = ET.SubElement(bestellung, 'tlieferadresse')
        ET.SubElement(lieferadresse, 'cAnrede')  # Pflichtfeld (muss da sein, auch wenn leer)
        ET.SubElement(lieferadresse, 'cVorname').text = vorname
        ET.SubElement(lieferadresse, 'cNachname').text = nachname
        ET.SubElement(lieferadresse, 'cTitel')  # Pflichtfeld (muss da sein, auch wenn leer)
        ET.SubElement(lieferadresse, 'cFirma')  # Pflichtfeld (muss da sein, auch wenn leer)
        ET.SubElement(lieferadresse, 'cStrasse').text = f"{strasse} {hausnummer}".strip()
        ET.SubElement(lieferadresse, 'cAdressZusatz')  # Pflichtfeld (muss da sein, auch wenn leer)
        ET.SubElement(lieferadresse, 'cPLZ').text = str(order_data['Versandpostleitzahl (Muss an die folgende Postleitzahl gesendet werden.)']).strip()
        ET.SubElement(lieferadresse, 'cOrt').text = str(order_data['Versandort'])
        ET.SubElement(lieferadresse, 'cBundesland')  # Pflichtfeld (muss da sein, auch wenn leer)
        ET.SubElement(lieferadresse, 'cLand').text = land_iso
        ET.SubElement(lieferadresse, 'cTel')  # Pflichtfeld (muss da sein, auch wenn leer)
        ET.SubElement(lieferadresse, 'cMobil')  # Pflichtfeld (muss da sein, auch wenn leer)
        ET.SubElement(lieferadresse, 'cFax')  # Pflichtfeld (muss da sein, auch wenn leer)
        ET.SubElement(lieferadresse, 'cMail').text = str(order_data['Virtuelle E-Mail'])
        
        # --- Zahlungsinfo - ALLE Felder müssen da sein (auch wenn leer) ---
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
            
    # 4. XML-Datei speichern
    xml_output = _prettify_xml(root)
    
    with open(xml_file, 'w', encoding='ISO-8859-1') as f:
        f.write(xml_output)
    
    print(f"SUCCESS: XML-Datei wurde erfolgreich erstellt: {xml_file}")
    return xml_file


# --- HAUPTPROGRAMM ---
if __name__ == "__main__":
    print("=" * 60)
    print("TEMU CSV zu JTL XML Konverter")
    print("=" * 60)
    
    result = convert_temu_csv_to_jtl_xml(CSV_DATEINAME, XML_DATEINAME)
    
    if result:
        print(f"\n✓ Konvertierung erfolgreich abgeschlossen!")
        print(f"  Output: {result}")
    else:
        print("\n✗ Konvertierung fehlgeschlagen. Bitte Fehlermeldungen prüfen.")