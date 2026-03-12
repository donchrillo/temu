"""Gemeinsame Utility-Funktionen für Betragsparsen in PDF-Services.

Konsolidiert die Betragslogik aus rechnungen_service und werbung_service
in eine einzige, robuste Implementierung.
"""
import re
from typing import List, Optional


# Länder mit Punkt als Dezimaltrennzeichen (UK/US-Format: 1,234.56)
DOT_DECIMAL_COUNTRIES = {"co.uk", "us", "ie"}

# Länder mit Komma als Dezimaltrennzeichen (EU-Format: 1.234,56)
# Alle anderen Länder nutzen standardmäßig EU-Format


def parse_amount(amount_str: str, country_code: str = "", currency: str = "") -> float:
    """Parst einen Betrag-String unter Berücksichtigung länderspezifischer Formate.

    Erkennt automatisch das korrekte Format basierend auf:
    1. Währung (GBP/USD -> Punkt als Dezimalzeichen)
    2. Ländercode (co.uk, us, ie -> Punkt als Dezimalzeichen)
    3. Heuristik für mehrdeutige Fälle

    Args:
        amount_str: Betrag als String (z.B. "1.234,56" oder "1,234.56")
        country_code: Ländercode (z.B. "de", "co.uk")
        currency: Währungscode (z.B. "EUR", "GBP")

    Returns:
        float: Geparster Betrag

    Raises:
        ValueError: Wenn der String nicht geparst werden kann
    """
    if not amount_str or not amount_str.strip():
        raise ValueError(f"Leerer Betrag-String: '{amount_str}'")

    amount_str = amount_str.strip()

    # UK/US-Format erkennen (Punkt = Dezimal, Komma = Tausender)
    if _is_dot_decimal_format(country_code, currency):
        return float(amount_str.replace(",", ""))

    # EU-Format mit Komma als Dezimaltrennzeichen
    if "," in amount_str:
        return float(amount_str.replace(".", "").replace(",", "."))

    # Nur Punkt vorhanden -> Heuristik anwenden
    if "." in amount_str:
        return _parse_ambiguous_dot(amount_str)

    # Keine Trennzeichen
    return float(amount_str)


def _is_dot_decimal_format(country_code: str, currency: str) -> bool:
    """Prüft ob Punkt als Dezimaltrennzeichen verwendet wird."""
    if currency.upper() in ("GBP", "USD"):
        return True
    return country_code in DOT_DECIMAL_COUNTRIES


def _parse_ambiguous_dot(amount_str: str) -> float:
    """Parst einen Betrag mit mehrdeutigem Punkt-Trennzeichen.

    Heuristik: Genau 2 Nachkommastellen -> Dezimalpunkt (z.B. "92.00")
    Sonst: Tausendertrennzeichen (z.B. "10.000")
    """
    parts = amount_str.split(".")
    if len(parts) == 2 and len(parts[1]) == 2:
        # Genau 2 Nachkommastellen -> Dezimalpunkt
        return float(amount_str)
    # Tausendertrennzeichen -> entfernen
    return float(amount_str.replace(".", ""))


def find_value_after_labels(
    text: str,
    labels: List[str],
    country_code: str,
    currency: str = "EUR",
) -> Optional[float]:
    """Sucht nach einer Zahl, die nach einem der Labels im Text steht.

    Flexible Erkennung verschiedener Formate:
    - "Label Währung Betrag" (z.B. "Nettobetrag EUR 92.00")
    - "Label: Betrag" (z.B. "USt: 17.48")
    - "Label Betrag" (z.B. "Gesamtsumme 109.48")

    Args:
        text: Gesamter PDF-Text
        labels: Liste der zu suchenden Labels
        country_code: Ländercode für Betragsformat
        currency: Währung für Betragsformat

    Returns:
        float or None: Gefundener Betrag oder None
    """
    for label in labels:
        regex = _build_label_regex(label)
        match = re.search(regex, text)
        if match:
            amount_str = match.group(1)
            # Ignoriere zu kurze Matches (z.B. "." aus "USt.-Satz")
            if len(amount_str) < 2:
                continue
            try:
                return parse_amount(amount_str, country_code, currency)
            except ValueError:
                continue
    return None


def _build_label_regex(label: str) -> str:
    """Erstellt ein flexibles Regex zum Finden von Beträgen nach einem Label.

    Berücksichtigt:
    - Labels mit/ohne Doppelpunkt
    - Optionale Währungsangabe zwischen Label und Betrag
    """
    escaped = re.escape(label)
    if label.endswith(":"):
        return fr"(?i){escaped}\s*(?:EUR|GBP|USD|SEK|PLN)?\s*([\d.,]+)"
    return fr"(?i){escaped}\s*:?\s*(?:EUR|GBP|USD|SEK|PLN)?\s*([\d.,]+)"
