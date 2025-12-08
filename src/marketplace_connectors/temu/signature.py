"""TEMU API Signature Berechnung (MD5)"""

import json
import hashlib

def calculate_signature(app_secret, params):
    """
    Berechnet die TEMU API Signatur (MD5).
    
    TEMU Signatur-Methode:
    1. Sortiere Parameter alphabetisch
    2. Für jeden Parameter: key + value (ohne Anführungszeichen)
    3. String: app_secret + sorted_params + app_secret
    4. MD5 Hash (UPPERCASE)
    
    Args:
        app_secret: TEMU_APP_SECRET aus .env
        params: Dict mit allen Request-Parametern
    
    Returns:
        Signatur als UPPERCASE HEX-String
    """
    
    temp = []
    
    # Sortiere Parameter alphabetisch
    sorted_params = sorted(params.items())
    
    # Erstelle String für die Berechnung
    param_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
    
    # Berechne den MD5 Hash
    hash_object = hashlib.md5(f"{app_secret}{param_string}{app_secret}".encode())
    sign = hash_object.hexdigest().upper()
    
    return sign

if __name__ == "__main__":
    # Testaufruf
    secret = "mein_app_secret"
    parameters = {
        "param1": "wert1",
        "param2": "wert2",
        "param3": "wert3"
    }
    
    signatur = calculate_signature(secret, parameters)
    print(f"Berechnete Signatur: {signatur}")