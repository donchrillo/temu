import pandas as pd
import pyodbc
from datetime import datetime
import re
import os
from dotenv import load_dotenv

# .env laden
load_dotenv()

# --- EINSTELLUNGEN ---
CSV_DATEINAME = os.getenv('CSV_INPUT_PATH', 'order_export.csv')

# SQL Server Verbindung
SQL_SERVER = os.getenv('SQL_SERVER')
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')

# Datenbanknamen (fest im Code)
DB_TOCI = 'toci'

TABLE_ORDERS = os.getenv('TABLE_ORDERS', 'temu_orders')
TABLE_ORDER_ITEMS = os.getenv('TABLE_ORDER_ITEMS', 'temu_order_items')

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
    """Konvertiert das TEMU Datumsformat in ein datetime-Objekt."""
    cleaned_date = re.sub(r'\sUhr\sCET\(UTC[+-]\d+\)', '', date_str).strip()
    try:
        return datetime.strptime(cleaned_date, '%d. %b. %Y, %H:%M')
    except Exception:
        try:
            return datetime.strptime(cleaned_date.replace('.', ''), '%d %b %Y, %H:%M')
        except:
            return datetime.now()

def _clean_street(address_line):
    """Trennt Straße und Hausnummer."""
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
    """Konvertiert Ländernamen in ISO-Code."""
    mapping = {
        'Germany': 'DE',
        'Austria': 'AT',
        'France': 'FR',
        'Netherlands': 'NL'
    }
    return mapping.get(country_name, 'DE')

def get_db_connection():
    """Erstellt SQL Server Verbindung zur TOCI Datenbank."""
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
        raise Exception("Kein SQL Server ODBC-Treiber gefunden! Bitte installieren Sie 'ODBC Driver 18 for SQL Server'")
    
    print(f"  Verwende Treiber: {driver}")
    
    conn_str = (
        f'DRIVER={{{driver}}};'
        f'SERVER={SQL_SERVER};'
        f'DATABASE={DB_TOCI};'
        f'UID={SQL_USERNAME};'
        f'PWD={SQL_PASSWORD};'
        f'TrustServerCertificate=yes;'
    )
    return pyodbc.connect(conn_str)

# --- HAUPTFUNKTION ---

def import_csv_to_database(csv_file):
    """Liest TEMU CSV und importiert in SQL-Datenbank."""
    
    print("=" * 60)
    print("TEMU CSV zu SQL Datenbank Import")
    print("=" * 60)
    
    # 1. CSV einlesen
    try:
        df = pd.read_csv(csv_file, delimiter=',', quotechar='"', encoding='utf-8-sig', dtype=str, keep_default_na=False)
        
        # Spaltennamen bereinigen
        df.columns = df.columns.str.replace('\ufeff', '', regex=False)
        df.columns = df.columns.str.replace('\xa0', ' ', regex=False).str.strip()
        df.columns = df.columns.str.strip()
        
        df.replace('', pd.NA, inplace=True)
        df.fillna('', inplace=True)
        
        print(f"✓ CSV erfolgreich eingelesen: {len(df)} Zeilen")
        
    except Exception as e:
        print(f"✗ FEHLER beim Einlesen der CSV: {e}")
        return False

    # 2. Datentypen konvertieren
    price_cols = ['Gesamteinzelhandelspreis', 'Versandkosten']
    for col in price_cols:
        if col in df.columns:
            df[col] = df[col].apply(_clean_price)
    
    df['Gekaufte Menge'] = pd.to_numeric(df['Gekaufte Menge'], errors='coerce').fillna(0)
    
    # Netto-Einzelpreis berechnen
    df['Netto_Einzelpreis'] = df.apply(
        lambda row: row['Gesamteinzelhandelspreis'] / row['Gekaufte Menge'] 
        if row['Gekaufte Menge'] > 0 else 0.00,
        axis=1
    )
    
    # 3. Datenbankverbindung
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("✓ SQL Server Verbindung hergestellt")
    except Exception as e:
        print(f"✗ FEHLER bei SQL-Verbindung: {e}")
        return False
    
    # 4. Daten gruppieren und importieren
    grouped_orders = df.groupby('Bestell-ID')
    imported_count = 0
    updated_count = 0
    
    for order_id, group in grouped_orders:
        order_data = group.iloc[0]
        
        # Namenslogik
        vorname = str(order_data.get('Vorname des Empfängers', '')).strip()
        nachname = str(order_data.get('Nachname des Empfängers', '')).strip()
        
        if not vorname and not nachname:
            vorname = ''
            nachname = str(order_data.get('Name des Empfängers', '')).strip()
        
        # Adresse
        strasse, _ = _clean_street(str(order_data.get('Versandadresse 1', '')))
        land_iso = _get_country_iso(str(order_data.get('Versandland', 'Germany')))
        kaufdatum = _format_date(str(order_data.get('Kaufdatum', '')))
        
        # Prüfen ob Bestellung bereits existiert
        cursor.execute(f"SELECT id FROM {TABLE_ORDERS} WHERE bestell_id = ?", order_id)
        existing_order = cursor.fetchone()
        
        if existing_order:
            # Update existierende Bestellung
            order_db_id = existing_order[0]
            
            # Status von TEMU prüfen
            temu_status = str(order_data.get('Bestellstatus', ''))
            
            # Stornierte Bestellungen
            if temu_status == 'Storniert':
                cursor.execute(f"""
                    UPDATE {TABLE_ORDERS} SET
                        bestellstatus = ?,
                        status = 'storniert',
                        updated_at = GETDATE()
                    WHERE id = ?
                """, temu_status, order_db_id)
                print(f"  ⚠ {order_id}: STORNIERT - Bitte in JTL manuell stornieren!")
            # Wenn in TEMU als "Versandt" oder "Zugestellt" markiert → temu_gemeldet = 1
            elif temu_status in ['Versandt', 'Zugestellt']:
                cursor.execute(f"""
                    UPDATE {TABLE_ORDERS} SET
                        bestellstatus = ?,
                        temu_gemeldet = 1,
                        updated_at = GETDATE()
                    WHERE id = ?
                """, temu_status, order_db_id)
                print(f"  ✓ {order_id}: Von TEMU bestätigt ({temu_status})")
            else:
                cursor.execute(f"""
                    UPDATE {TABLE_ORDERS} SET
                        bestellstatus = ?,
                        updated_at = GETDATE()
                    WHERE id = ?
                """, temu_status, order_db_id)
            
            updated_count += 1
        else:
            # Neue Bestellung einfügen
            temu_status = str(order_data.get('Bestellstatus', ''))
            
            # Stornierte Bestellungen direkt mit Status 'storniert' importieren
            if temu_status == 'Storniert':
                db_status = 'storniert'
                is_confirmed = 0
                print(f"  ⚠ {order_id}: STORNIERT - Wird nicht nach JTL exportiert")
            # Bereits versendete/zugestellte Bestellungen
            elif temu_status in ['Versandt', 'Zugestellt']:
                db_status = 'importiert'
                is_confirmed = 1
            # Normale neue Bestellungen
            else:
                db_status = 'importiert'
                is_confirmed = 0
            
            cursor.execute(f"""
                INSERT INTO {TABLE_ORDERS} (
                    bestell_id, bestellstatus, kaufdatum,
                    name_empfaenger, vorname_empfaenger, nachname_empfaenger,
                    telefon_empfaenger, email,
                    strasse, plz, ort, bundesland, land, land_iso,
                    versandkosten, status, temu_gemeldet
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, 
                order_id,
                temu_status,
                kaufdatum,
                str(order_data.get('Name des Empfängers', '')),
                vorname,
                nachname,
                str(order_data.get('Telefonnummer des Empfängers', '')),
                str(order_data.get('Virtuelle E-Mail', '')),
                strasse,
                str(order_data.get('Versandpostleitzahl (Muss an die folgende Postleitzahl gesendet werden.)', '')),
                str(order_data.get('Versandort', '')),
                str(order_data.get('Versandbundesland', '')),
                str(order_data.get('Versandland', '')),
                land_iso,
                float(order_data.get('Versandkosten', 0)),
                db_status,
                is_confirmed
            )
            
            cursor.execute("SELECT @@IDENTITY")
            order_db_id = cursor.fetchone()[0]
            imported_count += 1
        
        # Artikel-Positionen einfügen
        for _, row in group.iterrows():
            bestellartikel_id = str(row.get('Bestellartikel-ID', ''))
            
            # Prüfen ob Artikel bereits existiert
            cursor.execute(f"SELECT id FROM {TABLE_ORDER_ITEMS} WHERE bestellartikel_id = ?", bestellartikel_id)
            if cursor.fetchone():
                continue  # Artikel existiert bereits
            
            menge = float(row.get('Gekaufte Menge', 0))
            netto_einzelpreis = float(row.get('Netto_Einzelpreis', 0))
            mwst_satz = 19.00
            brutto_einzelpreis = netto_einzelpreis * (1 + mwst_satz / 100)
            
            cursor.execute(f"""
                INSERT INTO {TABLE_ORDER_ITEMS} (
                    order_id, bestell_id, bestellartikel_id,
                    produktname, sku, sku_id, variation,
                    menge, netto_einzelpreis, brutto_einzelpreis,
                    gesamtpreis_netto, gesamtpreis_brutto, mwst_satz
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                order_db_id,
                order_id,
                bestellartikel_id,
                str(row.get('Produktname', '')),
                str(row.get('Beitrags-SKU', '')),
                str(row.get('SKU-ID', '')),
                str(row.get('Variation', '')),
                menge,
                netto_einzelpreis,
                brutto_einzelpreis,
                netto_einzelpreis * menge,
                brutto_einzelpreis * menge,
                mwst_satz
            )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✓ Import erfolgreich abgeschlossen!")
    print(f"  Neue Bestellungen: {imported_count}")
    print(f"  Aktualisierte Bestellungen: {updated_count}")
    print(f"{'='*60}\n")
    
    return True


# --- HAUPTPROGRAMM ---
if __name__ == "__main__":
    result = import_csv_to_database(CSV_DATEINAME)
    
    if not result:
        print("\n✗ Import fehlgeschlagen!")
        exit(1)