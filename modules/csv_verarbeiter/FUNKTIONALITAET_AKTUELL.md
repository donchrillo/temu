# CSV Verarbeiter - Aktuelle Funktionalität

**Stand:** 13. Februar 2026  
**Status:** ✅ Vollständig getestet und funktionsfähig

---

## Übersicht

Der CSV-Verarbeiter ist für die Verarbeitung von **Amazon DATEV-kompatiblen CSV-Exporten** konzipiert. Die Hauptfunktion besteht darin, **Amazon OrderIDs durch JTL-Kundennummern zu ersetzen** und dabei kritische Konten zu überwachen.

---

## 🎯 Hauptfunktionalitäten (Aktuell)

### 1. OrderID → Kundennummer Ersetzung ✅

**Was passiert:**
- Liest CSV-Dateien aus `data/csv_verarbeiter/eingang/`
- Sucht in Spalte `"Belegfeld 1"` nach Amazon OrderIDs (Format: XXX-XXXXXXX-XXXXXXX)
- Führt Datenbank-Lookup in JTL durch:
  ```sql
  SELECT cKundennr FROM tAuftrag 
  WHERE cExterneAuftragsnummer = :order_id
  ```
- Ersetzt gefundene OrderIDs durch JTL-Kundennummer
- Markiert verarbeitete Zeilen mit Prüfvermerk:
  - `"Zusatzinformation - Art 1"` = `"Prüfung"`
  - `"Zusatzinformation- Inhalt 1"` = `"AmazonOrderID-Check durchgeführt am DATUM"`

**Dateien:**
- `modules/csv_verarbeiter/services/replacement_service.py`
  - `ersetze_amazon_order_ids()` - Hauptfunktion (Zeile 118-204)
  - `hole_kundennummer_cached()` - DB-Lookup mit Cache (Zeile 70-82)

**Test-Ergebnisse:**
- ✅ OrderID `"306-1234567-8910111"` → Korrekt erkannt
- ✅ OrderID `"028-0317451-0146753"` → Korrekt erkannt
- ✅ Invalide IDs → Korrekt ignoriert

---

### 2. Kritische Gegenkonten-Prüfung (0-20) ✅

**Was passiert:**
- Prüft Spalte `"Gegenkonto (ohne BU-Schlüssel)"`
- Erkennt kritische Konten im Bereich **0-20**
- Warnt im Report über gefundene kritische Konten
- Markiert Output-Dateien mit `"#_"` Präfix wenn kritisches Konto vorhanden

**Dateien:**
- `modules/csv_verarbeiter/services/replacement_service.py`
  - `pruefe_kritische_gegenkonten()` (Zeile 219-234)
  - `ist_kritisches_gegenkonto()` (Zeile 47-58)
- `modules/csv_verarbeiter/services/validation_service.py`
  - `is_critical_account()` (Zeile 50-62)

**Test-Ergebnisse:**
- ✅ Konto `"0"` → Kritisch erkannt
- ✅ Konto `"10"` → Kritisch erkannt
- ✅ Konto `"20"` → Kritisch erkannt
- ✅ Konto `"21"` → OK (nicht kritisch)
- ✅ Konto `"8400"` → OK (nicht kritisch)

---

### 3. CSV-Struktur & Validierung ✅

**Was geprüft wird:**
- **Erforderliche DATEV-Spalten:**
  - `"Belegfeld 1"` (OrderID-Spalte)
  - `"Gegenkonto (ohne BU-Schlüssel)"`
- **OrderID Pattern:** `\d{3}-\d{7}-\d{7}` (Amazon Format)
- **Datenintegrität:** NULL-Werte in Schlüsselspalten
- **Encoding:** Automatische Erkennung (chardet), Output in cp1252 (DATEV-Standard)

**Dateien:**
- `modules/csv_verarbeiter/services/validation_service.py`
  - `validate_csv_structure()` (Zeile 64-94)
  - `validate_order_id_pattern()` (Zeile 27-38)
  - `validate_dataframe()` (Zeile 96-177)
  - `check_data_integrity()` (Zeile 204-229)

---

## 📋 Workflow (Aktuell)

```
1. Upload CSV/ZIP → data/csv_verarbeiter/eingang/
2. Struktur-Validierung (Spalten prüfen)
3. OrderID Pattern-Erkennung
4. DB-Lookup: OrderID → Kundennummer (JTL tAuftrag)
5. Ersetzung durchführen + Prüfmarken setzen
6. Kritische Konten warnen
7. Excel-Report generieren
8. Output → data/csv_verarbeiter/ausgang/
```

---

## 📊 Report-Generierung ✅

**Output:** Excel-Datei mit 4 Sheets:
1. **Zusammenfassung** - Mini-Report mit Gesamtstatistiken
2. **Änderungen** - Liste aller Ersetzungen (Zeile, Alt, Neu)
3. **Nicht gefunden** - OrderIDs ohne JTL-Match
4. **Warnungen** - Kritische Konten, ungültige Patterns

**Dateien:**
- `modules/csv_verarbeiter/services/report_service.py`

---

## 🔧 Konfiguration

**Datei:** `modules/csv_verarbeiter/services/config.py`

```python
# DATEV-Standard
CSV_DELIMITER = ';'                          # Semikolon
CSV_INPUT_ENCODING = 'auto'                  # chardet detection
CSV_OUTPUT_ENCODING = 'cp1252'               # Windows DATEV Standard

# Spalten
DATEV_COLUMN_BELEG = 'Belegfeld 1'           # Amazon OrderID
DATEV_COLUMN_GEGENKONTO = 'Gegenkonto (ohne BU-Schlüssel)'

# Kritische Konten
CRITICAL_ACCOUNT_RANGE = (0, 20)             # Konten 0-20 nicht verändern
```

---

## 🔄 Geplante Änderung (Ab 2026)

### ⚠️ WICHTIG: Refactoring erforderlich!

**Grund:** Ab 2026 nutzen wir nicht mehr Kundennummern, sondern Bestellnummern.

**Aktuell:**
```
Amazon OrderID → JTL Kundennummer (cKundennr)
```

**Zukünftig (geplant):**
```
Amazon OrderID → Bestellnummer (direkt verwenden, kein DB-Lookup nötig)
```

### Betroffene Dateien für Refactoring:

1. **`replacement_service.py`**
   - `hole_kundennummer_cached()` → Überflüssig wenn Bestellnummer verwendet wird
   - `ersetze_amazon_order_ids()` → Logik vereinfachen (kein DB-Lookup mehr)
   - Zusatzfeld-Markierung → Eventuell anpassen/entfernen

2. **`config.py`**
   - Eventuell neue Spalten-Namen für Bestellnummer

3. **`report_service.py`**
   - Report-Texte anpassen ("Kundennummer" → "Bestellnummer")

4. **`README.md`**
   - Dokumentation aktualisieren

### Überlegungen für neue Implementierung:

**Option A:** Bestellnummer = Amazon OrderID (1:1 übernehmen)
- Kein DB-Lookup nötig
- Nur Validierung und kritische Konten prüfen
- Zusatzfelder weglassen oder anpassen

**Option B:** Bestellnummer aus JTL tAuftrag laden
- `SELECT cBestellnr FROM tAuftrag WHERE cExterneAuftragsnummer = :order_id`
- DB-Lookup bleibt, aber andere Spalte

**Empfehlung:** Klären welche Implementierung gewünscht ist, bevor Refactoring beginnt.

---

## 🧪 Test-Status

**Letzter Test:** 13. Februar 2026

✅ Alle Tests bestanden:
- Amazon OrderID Pattern-Erkennung
- Kritische Gegenkonten (0-20)-Erkennung
- CSV-Struktur-Validierung
- Replacement Service Initialisierung
- DataFrame-Validierung
- Zusatzfelder-Markierung

**Test-Script:** `/home/chx/temu/test_csv_verarbeiter.py` (temporär, nach Test entfernt)

---

## 📚 Referenzen

### Hauptdateien:
- `modules/csv_verarbeiter/router.py` - API Endpoints
- `modules/csv_verarbeiter/services/replacement_service.py` - OrderID Ersetzung
- `modules/csv_verarbeiter/services/validation_service.py` - Validierung
- `modules/csv_verarbeiter/services/csv_io_service.py` - CSV I/O
- `modules/csv_verarbeiter/services/report_service.py` - Excel Reports
- `modules/csv_verarbeiter/services/config.py` - Konfiguration

### Frontend:
- `modules/csv_verarbeiter/frontend/csv.html`
- `modules/csv_verarbeiter/frontend/csv.css`
- `modules/csv_verarbeiter/frontend/csv.script.js`

### Dokumentation:
- `modules/csv_verarbeiter/README.md` - Vollständige Modul-Dokumentation
- `docs/CURRENT_STATUS.md` - Projekt-Status (enthält CSV-Verarbeiter-Info)

---

## 💡 Hinweise für Refactoring-Session

1. **Backup erstellen** vor Änderungen
2. **Tests aktualisieren** nach Refactoring
3. **README.md aktualisieren** mit neuer Logik
4. **Frontend anpassen** (Text: "Kundennummer" → "Bestellnummer")
5. **API-Responses prüfen** (alte Feldnamen in JSON?)
6. **Datenbank-Abhängigkeit klären** (brauchen wir überhaupt noch JTL-Lookup?)
7. **Zusatzfelder-Logik überdenken** (noch relevant ohne Ersetzung?)

---

**Ende der Dokumentation**
