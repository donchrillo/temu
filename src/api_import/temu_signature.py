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
    
    # Baue Signatur-String
    for k, v in sorted_params:
        # JSON-encode den Wert (mit ensure_ascii=False)
        v_json = json.dumps(v, ensure_ascii=False, separators=(',', ':'))
        # Entferne äußere Anführungszeichen
        v_stripped = v_json.strip('"')
        # Concatenate key + value
        temp.append(str(k) + v_stripped)
    
    # Zusammenfassung
    un_sign = ''.join(temp)
    
    # Wrap mit app_secret
    un_sign = str(app_secret) + un_sign + str(app_secret)
    
    # MD5 Hash (UPPERCASE)
    sign = hashlib.md5(un_sign.encode('utf-8')).hexdigest().upper()
    
    return sign
