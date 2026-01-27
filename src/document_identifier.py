# identifier.py

rules = [
    # Deutschland
    {"land": "de", "typ": "rechnung", "contains": ["Rechnungsnummer:", "RECHNUNG", "Amazon.de"]},
    {"land": "de", "typ": "gutschrift", "contains": ["STEUERGUTSCHRIFT", "Gutschriftennummer:", "Amazon.de"]},
    {"land": "de", "typ": "werbung", "contains": ["Amazon Online Germany GmbH", "Rechnungszeitraum"]},

    # Frankreich
    {"land": "fr", "typ": "rechnung", "contains": ["Facture n°:", "FACTURE POUR LA TVA", "Amazon.fr"]},
    {"land": "fr", "typ": "gutschrift", "contains": ["NOTE DE CRÉDIT D'IMPÔT", "Numéro de note de crédit:", "Amazon.fr"]},
    {"land": "fr", "typ": "werbung", "contains": ["Amazon Online France", "Période de facturation"]},


    # Belgien
    {"land": "be", "typ": "rechnung", "contains": ["Factuurnummer:", "FACTUUR", "Amazon.com.be"]},
    {"land": "be", "typ": "gutschrift", "contains": ["CREDITNOTA", "Nummer creditnota:", "Amazon.com.be"]},

    # Niederlande
    {"land": "nl", "typ": "rechnung", "contains": ["Factuurnummer:", "FACTUUR", "Amazon.nl"]},
    {"land": "nl", "typ": "gutschrift", "contains": ["CREDITNOTA", "Nummer creditnota:", "Amazon.nl"]},

    # Spanien
    {"land": "es", "typ": "rechnung", "contains": ["Número de la factura:", "FACTURA FISCAL"]},
    {"land": "es", "typ": "gutschrift", "contains": ["NOTA DE CRÉDITO DE IMPUESTOS", "Número de nota de crédito:"]},
    {"land": "es", "typ": "werbung", "contains": ["Amazon Online Spain", "Periodo de facturación"]},


    # Italien
    {"land": "it", "typ": "rechnung", "contains": ["Numero fattura:", "FATTURA"]},
    {"land": "it", "typ": "gutschrift", "contains": ["NOTA DI CREDITO D'IMPOSTA", "Numero nota di credito:"]},
    {"land": "it", "typ": "werbung", "contains": ["Amazon Online Italy", "Periodo della fattura"]},


    # Polen
    {"land": "pl", "typ": "rechnung", "contains": ["Numer faktury:", "FAKTURA"]},
    {"land": "pl", "typ": "gutschrift", "contains": ["Faktura korygujca", "Nr faktury korygujcej:"]},

    # Großbritannien
    {"land": "co.uk", "typ": "rechnung", "contains": ["Invoice Number:", "INVOICE", "Amazon.co.uk"]},
    {"land": "co.uk", "typ": "gutschrift", "contains": ["TAX CREDIT NOTE", "Credit Note Number:", "Amazon.co.uk"]},
    {"land": "co.uk", "typ": "werbung", "contains": ["Amazon Online UK", "Invoice Period"]},


    # Irland
    {"land": "ie", "typ": "rechnung", "contains": ["Invoice Number:", "INVOICE", "Amazon.ie"]},
    {"land": "ie", "typ": "gutschrift", "contains": ["TAX CREDIT NOTE", "Credit Note Number:", "Amazon.ie"]},

    # Schweden
    {"land": "se", "typ": "rechnung", "contains": ["Fakturanummer:", "FAKTURA"]},
    {"land": "se", "typ": "gutschrift", "contains": ["KREDITFAKTURA", "Kreditnota-nummer:"]},
    {"land": "se", "typ": "werbung", "contains": ["Amazon Online Sweden", "Fakturaperiod"]}
]

def determine_country_and_document_type(text):
    """
    Erkennt Land und Dokumenttyp anhand typischer Begriffe im PDF-Text.

    Args:
        text (str): Gesamter Textinhalt der PDF.

    Returns:
        tuple: (land, dokumenttyp) oder (None, None)
    """
    for rule in rules:
        if all(keyword in text for keyword in rule["contains"]):
            return rule["land"], rule["typ"]
    return None, None
