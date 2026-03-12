"""Order Domain Model - Datenstruktur für TEMU Orders"""

from typing import Optional


class Order:
    """Domain Model für Order"""

    def __init__(
        self,
        id: Optional[int] = None,
        bestell_id: Optional[str] = None,
        bestellstatus: Optional[int] = None,
        kaufdatum=None,
        vorname_empfaenger: Optional[str] = None,
        nachname_empfaenger: Optional[str] = None,
        strasse: Optional[str] = None,
        adresszusatz: Optional[str] = None,
        plz: Optional[str] = None,
        ort: Optional[str] = None,
        bundesland: Optional[str] = None,
        land: Optional[str] = None,
        land_iso: Optional[str] = None,
        email: Optional[str] = None,
        telefon_empfaenger: Optional[str] = None,
        versandkosten: Optional[float] = None,
        status: Optional[str] = None,
        xml_erstellt: bool = False,
        trackingnummer: Optional[str] = None,
        versanddienstleister: Optional[str] = None,
        versanddatum=None,
    ):
        self.id = id
        self.bestell_id = bestell_id
        self.bestellstatus = bestellstatus
        self.kaufdatum = kaufdatum
        self.vorname_empfaenger = vorname_empfaenger
        self.nachname_empfaenger = nachname_empfaenger
        self.strasse = strasse
        self.adresszusatz = adresszusatz
        self.plz = plz
        self.ort = ort
        self.bundesland = bundesland
        self.land = land
        self.land_iso = land_iso
        self.email = email
        self.telefon_empfaenger = telefon_empfaenger
        self.versandkosten = versandkosten
        self.status = status
        self.xml_erstellt = xml_erstellt
        self.trackingnummer = trackingnummer
        self.versanddienstleister = versanddienstleister
        self.versanddatum = versanddatum


class OrderItem:
    """Domain Model für Order Item"""

    def __init__(
        self,
        id: Optional[int] = None,
        order_id: Optional[int] = None,
        bestell_id: Optional[str] = None,
        bestellartikel_id: Optional[str] = None,
        produktname: Optional[str] = None,
        sku: Optional[str] = None,
        sku_id: Optional[int] = None,
        variation: Optional[str] = None,
        menge: Optional[int] = None,
        netto_einzelpreis: Optional[float] = None,
        brutto_einzelpreis: Optional[float] = None,
        gesamtpreis_netto: Optional[float] = None,
        gesamtpreis_brutto: Optional[float] = None,
        mwst_satz: Optional[float] = None,
    ):
        self.id = id
        self.order_id = order_id
        self.bestell_id = bestell_id
        self.bestellartikel_id = bestellartikel_id
        self.produktname = produktname
        self.sku = sku
        self.sku_id = sku_id
        self.variation = variation
        self.menge = menge
        self.netto_einzelpreis = netto_einzelpreis
        self.brutto_einzelpreis = brutto_einzelpreis
        self.gesamtpreis_netto = gesamtpreis_netto
        self.gesamtpreis_brutto = gesamtpreis_brutto
        self.mwst_satz = mwst_satz
