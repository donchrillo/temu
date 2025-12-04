"""CSV-Import Service - importiert CSV in Datenbank"""

import pandas as pd
from datetime import datetime
import re
from src.database.connection import get_db_connection
from config.settings import TABLE_ORDERS, TABLE_ORDER_ITEMS, CSV_INPUT_PATH

def _clean_price(price_str):
    """Konvertiert Preis-String zu float"""
    if isinstance(price_str, str):
        cleaned_str = price_str.replace('€', '').replace('.', '').replace(',', '.').strip()
        try:
            return float(cleaned_str)
        except ValueError:
            return 0.00
    return float(price_str)

def _format_date(date_str):
    """Konvertiert TEMU Datumsformat zu datetime"""
    cleaned_date = re.sub(r'\sUhr\sCET\(UTC[+-]\d+\)', '', date_str).strip()
    try:
        return datetime.strptime(cleaned_date, '%d. %b. %Y, %H:%M')
    except Exception:
        try:
            return datetime.strptime(cleaned_date.replace('.', ''), '%d %b %Y, %H:%M')
        except:
            return datetime.now()

def _clean_street(address_line):
    """Trennt Straße und Hausnummer"""
    if not isinstance(address_line, str):
        return '', ''
    address_line = address_line.strip()
    
    match = re.search(r'(\s\d+[a-zA-Z]?(-|/)?\d*[a-zA-Z]?)$', address_line)
    if match:
        street = address_line[:match.start()].strip()
        number = match.group(1).strip()
        return f"{street} {number}".strip(), ''
    return address_line, ''

def _get_country_iso(country_name):
    """Konvertiert Ländernamen zu ISO-Code"""
    mapping = {
        'Germany': 'DE',
        'Austria': 'AT',
        'France': 'FR',
        'Netherlands': 'NL'
    }
    return mapping.get(country_name, 'DE')

def import_csv_to_database(csv_file=None):
    """Importiert CSV in Datenbank"""
    
    if csv_file is None:
        csv_file = str(CSV_INPUT_PATH)
    
    print("=" * 60)
    print("CSV Import → Datenbank")
    print("=" * 60)
    
    # CSV einlesen
    try:
        df = pd.read_csv(csv_file, delimiter=',', quotechar='"', encoding='utf-8-sig', dtype=str, keep_default_na=False)
        df.columns = df.columns.str.replace('\ufeff', '', regex=False)
        df.columns = df.columns.str.replace('\xa0', ' ', regex=False).str.strip()
        df.columns = df.columns.str.strip()
        df.replace('', pd.NA, inplace=True)
        df.fillna('', inplace=True)
        print(f"✓ CSV eingelesen: {len(df)} Zeilen")
    except Exception as e:
        print(f"✗ FEHLER: {e}")
        return False
    
    # Datentypen konvertieren
    price_cols = ['Gesamteinzelhandelspreis', 'Versandkosten']
    for col in price_cols:
        if col in df.columns:
            df[col] = df[col].apply(_clean_price)
    df['Gekaufte Menge'] = pd.to_numeric(df['Gekaufte Menge'], errors='coerce').fillna(0)
    df['Netto_Einzelpreis'] = df.apply(
        lambda row: row['Gesamteinzelhandelspreis'] / row['Gekaufte Menge'] if row['Gekaufte Menge'] > 0 else 0.00,
        axis=1
    )
    
    # Datenbankverbindung
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("✓ Datenbankverbindung hergestellt")
    except Exception as e:
        print(f"✗ FEHLER: {e}")
        return False
    
    # Daten importieren
    grouped_orders = df.groupby('Bestell-ID')
    imported_count = 0
    updated_count = 0
    
    for order_id, group in grouped_orders:
        order_data = group.iloc[0]
        
        vorname = str(order_data.get('Vorname des Empfängers', '')).strip()
        nachname = str(order_data.get('Nachname des Empfängers', '')).strip()
        if not vorname and not nachname:
            vorname = ''
            nachname = str(order_data.get('Name des Empfängers', '')).strip()
        
        strasse, _ = _clean_street(str(order_data.get('Versandadresse 1', '')))
        land_iso = _get_country_iso(str(order_data.get('Versandland', 'Germany')))
        kaufdatum = _format_date(str(order_data.get('Kaufdatum', '')))
        
        cursor.execute(f"SELECT id FROM {TABLE_ORDERS} WHERE bestell_id = ?", order_id)
        existing_order = cursor.fetchone()
        
        if existing_order:
            order_db_id = existing_order[0]
            temu_status = str(order_data.get('Bestellstatus', ''))
            
            if temu_status == 'Storniert':
                cursor.execute(f"""
                    UPDATE {TABLE_ORDERS} SET bestellstatus = ?, status = 'storniert', updated_at = GETDATE() WHERE id = ?
                """, temu_status, order_db_id)
                print(f"  ⚠ {order_id}: STORNIERT")
            elif temu_status in ['Versandt', 'Zugestellt']:
                cursor.execute(f"""
                    UPDATE {TABLE_ORDERS} SET bestellstatus = ?, temu_gemeldet = 1, updated_at = GETDATE() WHERE id = ?
                """, temu_status, order_db_id)
                print(f"  ✓ {order_id}: Bestätigt ({temu_status})")
            else:
                cursor.execute(f"""
                    UPDATE {TABLE_ORDERS} SET bestellstatus = ?, updated_at = GETDATE() WHERE id = ?
                """, temu_status, order_db_id)
            
            updated_count += 1
        else:
            temu_status = str(order_data.get('Bestellstatus', ''))
            db_status = 'storniert' if temu_status == 'Storniert' else 'importiert'
            is_confirmed = 1 if temu_status in ['Versandt', 'Zugestellt'] else 0
            
            cursor.execute(f"""
                INSERT INTO {TABLE_ORDERS} (
                    bestell_id, bestellstatus, kaufdatum, name_empfaenger, vorname_empfaenger, 
                    nachname_empfaenger, telefon_empfaenger, email, strasse, plz, ort, 
                    bundesland, land, land_iso, versandkosten, status, temu_gemeldet
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, 
                order_id, temu_status, kaufdatum,
                str(order_data.get('Name des Empfängers', '')),
                vorname, nachname,
                str(order_data.get('Telefonnummer des Empfängers', '')),
                str(order_data.get('Virtuelle E-Mail', '')),
                strasse,
                str(order_data.get('Versandpostleitzahl (Muss an die folgende Postleitzahl gesendet werden.)', '')),
                str(order_data.get('Versandort', '')),
                str(order_data.get('Versandbundesland', '')),
                str(order_data.get('Versandland', '')),
                land_iso,
                float(order_data.get('Versandkosten', 0)),
                db_status, is_confirmed
            )
            
            cursor.execute("SELECT @@IDENTITY")
            order_db_id = cursor.fetchone()[0]
            imported_count += 1
        
        # Artikel-Positionen
        for _, row in group.iterrows():
            bestellartikel_id = str(row.get('Bestellartikel-ID', ''))
            cursor.execute(f"SELECT id FROM {TABLE_ORDER_ITEMS} WHERE bestellartikel_id = ?", bestellartikel_id)
            if cursor.fetchone():
                continue
            
            menge = float(row.get('Gekaufte Menge', 0))
            netto_einzelpreis = float(row.get('Netto_Einzelpreis', 0))
            mwst_satz = 19.00
            brutto_einzelpreis = netto_einzelpreis * (1 + mwst_satz / 100)
            
            cursor.execute(f"""
                INSERT INTO {TABLE_ORDER_ITEMS} (
                    order_id, bestell_id, bestellartikel_id, produktname, sku, sku_id, variation,
                    menge, netto_einzelpreis, brutto_einzelpreis, gesamtpreis_netto, gesamtpreis_brutto, mwst_satz
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                order_db_id, order_id, bestellartikel_id,
                str(row.get('Produktname', '')),
                str(row.get('Beitrags-SKU', '')),
                str(row.get('SKU-ID', '')),
                str(row.get('Variation', '')),
                menge, netto_einzelpreis, brutto_einzelpreis,
                netto_einzelpreis * menge, brutto_einzelpreis * menge, mwst_satz
            )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✓ Import abgeschlossen!")
    print(f"  Neu: {imported_count} | Aktualisiert: {updated_count}")
    print(f"{'='*60}\n")
    
    return True
