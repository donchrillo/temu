"""Order Service - Business Logic Layer"""

import json
import traceback
from datetime import datetime
from typing import Dict, Optional

from modules.shared.config.settings import DB_TOCI
from .config import (
    TEMU_API_RESPONSES_DIR,
    AMOUNT_DIVISOR, TAX_RATE_DIVISOR, DEFAULT_TAX_RATE_RAW, DEFAULT_TAX_RATE_PERCENT,
    ORDER_STATUS_MAP, LAND_ISO_MAP,
)
from modules.shared import db_connect
from modules.shared.database.repositories.temu.order_repository import OrderRepository, Order
from modules.shared.database.repositories.temu.order_item_repository import OrderItemRepository, OrderItem
from modules.shared import log_service

class OrderService:
    """Business Logic - Importiert API Responses mit Merge-Logik"""
    
    def __init__(self, order_repo: OrderRepository = None, item_repo: OrderItemRepository = None, job_id: Optional[str] = None):
        self.order_repo = order_repo or OrderRepository()
        self.item_repo = item_repo or OrderItemRepository()
        self.api_response_dir = TEMU_API_RESPONSES_DIR
        self.job_id = job_id  # Optional für Logging
    
    def _load_json_responses(self, job_id: Optional[str] = None) -> Optional[tuple]:
        """
        Lädt und validiert die 3 JSON API Response Files.
        
        Returns:
            Tuple (orders, shipping_responses, amount_responses) oder None bei Fehler.
        """
        orders_file = self.api_response_dir / 'api_response_orders.json'
        shipping_file = self.api_response_dir / 'api_response_shipping_all.json'
        amount_file = self.api_response_dir / 'api_response_amount_all.json'
        
        for f in [orders_file, shipping_file, amount_file]:
            if not f.exists():
                log_service.log(job_id, "order_service", "ERROR", f"✗ Datei nicht gefunden: {f}")
                return None
        
        with open(orders_file, 'r', encoding='utf-8') as f:
            orders_response = json.load(f)
        with open(shipping_file, 'r', encoding='utf-8') as f:
            shipping_responses = json.load(f)
        with open(amount_file, 'r', encoding='utf-8') as f:
            amount_responses = json.load(f)
        
        if not orders_response.get('success'):
            log_service.log(job_id, "order_service", "ERROR", "✗ Orders API Response war nicht erfolgreich")
            return None
        
        orders = orders_response.get('result', {}).get('pageItems', [])
        log_service.log(job_id, "order_service", "INFO", f"  {len(orders)} Orders gefunden")
        
        return orders, shipping_responses, amount_responses
    
    def import_from_json_files(self, job_id: Optional[str] = None,
                               order_repo=None, item_repo=None) -> Dict:
        """
        Importiert Orders aus JSON Files mit kompletter Merge-Logik.
        
        Kann standalone (eigene Transaktion) oder mit injizierten Repos
        (shared Transaktion vom Workflow) genutzt werden.
        
        Args:
            job_id: Optional - für strukturiertes Logging
            order_repo: Optional - injiziertes Repo (shared Connection)
            item_repo: Optional - injiziertes Repo (shared Connection)
        
        Returns:
            dict mit imported/updated/errors/total counts
        """
        empty_result = {'imported': 0, 'updated': 0, 'errors': 0, 'total': 0}
        job_id = job_id or self.job_id
        log_service.log(job_id, "order_service", "INFO", 
                          "→ Importiere Orders aus JSON in Datenbank")
        
        try:
            loaded = self._load_json_responses(job_id)
            if loaded is None:
                return empty_result
            
            orders, shipping_responses, amount_responses = loaded
            
            # Wenn Repos injiziert → shared Transaktion (Workflow-Modus)
            if order_repo and item_repo:
                result = self.import_from_api_response(
                    orders, shipping_responses, amount_responses,
                    order_repo=order_repo, item_repo=item_repo, job_id=job_id
                )
            else:
                # Standalone-Modus → eigene Transaktion
                with db_connect(DB_TOCI) as pooled_conn:
                    result = self.import_from_api_response(
                        orders, shipping_responses, amount_responses,
                        order_repo=OrderRepository(connection=pooled_conn),
                        item_repo=OrderItemRepository(connection=pooled_conn),
                        job_id=job_id
                    )
            
            log_service.log(job_id, "order_service", "INFO", 
                              f"✓ Import abgeschlossen: {result.get('total', 0)} Orders")
            log_service.log(job_id, "order_service", "INFO", 
                              f"  Neu: {result.get('imported', 0)}, Aktualisiert: {result.get('updated', 0)}")
            
            return result
        
        except Exception as e:
            error_trace = traceback.format_exc()
            log_service.log(job_id, "order_service", "ERROR", f"✗ Import Fehler: {str(e)}", error_text=error_trace)
            return empty_result
    
    def import_from_api_response(self, orders: list, shipping_responses: dict, 
                                 amount_responses: dict,
                                 order_repo=None, item_repo=None,
                                 job_id: Optional[str] = None) -> Dict:
        """
        Business Logic: Merge + Import Orders.
        Verwendet die übergebenen Repositories (wichtig für Transaktionen).
        
        Returns:
            dict mit imported/updated/errors/total counts
        """
        if order_repo is None:
            order_repo = self.order_repo
        if item_repo is None:
            item_repo = self.item_repo
        
        imported_count = 0
        updated_count = 0
        error_count = 0
        
        for order_item in orders:
            try:
                parent_order_map = order_item.get('parentOrderMap', {})
                parent_order_sn = parent_order_map.get('parentOrderSn')
                
                if not parent_order_sn:
                    log_service.log(job_id, "order_service", "WARNING", 
                                      "⚠ Keine parentOrderSn gefunden")
                    error_count += 1
                    continue
                
                # Step 1: Shipping/Kundendaten parsen
                shipping = self._parse_shipping_data(shipping_responses, parent_order_sn)
                
                # Step 2: Amount/Preisdaten parsen
                amount = self._parse_amount_data(amount_responses, parent_order_sn)
                
                # Order-Metadaten
                order_time = parent_order_map.get('parentOrderTime', 0)
                kaufdatum = datetime.fromtimestamp(order_time) if order_time else datetime.now()
                bestellstatus = self._map_order_status(
                    parent_order_map.get('parentOrderStatus', 2)
                )
                
                # Step 3: Order upsert
                order_db_id, is_new = self._upsert_order(
                    order_repo, parent_order_sn, shipping,
                    bestellstatus, kaufdatum, amount['versandkosten_netto'],
                    job_id
                )
                
                if is_new:
                    imported_count += 1
                else:
                    updated_count += 1
                
                # Step 4: Items upsert
                order_list = order_item.get('orderList', [])
                self._upsert_order_items(
                    item_repo, order_db_id, parent_order_sn,
                    order_list, amount['order_amount_list']
                )
            
            except Exception as e:
                error_trace = traceback.format_exc()
                psn = order_item.get('parentOrderMap', {}).get('parentOrderSn', 'unknown')
                log_service.log(job_id, "order_service", "ERROR", 
                                  f"✗ Fehler bei Order {psn}: {str(e)}", error_text=error_trace)
                error_count += 1

        return {
            'imported': imported_count,
            'updated': updated_count,
            'errors': error_count,
            'total': imported_count + updated_count
        }
    
    # ═══════════════════════════════════════════════════════════════
    # HELPER: Daten-Extraktion aus API Responses
    # ═══════════════════════════════════════════════════════════════
    
    def _parse_shipping_data(self, shipping_responses: dict, parent_order_sn: str) -> Dict:
        """Extrahiert Kunden- und Adressdaten aus Shipping Response."""
        shipping_data = shipping_responses.get(parent_order_sn, {})
        shipping_result = shipping_data.get('result', {})
        
        vorname = ''
        nachname = (shipping_result.get('receiptName', '') or '').strip()
        
        if nachname and ' ' in nachname:
            parts = nachname.rsplit(' ', 1)
            vorname = parts[0].strip()
            nachname = parts[1].strip()
        
        land = (shipping_result.get('regionName1') or '').strip()
        
        return {
            'vorname_empfaenger': vorname,
            'nachname_empfaenger': nachname,
            'strasse': (shipping_result.get('addressLineAll') or '').strip(),
            'plz': (shipping_result.get('postCode') or '').strip(),
            'ort': (shipping_result.get('regionName3') or '').strip(),
            'bundesland': (shipping_result.get('regionName2') or '').strip(),
            'land': land,
            'land_iso': self._map_land_to_iso(land),
            'email': (shipping_result.get('mail') or '').strip(),
            'telefon': (shipping_result.get('mobile') or '').strip(),
        }
    
    def _parse_amount_data(self, amount_responses: dict, parent_order_sn: str) -> Dict:
        """Extrahiert Versandkosten und Artikelpreis-Liste aus Amount Response."""
        amount_data = amount_responses.get(parent_order_sn, {})
        amount_result = amount_data.get('result', {})
        parent_amount_map = amount_result.get('parentOrderMap', {})
        
        versandkosten_netto = (
            parent_amount_map.get('shippingAmountTotal', {}).get('amount', 0) / AMOUNT_DIVISOR
        )
        
        return {
            'versandkosten_netto': versandkosten_netto,
            'order_amount_list': amount_result.get('orderList', []),
        }
    
    # ═══════════════════════════════════════════════════════════════
    # HELPER: Order & Item Upsert
    # ═══════════════════════════════════════════════════════════════
    
    def _upsert_order(
        self, order_repo, parent_order_sn: str, shipping: Dict,
        bestellstatus: str, kaufdatum: datetime, versandkosten_netto: float,
        job_id: Optional[str] = None
    ) -> tuple:
        """
        Erstellt oder aktualisiert eine Order in der DB.
        
        Returns:
            Tuple (order_db_id, is_new)
        """
        existing_order = order_repo.find_by_bestell_id(parent_order_sn)
        
        if existing_order:
            order = Order(
                id=existing_order.id,
                bestell_id=parent_order_sn,
                bestellstatus=bestellstatus,
                kaufdatum=kaufdatum,
                vorname_empfaenger=shipping['vorname_empfaenger'],
                nachname_empfaenger=shipping['nachname_empfaenger'],
                strasse=shipping['strasse'],
                adresszusatz=existing_order.adresszusatz,
                plz=shipping['plz'],
                ort=shipping['ort'],
                bundesland=shipping['bundesland'],
                land=shipping['land'],
                land_iso=shipping['land_iso'],
                email=shipping['email'],
                telefon_empfaenger=shipping['telefon'],
                versandkosten=versandkosten_netto,
                status=existing_order.status,
                xml_erstellt=existing_order.xml_erstellt,
                trackingnummer=existing_order.trackingnummer,
                versanddienstleister=existing_order.versanddienstleister
            )
            order_repo.save(order)
            log_service.log(job_id, "order_service", "INFO",
                              f"  ↻ {parent_order_sn}: aktualisiert")
            return existing_order.id, False
        
        order = Order(
            id=None,
            bestell_id=parent_order_sn,
            bestellstatus=bestellstatus,
            kaufdatum=kaufdatum,
            vorname_empfaenger=shipping['vorname_empfaenger'],
            nachname_empfaenger=shipping['nachname_empfaenger'],
            strasse=shipping['strasse'],
            plz=shipping['plz'],
            ort=shipping['ort'],
            bundesland=shipping['bundesland'],
            land=shipping['land'],
            land_iso=shipping['land_iso'],
            email=shipping['email'],
            telefon_empfaenger=shipping['telefon'],
            versandkosten=versandkosten_netto,
            status='importiert'
        )
        order_db_id = order_repo.save(order)
        
        if not order_db_id or order_db_id <= 0:
            raise ValueError(
                f"Order {parent_order_sn} konnte nicht gespeichert werden "
                f"(order_db_id={order_db_id})"
            )
        
        return order_db_id, True
    
    def _upsert_order_items(
        self, item_repo, order_db_id: int, parent_order_sn: str,
        order_list: list, order_amount_list: list
    ) -> None:
        """Importiert/aktualisiert OrderItems für eine Order."""
        for item_idx, order_item_data in enumerate(order_list):
            bestellartikel_id = order_item_data.get('orderSn')
            if not bestellartikel_id:
                continue
            
            produktname = order_item_data.get('originalGoodsName', '')
            variation = order_item_data.get('originalSpecName', '')
            menge = float(order_item_data.get('originalOrderQuantity', 0))
            sku_id = order_item_data.get('skuId', '')
            
            sku = ''
            product_list = order_item_data.get('productList', [])
            if product_list:
                sku = product_list[0].get('extCode', '')
            
            # Preise aus Amount Response
            netto_einzelpreis = 0.0
            brutto_einzelpreis = 0.0
            mwst_satz = DEFAULT_TAX_RATE_PERCENT
            
            if item_idx < len(order_amount_list):
                amount_item = order_amount_list[item_idx]
                netto_einzelpreis = amount_item.get('unitRetailPriceVatExcl', {}).get('amount', 0) / AMOUNT_DIVISOR
                brutto_einzelpreis = amount_item.get('unitRetailPriceVatIncl', {}).get('amount', 0) / AMOUNT_DIVISOR
                mwst_satz = amount_item.get('productTaxRate', DEFAULT_TAX_RATE_RAW) / TAX_RATE_DIVISOR
            
            existing_item = item_repo.find_by_bestellartikel_id(bestellartikel_id)
            
            item = OrderItem(
                id=existing_item.id if existing_item else None,
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
    
    # ═══════════════════════════════════════════════════════════════
    # HELPER: Status & Land Mapping
    # ═══════════════════════════════════════════════════════════════
    
    def _map_order_status(self, status_code: int) -> str:
        """Mappt TEMU Status Code zu Status String"""
        return ORDER_STATUS_MAP.get(status_code, 'unknown')
    
    def _map_land_to_iso(self, land: str) -> str:
        """Mappt Land-Namen zu ISO-2 Code"""
        return LAND_ISO_MAP.get(land, 'DE')