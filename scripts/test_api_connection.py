"""
Testet die TEMU API-Verbindung und Authentifizierung.
Hilfstool zur Fehlersuche.
"""

import sys
import os
from pathlib import Path

# Pfade hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import (
    TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT
)
from src.api_import.temu_client import TemuApiClient
from src.api_import.temu_orders_api import TemuOrdersApi

def test_api_connection():
    """Testet API-Verbindung"""
    
    print("=" * 70)
    print("TEMU API - Verbindungstest")
    print("=" * 70)
    
    # Validiere Credentials
    print("\n[1/3] Credentials prüfen...")
    print("-" * 70)
    
    credentials = {
        'APP_KEY': TEMU_APP_KEY,
        'APP_SECRET': TEMU_APP_SECRET,
        'ACCESS_TOKEN': TEMU_ACCESS_TOKEN,
        'API_ENDPOINT': TEMU_API_ENDPOINT
    }
    
    missing = [k for k, v in credentials.items() if not v]
    
    if missing:
        print(f"✗ Fehlende Credentials: {', '.join(missing)}")
        return False
    
    print("✓ Alle Credentials vorhanden")
    print(f"  Endpoint: {TEMU_API_ENDPOINT}")
    
    # Erstelle Client
    print("\n[2/3] API Client erstellen...")
    print("-" * 70)
    
    try:
        client = TemuApiClient(
            TEMU_APP_KEY,
            TEMU_APP_SECRET,
            TEMU_ACCESS_TOKEN,
            TEMU_API_ENDPOINT
        )
        print("✓ API Client erstellt")
    except Exception as e:
        print(f"✗ Fehler beim Erstellen des API Clients: {e}")
        return False
    
    # Teste Orders API
    print("\n[3/3] Orders API testen...")
    print("-" * 70)
    
    try:
        orders_api = TemuOrdersApi(client)
        response = orders_api.get_orders(page_number=1, page_size=1)
        
        if response is None:
            print("✗ API Response ist None")
            return False
        
        if not response.get('success', False):
            error_code = response.get('errorCode', '?')
            error_msg = response.get('errorMsg', 'Unbekannter Fehler')
            print(f"✗ API Fehler (Code {error_code}): {error_msg}")
            return False
        
        orders_count = len(response.get('result', {}).get('pageItems', []))
        print(f"✓ API erfolgreich - {orders_count} Order(s) gefunden")
        
    except Exception as e:
        print(f"✗ Fehler beim API-Test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Erfolg
    print("\n" + "=" * 70)
    print("✓ ALLE TESTS ERFOLGREICH")
    print("=" * 70)
    print("\nNächste Schritte:")
    print("  1. python -m scripts.fetch_api_responses  (Responses speichern)")
    print("  2. python -m workflows.api_to_db          (In DB importieren)")
    print("=" * 70 + "\n")
    
    return True

if __name__ == "__main__":
    success = test_api_connection()
    sys.exit(0 if success else 1)
