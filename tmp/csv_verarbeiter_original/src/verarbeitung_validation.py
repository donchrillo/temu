"""
verarbeitung_validation.py – Validierungsfunktionen für Amazon-Bestellnummern und kritische Gegenkonten

Dieses Modul stellt elementare Prüfmechanismen für die Datenverarbeitung bereit:

Funktionen:
- `ist_amazon_bestellnummer`: Ermittelt, ob ein String dem typischen Amazon-Bestellnummernformat entspricht.
- `ist_kritisches_gegenkonto`: Identifiziert Gegenkonten, die im Bereich 0–20 liegen und als kritisch gelten.

Diese Funktionen werden im Rahmen der zeilenweisen CSV-Verarbeitung eingesetzt, um bestimmte Felder
zu validieren und potenzielle Prüf- oder Fehlerquellen zu markieren.
"""

import re  # Für Mustererkennung mit regulären Ausdrücken


def ist_amazon_bestellnummer(wert: str) -> bool:
    """
    Überprüft, ob ein übergebener String eine gültige Amazon-Bestellnummer ist.

    Amazon-Bestellnummern folgen einem standardisierten Format:
    - Drei Ziffern
    - Ein Bindestrich
    - Sieben Ziffern
    - Ein weiterer Bindestrich
    - Sieben Ziffern

    Beispiel für eine gültige Bestellnummer: '306-1234567-8910111'

    Args:
        wert (str): Der zu prüfende Wert, üblicherweise aus der Spalte "Belegfeld 1"

    Returns:
        bool: True, wenn der Wert dem Amazon-Format entspricht, andernfalls False.
    """
    if isinstance(wert, str):
        muster = r"\d{3}-\d{7}-\d{7}$"
        # Entfernt Leerzeichen am Anfang/Ende und prüft mit regulärem Ausdruck
        return re.match(muster, wert.strip()) is not None
    return False


def ist_kritisches_gegenkonto(wert) -> bool:
    """
    Bestimmt, ob der übergebene Wert ein "kritisches Gegenkonto" darstellt.

    In diesem Kontext gelten alle Kontonummern zwischen 0 und 20 als kritisch.
    Solche Konten erfordern eine manuelle Überprüfung, da sie oft für Ausgleichsbuchungen
    oder Systemfehler verwendet werden.

    Die Funktion versucht, den Wert in eine Ganzzahl zu konvertieren. Ist das nicht möglich,
    wird False zurückgegeben.

    Args:
        wert (Any): Der Inhalt der Spalte "Gegenkonto (ohne BU-Schlüssel)"

    Returns:
        bool: True, wenn der Wert eine Ganzzahl von 0 bis 20 ist, sonst False.
    """
    try:
        val = int(wert)
        return 0 <= val <= 20
    except (ValueError, TypeError):
        # Wert ist nicht konvertierbar (z. B. leer oder alphanumerisch)
        return False
