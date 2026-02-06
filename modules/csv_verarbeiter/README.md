# CSV Verarbeiter Module

## Übersicht

Das CSV Verarbeiter Modul ist für die Verarbeitung von **Amazon DATEV-kompatiblen CSV-Exporte** konzipiert. Es ersetzt Amazon-Bestellnummern durch JTL-Kundennummern und generiert detaillierte Verarbeitungsberichte.

**Zweck:** Konvertierung von Marktplatz-CSV-Exporten (Amazon) in JTL-kompatibles Format für die Buchhaltung.

## Features

- ✅ Amazon OrderID Validierung (Format: XXX-XXXXXXX-XXXXXXX)
- ✅ Kritische Konten-Erkennung (0-20)
- ✅ OrderID → JTL-Kundennummer Ersetzung via SQL
- ✅ CSV/ZIP Datei-Verarbeitung mit Encoding-Erkennung (cp1252)
- ✅ Excel-Report-Generierung (Mini-Report, Änderungen, Fehler)
- ✅ Strukturiertes Logging und Fehlerbehandlung

## Core Services

### csv_io_service.py
Datei-I/O Operationen für CSV und ZIP Dateien.

**Hauptfunktionen:**
- `read_csv()` - CSV mit automatischer Encoding-Erkennung (chardet)
- `write_csv()` - CSV mit DATEV-Standard (cp1252, Semikolon)
- `extract_zip()` - ZIP-Extraktion
- `create_zip()` - ZIP-Erstellung

**Editor-Spalten-Standard:**
- Trennzeichen: `;` (Semikolon)
- Encoding: `cp1252` (Windows DATEV Standard)

### validation_service.py
Validierung von OrderID Patterns und Konten.

**Funktionen:**
- `validate_order_id_pattern()` - **Amazon Format:** `XXX-XXXXXXX-XXXXXXX`
- `is_critical_account()` - Prüfung auf kritische Konten (0-20)
- `validate_csv_structure()` - Prüfung erforderlicher DATEV-Spalten
- `validate_dataframe()` - Umfassende Datenvalidierung
- `check_data_integrity()` - NULL-Wert Prüfung

**DATEV-Spalten (Standard):**
- `'Belegfeld 1'` - Amazon OrderID
- `'Gegenkonto (ohne BU-Schlüssel)'` - Kritische Konten-Prüfung

### replacement_service.py
Ersetzung von Amazon OrderIDs mit JTL-Kundennummern.

**Funktionen:**
- `get_customer_number_by_amazon_order_id()` - Lookup via JTL tAuftrag
- `replace_amazon_order_ids()` - DataFrame-Ersetzung
- `get_replacement_stats()` - Statistiken

**DB-Abfrage:**
```sql
SELECT cKundennr FROM tAuftrag 
WHERE cExterneAuftragsnummer = :order_id
```

### report_service.py
Excel-Report-Generierung mit Überblick und Details.

**Output-Format:**
- `Zusammenfassung` - Mini-Report mit Gesamtstatistiken
- `Validierungsfehler` - Strukturelle Fehler
- `Warnungen` - OrderID Patterns, Kritische Konten
- `Statistiken` - Ersetzungs- und Validierungsmetriken

## Configuration (config.py)

```python
# DATEV-Standard
CSV_DELIMITER = ';'              # Semikolon
CSV_INPUT_ENCODING = 'auto'      # chardet detection
CSV_OUTPUT_ENCODING = 'cp1252'   # Windows DATEV Standard

# Spalten
DATEV_COLUMN_BELEG = 'Belegfeld 1'
DATEV_COLUMN_GEGENKONTO = 'Gegenkonto (ohne BU-Schlüssel)'

# Verarbeitung
SKIP_CRITICAL_ACCOUNTS = True    # Konten 0-20 überspringen
CRITICAL_ACCOUNT_RANGE = (0, 20)
```

## Workflow (Phase 3+)

Die folgenden Phasen sind noch ausstehend:

1. **Phase 3: API Endpoints** - REST-API für Upload, Processing, Status
2. **Phase 4: Frontend** - Drag & Drop UI mit Progress Tracking
3. **Phase 5: Integration** - Router Mount, WebSocket Updates
4. **Phase 6: Documentation** - API Docs, Troubleshooting
5. **Phase 7: Deployment** - PM2 Integration, Testing

## Dependencies

```
pandas==2.1.3
openpyxl==3.1.5
chardet==5.2.0
pyodbc==5.0.1
SQLAlchemy==2.0.23
```

## Error Handling

Das Modul implementiert umfassendes Error-Handling:

- **Encoding-Fehler** - Automatische Detektion und Fallback
- **Missing Columns** - Validierung erforderlicher DATEV-Spalten
- **Invalid OrderIDs** - Pattern-Matching mit detaillierten Warnungen
- **DB Connection** - Fehlerbehandlung mit Fallback
- **NULL Values** - Datenintegritätsprüfung

## Logging

Strukturiertes Logging über `log_service`:

```python
log_service.log(job_id, "csv_io", "INFO", "→ CSV gelesen: 1000 Zeilen")
log_service.log(job_id, "csv_validation", "WARNING", "⚠ Invalid OrderID Pattern")
log_service.log(job_id, "csv_replacement", "ERROR", "❌ DB Connection failed")
```

## Testing

Unit Tests (Phase 5):
- CSV Lesen/Schreiben mit verschiedenen Encodings
- OrderID Pattern-Validierung (gültig/ungültig)
- Replacement Logik (erfolg/fehler)
- Report-Generierung

## Lizenz & Attributionen

Basierend auf dem ursprünglichen **JTL2DATEV CSV-Verarbeiter** von Christian Blass.
Migration in TOCI Tools Monorepo (6. Februar 2026).

---

**Datum:** 6. Februar 2026  
**Status:** Phase 2 ✅ | Phase 3 ⏳
