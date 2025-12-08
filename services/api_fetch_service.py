"""API Fetch Service - Ruft TEMU API auf und speichert Responses lokal"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from config.settings import DATA_DIR
from services.temu_client import TemuApiClient
from services.temu_orders_api import TemuOrdersApi

API_RESPONSE_DIR = DATA_DIR / 'api_responses'
API_RESPONSE_DIR.mkdir(exist_ok=True)

def save_json_pretty(data, filepath):
    """Speichert JSON schön formatiert."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_and_save_orders(app_key, app_secret, access_token, api_endpoint, 
                         parent_order_status=0, days_back=7):
    """
    Ruft TEMU API auf und speichert Responses lokal.
    
    Args:
        app_key: TEMU_APP_KEY
        app_secret: TEMU_APP_SECRET
        access_token: TEMU_ACCESS_TOKEN
        api_endpoint: TEMU_API_ENDPOINT
        parent_order_status: Order Status Filter (0=All, 1=PENDING, 2=UN_SHIPPING, etc.)
        days_back: Wie viele Tage zurück (Standard: 7 Tage)
    
    Returns:
        bool: True wenn erfolgreich
    """
    
    # Validiere Credentials
    if not all([app_key, app_secret, access_token]):
        return False
    
    # Berechne Timestamps aus Tagen
    now = datetime.now()
    create_before = int(now.timestamp())
    create_after = int((now - timedelta(days=days_back)).timestamp())
    
    # Erstelle API Client
    client = TemuApiClient(app_key, app_secret, access_token, api_endpoint)
    orders_api = TemuOrdersApi(client)
    
    # Abrufe Orders mit optionalen Parametern
    orders_response = orders_api.get_orders(
        page_number=1, 
        page_size=100, 
        parent_order_status=parent_order_status,
        createAfter=create_after,
        createBefore=create_before
    )
    
    if orders_response is None:
        return False
    
    # Speichere Orders
    orders_file = API_RESPONSE_DIR / 'api_response_orders.json'
    save_json_pretty(orders_response, orders_file)
    
    # Extrahiere Orders
    orders = orders_response.get("result", {}).get("pageItems", [])
    
    if not orders:
        return True
    
    # Abrufe Versand- & Preisinformationen
    shipping_responses = {}
    amount_responses = {}
    
    for order_item in orders:
        parent_order_map = order_item.get("parentOrderMap", {})
        parent_order_sn = parent_order_map.get("parentOrderSn")
        
        if not parent_order_sn:
            continue
        
        # Versandinfo
        shipping_response = orders_api.get_shipping_info(parent_order_sn)
        if shipping_response:
            shipping_responses[parent_order_sn] = shipping_response
        
        # Preisinformation
        amount_response = orders_api.get_order_amount(parent_order_sn)
        if amount_response:
            amount_responses[parent_order_sn] = amount_response
    
    # Speichere Zusammenfassungen
    all_shipping_file = API_RESPONSE_DIR / 'api_response_shipping_all.json'
    save_json_pretty(shipping_responses, all_shipping_file)
    
    all_amount_file = API_RESPONSE_DIR / 'api_response_amount_all.json'
    save_json_pretty(amount_responses, all_amount_file)
    
    return True