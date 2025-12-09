"""Order Service - Business Logic Layer"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from config.settings import DATA_DIR
from src.db.repositories.order_repository import OrderRepository, Order
from src.db.repositories.order_item_repository import OrderItemRepository, OrderItem

class OrderService:
    """Business Logic - Importiert API Responses mit Merge-Logik"""
    
    def __init__(self, order_repo: OrderRepository = None, item_repo: OrderItemRepository = None):
        self.order_repo = order_repo or OrderRepository()
        self.item_repo = item_repo or OrderItemRepository()
        self.api_response_dir = DATA_DIR / 'api_responses'
    
    def import_from_json_files(self) -> Dict:
        """
        Importiert Orders aus JSON Files mit kompletter Merge-Logik
        MIT CONNECTION POOLING!
        
        Merged Daten aus 3 API Calls:
        - api_response_orders.json → Orders & Items
        - api_response_shipping_all.json → Kundendaten & Adresse
        - api_response_amount_all.json → Preise
        
        Returns:
            dict mit imported/updated/total counts
        """
        
        # Lade alle JSON Responses
        orders_file = self.api_response_dir / 'api_response_orders.json'
        shipping_file = self.api_response_dir / 'api_response_shipping_all.json'
        amount_file = self.api_response_dir / 'api_response_amount_all.json'
        
        # Validiere Dateien
        required_files = [orders_file, shipping_file, amount_file]
        for f in required_files:
            if not f.exists():
                print(f"✗ Datei nicht gefunden: {f}")
                return {'imported': 0, 'updated': 0, 'total': 0}
        
        # Lade Responses
        with open(orders_file, 'r', encoding='utf-8') as f:
            orders_response = json.load(f)
        
        with open(shipping_file, 'r', encoding='utf-8') as f:
            shipping_responses = json.load(f)
        
        with open(amount_file, 'r', encoding='utf-8') as f:
            amount_responses = json.load(f)
        
        # Validiere Orders Response
        if not orders_response.get('success'):
            print("✗ Orders API Response war nicht erfolgreich")
            return {'imported': 0, 'updated': 0, 'total': 0}
        
        orders = orders_response.get('result', {}).get('pageItems', [])
        print(f"✓ {len(orders)} Orders geladen")
        print(f"✓ {len(shipping_responses)} Versandinformationen vorhanden")
        print(f"✓ {len(amount_responses)} Preisinformationen vorhanden\n")
        
        # ===== IMPORT mit vollständiger Merge-Logik =====
        # ===== WICHTIG: Hole gepoolte Connection EINMAL! =====
        from src.db.connection import get_db_connection
        pooled_conn = get_db_connection(database='toci', use_pool=True)
        
        # Injiziere pooled Connection in Repositories
        order_repo_with_pool = OrderRepository(connection=pooled_conn)
        item_repo_with_pool = OrderItemRepository(connection=pooled_conn)
        
        # Nutze Repositories mit gepoolter Connection
        result = self.import_from_api_response(
            orders,
            shipping_responses,
            amount_responses,
            order_repo_with_pool,
            item_repo_with_pool
        )
        
        return result
    
    def import_from_api_response(self, orders: list, shipping_responses: dict, 
                                 amount_responses: dict,
                                 order_repo=None, item_repo=None) -> Dict:
        """
        Business Logic: Merge + Import Orders
        MIT optionalen Repositories (für gepoolte Connections)
        
        Args:
            orders: List von Orders aus API
            shipping_responses: Dict mit Versandinformationen (parentOrderSn -> response)
            amount_responses: Dict mit Preisinformationen (parentOrderSn -> response)
        
        Returns:
            dict mit import statistics
        """
        
        if order_repo is None:
            order_repo = self.order_repo
        if item_repo is None:
            item_repo = self.item_repo
        
        imported_count = 0
        updated_count = 0
        
        for order_item in orders:
            try:
                parent_order_map = order_item.get('parentOrderMap', {})
                parent_order_sn = parent_order_map.get('parentOrderSn')
                
                if not parent_order_sn:
                    print("⚠ Keine parentOrderSn gefunden")
                    continue
                
                # ===== MERGE STEP 1: Kundendaten aus shipping_info =====
                shipping_data = shipping_responses.get(parent_order_sn, {})
                shipping_result = shipping_data.get('result', {})
                
                # Parse Name (Format: "Vorname Nachname")
                vorname_empfaenger = ''
                nachname_empfaenger = (shipping_result.get('receiptName', '') or '').strip()
                
                if nachname_empfaenger and ' ' in nachname_empfaenger:
                    parts = nachname_empfaenger.rsplit(' ', 1)
                    vorname_empfaenger = parts[0].strip()
                    nachname_empfaenger = parts[1].strip()
                
                # Adressdaten
                strasse = (shipping_result.get('addressLineAll') or '').strip()
                plz = (shipping_result.get('postCode') or '').strip()
                ort = (shipping_result.get('regionName3') or '').strip()
                bundesland = (shipping_result.get('regionName2') or '').strip()
                land = (shipping_result.get('regionName1') or '').strip()
                email = (shipping_result.get('mail') or '').strip()
                telefon = (shipping_result.get('mobile') or '').strip()
                
                # Land zu ISO konvertieren
                land_iso = self._map_land_to_iso(land)
                
                # ===== MERGE STEP 2: Amount Daten (Preise & Versandkosten) =====
                amount_data = amount_responses.get(parent_order_sn, {})
                amount_result = amount_data.get('result', {})
                parent_amount_map = amount_result.get('parentOrderMap', {})
                order_amount_list = amount_result.get('orderList', [])
                
                # Versandkosten (in Cents, daher /100)
                versandkosten_brutto = parent_amount_map.get('shipAmountTotalTaxIncl', {}).get('amount', 0) / 100
                versandkosten_netto = parent_amount_map.get('shippingAmountTotal', {}).get('amount', 0) / 100
                
                # Status & Datum
                order_time = parent_order_map.get('parentOrderTime', 0)
                kaufdatum = datetime.fromtimestamp(order_time) if order_time else datetime.now()
                
                parent_order_status = parent_order_map.get('parentOrderStatus', 2)
                bestellstatus = self._map_order_status(parent_order_status)
                
                # ===== BUSINESS LOGIC: Prüfe ob Order existiert =====
                existing_order = order_repo.find_by_bestell_id(parent_order_sn)
                
                if existing_order:
                    # UPDATE Order
                    order_db_id = existing_order.id
                    order = Order(
                        id=order_db_id,
                        bestell_id=parent_order_sn,
                        bestellstatus=bestellstatus,
                        kaufdatum=kaufdatum,
                        vorname_empfaenger=vorname_empfaenger,
                        nachname_empfaenger=nachname_empfaenger,
                        strasse=strasse,
                        plz=plz,
                        ort=ort,
                        bundesland=bundesland,
                        land=land,
                        land_iso=land_iso,
                        email=email,
                        telefon_empfaenger=telefon,
                        versandkosten=versandkosten_netto,
                        status='importiert'
                    )
                    order_repo.save(order)
                    updated_count += 1
                    print(f"  ↻ {parent_order_sn}: aktualisiert")
                else:
                    # INSERT neue Order
                    order = Order(
                        id=None,
                        bestell_id=parent_order_sn,
                        bestellstatus=bestellstatus,
                        kaufdatum=kaufdatum,
                        vorname_empfaenger=vorname_empfaenger,
                        nachname_empfaenger=nachname_empfaenger,
                        strasse=strasse,
                        plz=plz,
                        ort=ort,
                        bundesland=bundesland,
                        land=land,
                        land_iso=land_iso,
                        email=email,
                        telefon_empfaenger=telefon,
                        versandkosten=versandkosten_netto,
                        status='importiert'
                    )
                    order_db_id = order_repo.save(order)
                    imported_count += 1
                    print(f"  ✓ {parent_order_sn}: neu importiert")
                
                # ===== BUSINESS LOGIC: Import Order Items mit Preisen =====
                order_list = order_item.get('orderList', [])
                
                for item_idx, order_item_data in enumerate(order_list):
                    bestellartikel_id = order_item_data.get('orderSn')
                    
                    if not bestellartikel_id:
                        continue
                    
                    # Artikel-Daten (original = sprachunabhängig!)
                    produktname = order_item_data.get('originalGoodsName', '')
                    variation = order_item_data.get('originalSpecName', '')
                    menge = float(order_item_data.get('originalOrderQuantity', 0))
                    sku_id = order_item_data.get('skuId', '')
                    
                    # Extract SKU aus productList
                    sku = ''
                    product_list = order_item_data.get('productList', [])
                    if product_list and len(product_list) > 0:
                        sku = product_list[0].get('extCode', '')
                    
                    # ===== MERGE STEP 3: Preise aus Amount Response =====
                    netto_einzelpreis = 0.0
                    brutto_einzelpreis = 0.0
                    mwst_satz = 19.00
                    
                    if item_idx < len(order_amount_list):
                        amount_item = order_amount_list[item_idx]
                        # Preise sind in Cents, daher /100
                        netto_einzelpreis = amount_item.get('unitRetailPriceVatExcl', {}).get('amount', 0) / 100
                        brutto_einzelpreis = amount_item.get('unitRetailPriceVatIncl', {}).get('amount', 0) / 100
                        # MwSt ist in Millionsten, daher /1000000
                        mwst_satz = amount_item.get('productTaxRate', 19000000) / 1000000
                    
                    # Prüfe ob Artikel bereits existiert
                    existing_item = item_repo.find_by_bestellartikel_id(bestellartikel_id)
                    
                    if existing_item:
                        # UPDATE Item
                        item = OrderItem(
                            id=existing_item.id,
                            order_id=order_db_id,
                            bestell_id=parent_order_sn,
                            bestellartikel_id=bestellartikel_id,
                            produktname=produktname,
                            sku=sku,
                            sku_id=sku_id,
                            variation=variation,
                            menge=menge,
                            netto_einzelpreis=netto_einzelpreis,
                            brutto_einzelpreis=brutto_einzelpreis,
                            gesamtpreis_netto=netto_einzelpreis * menge,
                            gesamtpreis_brutto=brutto_einzelpreis * menge,
                            mwst_satz=mwst_satz
                        )
                        item_repo.save(item)
                    else:
                        # INSERT neuer Item
                        item = OrderItem(
                            id=None,
                            order_id=order_db_id,
                            bestell_id=parent_order_sn,
                            bestellartikel_id=bestellartikel_id,
                            produktname=produktname,
                            sku=sku,
                            sku_id=sku_id,
                            variation=variation,
                            menge=menge,
                            netto_einzelpreis=netto_einzelpreis,
                            brutto_einzelpreis=brutto_einzelpreis,
                            gesamtpreis_netto=netto_einzelpreis * menge,
                            gesamtpreis_brutto=brutto_einzelpreis * menge,
                            mwst_satz=mwst_satz
                        )
                        item_repo.save(item)
            
            except Exception as e:
                print(f"  ✗ Fehler bei Order {parent_order_sn}: {e}")
                import traceback
                traceback.print_exc()
        
        return {
            'imported': imported_count,
            'updated': updated_count,
            'total': imported_count + updated_count
        }
    
    def _map_order_status(self, status_code: int) -> str:
        """Mappt TEMU Status Code zu Status String"""
        status_map = {
            1: 'pending',
            2: 'processing',
            3: 'cancelled',
            4: 'shipped',
            5: 'delivered'
        }
        return status_map.get(status_code, 'unknown')
    
    def _map_land_to_iso(self, land: str) -> str:
        """Mappt Land-Namen zu ISO-2 Code"""
        land_iso_map = {
            'Germany': 'DE',
            'Austria': 'AT',
            'France': 'FR',
            'Netherlands': 'NL',
            'Poland': 'PL',
            'Italy': 'IT',
            'Spain': 'ES',
            'Belgium': 'BE',
            'Sweden': 'SE',
            'Denmark': 'DK',
            'United Kingdom': 'GB',
            'Switzerland': 'CH',
            'Czech Republic': 'CZ',
            'Hungary': 'HU',
            'Romania': 'RO',
            'Bulgaria': 'BG',
            'Greece': 'GR',
            'Portugal': 'PT'
        }
        return land_iso_map.get(land, 'DE')
