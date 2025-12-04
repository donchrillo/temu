"""API Sync Service - Merged TEMU API Responses in Datenbank"""

import json
from pathlib import Path
from datetime import datetime
from src.database.connection import get_db_connection
from config.settings import TABLE_ORDERS, TABLE_ORDER_ITEMS, DB_TOCI, DATA_DIR

def import_api_responses_to_db(api_response_dir=None):
    """
    Importiert TEMU API Responses aus JSON-Dateien in die Datenbank.
    Merged Daten aus 3 API Calls:
    - bg.order.list.v2.get → Orders & Items
    - bg.order.shippinginfo.v2.get → Kundendaten & Adresse
    - bg.order.amount.query → Preise
    """
    
    if api_response_dir is None:
        api_response_dir = DATA_DIR / 'api_responses'
    
    orders_file = Path(api_response_dir) / 'api_response_orders.json'
    shipping_file = Path(api_response_dir) / 'api_response_shipping_all.json'
    amount_file = Path(api_response_dir) / 'api_response_amount_all.json'
    
    # Prüfe erforderliche Dateien
    required_files = [orders_file, shipping_file, amount_file]
    for f in required_files:
        if not f.exists():
            print(f"✗ Datei nicht gefunden: {f}")
            return False
    
    print("=" * 70)
    print("API Responses → Datenbank importieren")
    print("=" * 70)
    print(f"✓ Lese API Response Dateien\n")
    
    # Lade alle Responses
    with open(orders_file, 'r', encoding='utf-8') as f:
        orders_response = json.load(f)
    
    with open(shipping_file, 'r', encoding='utf-8') as f:
        shipping_responses = json.load(f)
    
    with open(amount_file, 'r', encoding='utf-8') as f:
        amount_responses = json.load(f)
    
    if not orders_response.get('success'):
        print("✗ Orders API Response war nicht erfolgreich")
        return False
    
    orders = orders_response.get('result', {}).get('pageItems', [])
    print(f"✓ {len(orders)} Orders geladen")
    print(f"✓ {len(shipping_responses)} Versandinformationen vorhanden")
    print(f"✓ {len(amount_responses)} Preisinformationen vorhanden\n")
    
    conn = get_db_connection(DB_TOCI)
    cursor = conn.cursor()
    
    imported_count = 0
    updated_count = 0
    
    for order_item in orders:
        parent_order_map = order_item.get('parentOrderMap', {})
        parent_order_sn = parent_order_map.get('parentOrderSn')
        
        if not parent_order_sn:
            print("⚠ Keine parentOrderSn gefunden")
            continue
        
        # ===== MERGE: Kundendaten aus shipping_info =====
        shipping_data = shipping_responses.get(parent_order_sn, {})
        shipping_result = shipping_data.get('result', {})
        
        vorname_empfaenger = ''
        nachname_empfaenger = shipping_result.get('receiptName', '') or ''
        nachname_empfaenger = nachname_empfaenger.strip()
        
        # Name splitten (Format: "Vorname Nachname")
        if nachname_empfaenger and ' ' in nachname_empfaenger:
            parts = nachname_empfaenger.rsplit(' ', 1)
            vorname_empfaenger = parts[0].strip()
            nachname_empfaenger = parts[1].strip()
        
        strasse = (shipping_result.get('addressLineAll') or '').strip()
        plz = (shipping_result.get('postCode') or '').strip()
        ort = (shipping_result.get('regionName3') or '').strip()
        bundesland = (shipping_result.get('regionName2') or '').strip()
        land = (shipping_result.get('regionName1') or '').strip()
        email = (shipping_result.get('mail') or '').strip()
        telefon = (shipping_result.get('mobile') or '').strip()
        
        # Land zu ISO konvertieren
        land_iso_map = {
            'Germany': 'DE', 'Austria': 'AT', 'France': 'FR', 'Netherlands': 'NL',
            'Poland': 'PL', 'Italy': 'IT', 'Spain': 'ES', 'Belgium': 'BE',
            'Sweden': 'SE', 'Denmark': 'DK'
        }
        land_iso = land_iso_map.get(land, 'DE')
        
        # ===== MERGE: Preise & Versandkosten aus amount_info =====
        amount_data = amount_responses.get(parent_order_sn, {})
        amount_result = amount_data.get('result', {})
        parent_amount_map = amount_result.get('parentOrderMap', {})
        order_amount_list = amount_result.get('orderList', [])
        
        # Versandkosten (in Cents, daher /100)
        versandkosten_brutto = parent_amount_map.get('shipAmountTotalTaxIncl', {}).get('amount', 0) / 100
        versandkosten_netto = parent_amount_map.get('shippingAmountTotal', {}).get('amount', 0) / 100
        
        # Bestellstatus
        order_time = parent_order_map.get('parentOrderTime', 0)
        kaufdatum = datetime.fromtimestamp(order_time) if order_time else datetime.now()
        
        parent_order_status = parent_order_map.get('parentOrderStatus', 2)
        status_map = {1: 'pending', 2: 'processing', 3: 'cancelled', 4: 'shipped', 5: 'delivered'}
        bestellstatus = status_map.get(parent_order_status, 'unknown')
        
        # ===== DB: Prüfe & Insert/Update Order =====
        cursor.execute(f"SELECT id FROM {TABLE_ORDERS} WHERE bestell_id = ?", parent_order_sn)
        existing_order = cursor.fetchone()
        
        if existing_order:
            order_db_id = existing_order[0]
            # Update
            cursor.execute(f"""
                UPDATE {TABLE_ORDERS} SET
                    bestellstatus = ?,
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
                    updated_at = GETDATE()
                WHERE id = ?
            """, bestellstatus, vorname_empfaenger, nachname_empfaenger,
                strasse, plz, ort, bundesland, land, land_iso,
                email, telefon, versandkosten_netto, order_db_id)
            updated_count += 1
            print(f"  ↻ {parent_order_sn}: aktualisiert")
        else:
            # Insert neue Bestellung
            cursor.execute(f"""
                INSERT INTO {TABLE_ORDERS} (
                    bestell_id, bestellstatus, kaufdatum,
                    vorname_empfaenger, nachname_empfaenger,
                    strasse, plz, ort, bundesland, land, land_iso,
                    email, telefon_empfaenger,
                    versandkosten, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'importiert')
            """, parent_order_sn, bestellstatus, kaufdatum,
                vorname_empfaenger, nachname_empfaenger,
                strasse, plz, ort, bundesland, land, land_iso,
                email, telefon, versandkosten_netto)
            
            cursor.execute("SELECT @@IDENTITY")
            order_db_id = cursor.fetchone()[0]
            imported_count += 1
            print(f"  ✓ {parent_order_sn}: neu importiert")
        
        # ===== DB: Insert Order Items mit Preisen =====
        order_list = order_item.get('orderList', [])
        
        for item_idx, order in enumerate(order_list):
            bestellartikel_id = order.get('orderSn')
            
            # Prüfe ob Artikel bereits existiert
            cursor.execute(f"SELECT id FROM {TABLE_ORDER_ITEMS} WHERE bestellartikel_id = ?", bestellartikel_id)
            if cursor.fetchone():
                continue
            
            # Artikel-Daten (original = sprachunabhängig!)
            produktname = order.get('originalGoodsName', '')
            variation = order.get('originalSpecName', '')
            menge = float(order.get('originalOrderQuantity', 0))
            sku = order.get('skuId', '')
            
            # ===== Preise aus amount_info =====
            netto_einzelpreis = 0.0
            brutto_einzelpreis = 0.0
            mwst_satz = 19.00
            
            if item_idx < len(order_amount_list):
                amount_item = order_amount_list[item_idx]
                netto_einzelpreis = amount_item.get('unitRetailPriceVatExcl', {}).get('amount', 0) / 100
                brutto_einzelpreis = amount_item.get('unitRetailPriceVatIncl', {}).get('amount', 0) / 100
                mwst_satz = amount_item.get('productTaxRate', 19000000) / 1000000
            
            cursor.execute(f"""
                INSERT INTO {TABLE_ORDER_ITEMS} (
                    order_id, bestell_id, bestellartikel_id,
                    produktname, sku, variation,
                    menge, netto_einzelpreis, brutto_einzelpreis,
                    gesamtpreis_netto, gesamtpreis_brutto, mwst_satz
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                order_db_id,
                parent_order_sn,
                bestellartikel_id,
                produktname,
                sku,
                variation,
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
    
    print(f"\n{'='*70}")
    print(f"✓ API Import erfolgreich!")
    print(f"  Neue Bestellungen: {imported_count}")
    print(f"  Aktualisierte Bestellungen: {updated_count}")
    print(f"{'='*70}\n")
    
    return True
