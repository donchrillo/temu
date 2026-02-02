# PDF Reader Fixes – 2026-02-02

## Übersicht

Drei kritische Fixes für das PDF Reader Modul (Werbungsrechnungen):

1. **Dateinamen-Mapping**: Ursprünglicher Dateiname in Excel statt umbenanntem
2. **Import-Fix**: Korrektur des app_logger Imports in api/server.py
3. **Dezimaltrennzeichen**: Korrekte Zahlenformatierung für GBP/USD

---

## Fix 1: Dateinamen-Mapping für Werbungsrechnungen

### Problem

Bei Werbungsrechnungen wurde in der Excel-Ausgabe (Spalte A "Dateiname") nicht der ursprüngliche Dateiname angezeigt, sondern der umbenannte Name.

**Beispiel:**
- Original: `INVOICE-4026MUPA26.pdf`
- In Excel: `se_2025-12-08_2025-12-15.pdf` (Land + Zeitraum)

### Ursache

Der Workflow für Werbungsrechnungen:
1. `extract_and_save_first_page()` extrahiert erste Seite und benennt PDF um zu `{country_code}_{start_date}_{end_date}.pdf`
2. `process_ad_pdfs()` verarbeitet die umbenannten PDFs aus TMP_ORDNER
3. Excel-Export verwendet `pdf_path.name` → zeigt umbenannten Namen

### Lösung

**Datei: `src/modules/pdf_reader/werbung_extraction_service.py`**

```python
# Neue Signatur mit Mapping als Return-Typ
def extract_and_save_first_page(...) -> dict[Path, str]:
    """
    Returns:
        dict[Path, str]: Mapping von neuem Pfad zu ursprünglichem Dateinamen
    """
    path_mapping: dict[Path, str] = {}

    # ... PDF-Verarbeitung ...

    path_mapping[output_path] = file.name  # Speichere Original-Namen

    # Speichere Mapping als JSON für spätere Verwendung
    if path_mapping:
        mapping_file = output_dir / "filename_mapping.json"
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump(mapping_for_json, f, ensure_ascii=False, indent=2)

    return path_mapping
```

**Neue Funktion:**
```python
def load_filename_mapping(mapping_dir: Path = TMP_ORDNER) -> dict[Path, str]:
    """Lädt gespeichertes Dateinamen-Mapping aus JSON."""
```

**Datei: `src/modules/pdf_reader/werbung_service.py`**

```python
def extract_data_from_pdf(pdf_path: Path, original_filename: Optional[str] = None):
    """Akzeptiert optionalen ursprünglichen Dateinamen."""
    data = {
        "Dateiname": original_filename if original_filename else pdf_path.name,
        # ...
    }

def process_ad_pdfs(..., filename_mapping: Optional[dict[Path, str]] = None):
    """
    Lädt automatisch Mapping aus JSON, falls nicht übergeben.
    """
    if filename_mapping is None:
        filename_mapping = load_filename_mapping(directory)

    for pdf_file in pdf_files:
        original_name = filename_mapping.get(pdf_file) if filename_mapping else None
        result = extract_data_from_pdf(pdf_file, original_filename=original_name)
```

**Datei: `api/server.py`**

```python
@app.post("/api/pdf/werbung/upload")
async def upload_werbung(...):
    filename_mapping = extract_and_save_first_page()
    result = process_ad_pdfs(filename_mapping=filename_mapping)
```

### Ergebnis

Excel zeigt nun den ursprünglichen Dateinamen:
- Spalte A: `INVOICE-4026MUPA26.pdf` ✅

Das Mapping wird als `filename_mapping.json` im TMP_ORDNER persistiert und kann auch bei separaten Verarbeitungsschritten geladen werden.

---

## Fix 2: Import-Fehler app_logger

### Problem

Server startete nicht mit folgendem Fehler:
```
ImportError: cannot import name 'app_logger' from 'src.services.logger'
```

### Ursache

**Datei: `api/server.py` (alt)**
```python
from src.services.logger import app_logger  # ❌ Falsch
```

`app_logger` ist nicht in `src/services/logger.py` definiert, sondern in `src/services/__init__.py`:

**Datei: `src/services/__init__.py`**
```python
from src.services.logger import create_module_logger
import logging

app_logger = create_module_logger('APP', 'app',
                                  console_level=logging.ERROR,
                                  file_level=logging.ERROR)

__all__ = ['app_logger']
```

### Lösung

**Datei: `api/server.py` (neu)**
```python
from src.services import app_logger  # ✅ Korrekt
```

### Ergebnis

Server startet ohne Fehler.

---

## Fix 3: Dezimaltrennzeichen für GBP/USD

### Problem

UK-Rechnungen (GBP) mit Beträgen wie `121.22 GBP` wurden falsch als `12.122,00 GBP` in Excel angezeigt.

### Ursache

Der Code behandelte alle Beträge gleich:

**Alt:**
```python
bruttowert = match.group(1).replace(".", "").replace(",", ".")
data["Bruttowert"] = float(bruttowert)
```

Diese Logik funktioniert für EU-Format (`1.234,56`), aber nicht für UK/US-Format (`1,234.56`):
- EU: Punkt = Tausendertrennzeichen, Komma = Dezimaltrennzeichen
- UK/US: Komma = Tausendertrennzeichen, Punkt = Dezimaltrennzeichen

**Beispiel:**
- Input: `121.22` (GBP)
- Alte Logik: `.replace(".", "")` → `12122`, dann `.replace(",", ".")` → `12122`
- Float-Konvertierung: `12122.0` → in Excel: `12.122,00` ❌

### Lösung

**Datei: `src/modules/pdf_reader/werbung_service.py`**

Neue Hilfsfunktion:
```python
def parse_amount(amount_str: str, currency: str) -> float:
    """
    Parst einen Betrag basierend auf der Währung.

    Args:
        amount_str: Betrag als String (z.B. "1.234,56" oder "1,234.56")
        currency: Währung (z.B. "EUR", "GBP", "USD")

    Returns:
        float: Geparster Betrag
    """
    # UK und US verwenden Punkt als Dezimaltrennzeichen
    if currency.upper() in ["GBP", "USD"]:
        # Format: 1,234.56 -> entferne Kommas, behalte Punkt
        return float(amount_str.replace(",", ""))
    else:
        # EU-Format: 1.234,56 -> entferne Punkte, ersetze Komma durch Punkt
        return float(amount_str.replace(".", "").replace(",", "."))
```

Verwendung im Code:
```python
# Währung aus patterns extrahieren
currency = lang_patterns.get("währung", "EUR")

if lang_patterns.get("summe"):
    match = re.search(fr"{re.escape(lang_patterns['summe'])}\s*([\d.,]+)\s*{currency}", text)
    if match:
        data["Bruttowert"] = parse_amount(match.group(1), currency)

if lang_patterns.get("mwst"):
    pattern = fr"{re.escape(lang_patterns['mwst'])}\s*([\d.,]+)\s*{currency}"
    match = re.search(pattern, text)
    if match:
        data["Mehrwertsteuer"] = parse_amount(match.group(1), currency)
```

### Währungszuordnung

**UK (co.uk):** GBP → Punkt als Dezimaltrennzeichen
**USA:** USD → Punkt als Dezimaltrennzeichen
**EU (de, fr, es, it, nl, be, ie):** EUR → Komma als Dezimaltrennzeichen
**Schweden (se):** SEK → Komma als Dezimaltrennzeichen
**Polen (pl):** PLN → Komma als Dezimaltrennzeichen

### Ergebnis

**UK-Rechnung:**
- Input PDF: `121.22 GBP`
- Excel-Output: `121,22` (float: 121.22) ✅

**EU-Rechnung:**
- Input PDF: `121,22 EUR`
- Excel-Output: `121,22` (float: 121.22) ✅

---

## Zusammenfassung

| Fix | Dateien | Status |
|-----|---------|--------|
| Dateinamen-Mapping | `werbung_extraction_service.py`, `werbung_service.py`, `api/server.py` | ✅ Behoben |
| Import-Fehler | `api/server.py` | ✅ Behoben |
| Dezimaltrennzeichen | `werbung_service.py` | ✅ Behoben |

## Testing

Alle drei Fixes wurden getestet:
1. ✅ Werbungsrechnungen zeigen ursprünglichen Dateinamen in Excel
2. ✅ Server startet ohne Import-Fehler
3. ✅ UK-Rechnungen (GBP) zeigen korrekte Beträge in Excel

---

**Datum:** 2. Februar 2026
**Betroffen:** PDF Reader Modul (Werbungsrechnungen)
**Priority:** High (Produktionsfehler)
