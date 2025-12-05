"""
Validiert API-Responses VOR dem DB-Import.
Zeigt alle geparsten Daten (Orders + Kundendaten + Preise) die in die DB gehen.
"""

import json
from pathlib import Path
from datetime import datetime
from config.settings import DATA_DIR

API_RESPONSE_DIR = DATA_DIR / 'api_responses'

def validate_and_preview():
    """
    Validiert die 3 API-Response-Dateien und zeigt 
    die geparsten Daten wie sie in die DB gehen.
    """
    
    orders_file = API_RESPONSE_DIR / 'api_response_orders.json'
    shipping_file = API_RESPONSE_DIR / 'api_response_shipping_all.json'
    amount_file = API_RESPONSE_DIR / 'api_response_amount_all.json'
    
    # Dateien vorhanden?
    for f in [orders_file, shipping_file, amount_file]:
        if not f.exists():
            print(f"✗ Datei nicht gefunden: {f}")
            return False
    
    print("=" * 70)
    print("API Responses - VALIDIERUNG & PREVIEW")
    print("=" * 70)
    print(f"✓ Alle 3 Dateien vorhanden\n")
    
    # Lade alle Responses
    with open(orders_file, 'r', encoding='utf-8') as f:
        orders_response = json.load(f)
    
    with open(shipping_file, 'r', encoding='utf-8') as f:
        shipping_responses = json.load(f)
    
    with open(amount_file, 'r', encoding='utf-8') as f:
        amount_responses = json.load(f)
    
    if not orders_response.get('success'):
        print("✗ Orders Response nicht erfolgreich")
        return False
    
    orders = orders_response.get('result', {}).get('pageItems', [])
    print(f"✓ {len(orders)} Orders geladen")
    print(f"✓ {len(shipping_responses)} Versandinformationen vorhanden")
    print(f"✓ {len(amount_responses)} Preisinformationen vorhanden")
    print(f"\n{'='*70}\n")
    
    # Validiere ALLE Orders
    valid_count = 0
    invalid_count = 0
    errors = []
    
    for i, order_item in enumerate(orders, 1):
        parent_order_map = order_item.get('parentOrderMap', {})
        parent_order_sn = parent_order_map.get('parentOrderSn')
        
        if not parent_order_sn:
            print(f"[{i}] ✗ Keine parentOrderSn - ÜBERSPRUNGEN")
            invalid_count += 1
            continue
        
        # ===== MERGE: Kundendaten =====
        shipping_data = shipping_responses.get(parent_order_sn, {})
        shipping_result = shipping_data.get('result', {})
        
        vorname = ''
        nachname = shipping_result.get('receiptName', '').strip()
        if nachname and ' ' in nachname:
            parts = nachname.rsplit(' ', 1)
            vorname = parts[0].strip()
            nachname = parts[1].strip()
        
        strasse = shipping_result.get('addressLineAll', '').strip()
        plz = shipping_result.get('postCode', '').strip()
        ort = shipping_result.get('regionName3', '').strip()
        email = shipping_result.get('mail', '').strip()
        
        # ===== MERGE: Preise =====
        amount_data = amount_responses.get(parent_order_sn, {})
        amount_result = amount_data.get('result', {})
        parent_amount_map = amount_result.get('parentOrderMap', {})
        order_amount_list = amount_result.get('orderList', [])
        
        versandkosten_netto = parent_amount_map.get('shippingAmountTotal', {}).get('amount', 0) / 100
        
        # ===== Validierung =====
        order_list = order_item.get('orderList', [])
        item_errors = []
        
        # Prüfe Kundendaten
        if not nachname:
            item_errors.append("Kein Empfängername")
        if not strasse:
            item_errors.append("Keine Straße")
        if not plz:
            item_errors.append("Keine PLZ")
        if not order_list:
            item_errors.append("Keine Artikel")
        
        # Prüfe Artikel
        for idx, order in enumerate(order_list):
            produktname = order.get('originalGoodsName', '')
            menge = float(order.get('originalOrderQuantity', 0))
            
            if not produktname:
                item_errors.append(f"  Artikel {idx+1}: Keine originalGoodsName")
            if menge <= 0:
                item_errors.append(f"  Artikel {idx+1}: Ungültige Menge")
        
        if item_errors:
            print(f"[{i}] ✗ {parent_order_sn}")
            for error in item_errors:
                print(f"    {error}")
            invalid_count += 1
            errors.extend([f"{parent_order_sn}: {e}" for e in item_errors])
        else:
            print(f"[{i}] ✓ {parent_order_sn}")
            valid_count += 1
            
            # Zeige GEPARSTE DATEN
            print(f"    ┌─ KUNDENDATEN:")
            print(f"    │  Name: {vorname} {nachname}")
            print(f"    │  Adresse: {strasse}, {plz} {ort}")
            print(f"    │  Email: {email}")
            print(f"    ├─ VERSAND:")
            print(f"    │  Kosten (netto): {versandkosten_netto:.2f}€")
            print(f"    ├─ ARTIKEL:")
            
            for idx, order in enumerate(order_list, 1):
                produktname = order.get('originalGoodsName', '')
                variation = order.get('originalSpecName', '')
                menge = float(order.get('originalOrderQuantity', 0))
                sku_id = order.get('skuId', '')
                
                # Extrahiere SKU aus productList
                sku = ''
                product_list = order.get('productList', [])
                if product_list and len(product_list) > 0:
                    sku = product_list[0].get('extCode', '')
                
                # Preis aus amount_list
                if idx-1 < len(order_amount_list):
                    amount_item = order_amount_list[idx-1]
                    netto = amount_item.get('unitRetailPriceVatExcl', {}).get('amount', 0) / 100
                    brutto = amount_item.get('unitRetailPriceVatIncl', {}).get('amount', 0) / 100
                else:
                    netto = 0.0
                    brutto = 0.0
                
                print(f"    │  {idx}. {produktname}")
                print(f"    │     Variation: {variation}")
                print(f"    │     Menge: {menge}x")
                print(f"    │     SKU: {sku}")
                print(f"    │     SKU-ID: {sku_id}")
                print(f"    │     Preis: {netto:.2f}€ (netto) / {brutto:.2f}€ (brutto)")
            
            print(f"    └─ STATUS: OK - Bereit für DB-Import")
            print()
    
    # ===== ZUSAMMENFASSUNG =====
    print("=" * 70)
    print("VALIDIERUNGSERGEBNIS")
    print("=" * 70)
    print(f"✓ Valide Orders: {valid_count}")
    print(f"✗ Fehlerhafte Orders: {invalid_count}")
    
    if errors:
        print(f"\nFEHLER ({len(errors)}):")
        for error in errors:
            print(f"  • {error}")
        print("\n⚠️ Es gibt {len(errors)} Fehler!")
        return False
    
    print(f"\n✓ Alle {valid_count} Orders sind valid!")
    print("Führe folgendes aus um zu importieren:")
    print("  python -m workflows.api_to_db")
    print("=" * 70 + "\n")
    
    return True

if __name__ == "__main__":
    import sys
    success = validate_and_preview()
    sys.exit(0 if success else 1)
