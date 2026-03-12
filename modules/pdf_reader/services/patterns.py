"""Sprach- und dokumenttypspezifische Patterns für die PDF-Datenextraktion.

Jedes Land definiert Patterns für Rechnungen, Gutschriften und Werbung.
Die Keys (rechnungsnummer, summe, etc.) werden von den Extraction-Services genutzt.
"""

PATTERNS = {
    "fr": {
        "rechnung": {
            "rechnungsnummer": "Facture n°:",
            "rechnungsdatum": "Date de la facture:",
            "summe": "Total",
            "währung": "EUR"
        },
        "gutschrift": {
            "rechnungsnummer": "Numéro de note de crédit:",
            "rechnungsdatum": "Date d'émission de la note de crédit:",
            "summe": "Total",
            "währung": "EUR"
        },
        "werbung": {
            "rechnungsnummer": "Numéro de facture",
            "rechnungsdatum": "Date de facturation",
            "zeitraum": "Période de facturation",
            "summe": "Montant de la facture dû",
            "währung": "EUR",
            "mwst": "VAT",
            "mwst_regex": r"VAT\s*\(0%\)\s*-\s*FRANCE\s*([\d.,]+)\s*EUR",
            "mwst_calc": True
        }
    },
    "de": {
        "rechnung": {
            "rechnungsnummer": "Rechnungsnummer:",
            "rechnungsdatum": "Rechnungsdatum:",
            "summe": "Gesamtsumme",
            "währung": "EUR"
        },
        "gutschrift": {
            "rechnungsnummer": "Gutschriftennummer:",
            "rechnungsdatum": "Ausstellungsdatum der Gutschrift:",
            "summe": "Gesamtsumme",
            "währung": "EUR"
        },
        "werbung": {
            "rechnungsnummer": "Nummer der Rechnung",
            "rechnungsdatum": "Datum der Rechnung",
            "zeitraum": "Rechnungszeitraum",
            "summe": "Fälliger Gesamtbetrag",
            "währung": "EUR",
            "mwst": "VAT",
            "mwst_regex": r"VAT\s*\(19%\)\s*-\s*GERMANY\s*([\d.,]+)\s*EUR"
        }
    },

    "nl": {
        "rechnung": {
            "rechnungsnummer": "Factuurnummer:",
            "rechnungsdatum": "Factuurdatum:",
            "summe": "Totaal",
            "währung": "EUR"
        },
        "gutschrift": {
            "rechnungsnummer": "Nummer creditnota:",
            "rechnungsdatum": "Creditnotadatum:",
            "summe": "Totaal",
            "währung": "EUR"
        }
    },
    "be": {
        "rechnung": {
            "rechnungsnummer": "Factuurnummer:",
            "rechnungsdatum": "Factuurdatum:",
            "summe": "Totaal",
            "währung": "EUR"
        },
        "gutschrift": {
            "rechnungsnummer": "Nummer creditnota:",
            "rechnungsdatum": "Creditnotadatum:",
            "summe": "Totaal",
            "währung": "EUR"
        }
    },    
    "it": {
        "rechnung": {
            "rechnungsnummer": "Numero fattura:",
            "rechnungsdatum": "Data fattura:",
            "summe": "Totale",
            "währung": "EUR"
        },
        "gutschrift": {
            "rechnungsnummer": "Numero nota di credito:",
            "rechnungsdatum": "Data emissione nota di credito:",
            "summe": "Totale",
            "währung": "EUR"
        },
        "werbung": {
            "rechnungsnummer": "Numero Di Fattura",
            "rechnungsdatum": "Data Della Fattura",
            "zeitraum": "Periodo Della Fattura",
            "summe": "Importo Fatturato Dovuto",
            "währung": "EUR",
            "mwst": "VAT",
            "mwst_regex": r"VAT\s*\(\d+%\)\s*-\s*ITALY\s*([\d.,]+)\s*EUR",
            "mwst_calc": True,
            "brutto_pattern": "Importo Totale \\(Tasse Incluse\\)",
            "netto_pattern": "Totale Parziale \\(Tasse Escluse\\)"
        }        
    },
    "es": {
        "rechnung": {
            "rechnungsnummer": "Número de la factura:",
            "rechnungsdatum": "Fecha de la factura:",
            "summe": "Total",
            "währung": "EUR"
        },
         "gutschrift": {
            "rechnungsnummer": "Número de nota de crédito:",
            "rechnungsdatum": "Fecha de emisión de la nota de crédito:",
            "summe": "Total",
            "währung": "EUR"
        },
        "werbung": {
            "rechnungsnummer": "Número de factura",
            "rechnungsdatum": "Fecha de la factura",
            "zeitraum": "Periodo de facturación",
            "summe": "Importe de factura adeudado",
            "währung": "EUR",
            "mwst": "VAT",
            "mwst_regex": r"VAT\s*\(0%\)\s*-\s*SPAIN\s*([\d.,]+)\s*EUR",
            "mwst_calc": True
        }       
    },
    "pl": {
        "rechnung": {
            "rechnungsnummer": "Numer faktury:",
            "rechnungsdatum": "Data wystawienia faktury:",
         "summe": "Łączna",
            "währung": "PLN"
        },
        "gutschrift": {
            "rechnungsnummer": "Nr faktury korygujcej:",
            "rechnungsdatum": "Data faktury korygujcej:",
            "summe": "Łączna",
            "währung": "PLN"
        }         
    },
    "co.uk": {
        "rechnung": {
            "rechnungsnummer": "Invoice Number:",
            "rechnungsdatum": "Invoice Date:",
            "summe": "Total",
            "währung": "GBP"
        },
        "gutschrift": {
            "rechnungsnummer": "Credit Note Number:",
            "rechnungsdatum": "Credit Note Issue Date:",
            "summe": "Total",
            "währung": "GBP"
        },
        "werbung": {
            "rechnungsnummer": "Invoice Number",
            "rechnungsdatum": "Invoice Date",
            "zeitraum": "Invoice Period",
            "summe": "Total Amount Due",
            "währung": "GBP",
            "mwst": "VAT",
            "mwst_regex": r"VAT\s*\(\d+%\)\s*-\s*UNITED KINGDOM\s*([\d.,]+)\s*GBP",
            "mwst_calc": True
         }
    },
    "ie": {
        "rechnung": {
            "rechnungsnummer": "Invoice Number:",
            "rechnungsdatum": "Invoice Date:",
            "summe": "Total",
            "währung": "EUR"
        },
        "gutschrift": {
            "rechnungsnummer": "Credit Note Number:",
            "rechnungsdatum": "Credit Note Issue Date:",
            "summe": "Total",
            "währung": "EUR"
        } 
    },
    "se": {
        "rechnung": {
            "rechnungsnummer": "Fakturanummer:",
            "rechnungsdatum": "Fakturadatum:",
            "summe": "Total",
            "währung": "SEK"
        },
        "gutschrift": {
            "rechnungsnummer": "Kreditnota-nummer:",
            "rechnungsdatum": "Kreditfakturadatum:",
            "summe": "Total",
            "währung": "SEK"
        },
        "werbung": {
            "rechnungsnummer": "Fakturanummer",
            "rechnungsdatum": "Fakturadatum",
            "zeitraum": "Fakturaperiod",
            "summe": "Totalt belopp (inkl. moms)",
            "währung": "SEK",
            "mwst": "VAT",
            "mwst_regex": r"VAT\s*\(\d+%\)\s*-\s*SWEDEN\s*([\d.,]+)\s*SEK",
            "mwst_calc": True
        }        
    }


}
