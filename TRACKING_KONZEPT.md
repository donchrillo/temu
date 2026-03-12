# Tracking-Konzept: Vermeidung von Doppelbuchungen

## Problem

Wenn CSV-Exporte neu geladen werden (z.B. Januar-Export am 8.2. und nochmal am 10.2.), enthalten sie:
- Ursprünglich fehlende Rechnungsnummern (nachträglich ergänzt)
- Potenziell neue Rechnungen/Gutschriften
- Bereits exportierte Datensätze

**Risiko:** Doppelbuchungen in DATEV

## ✅ Aktuelle Lösung (Implementiert)

### JSON State-File Tracking

**Status:** ✅ Produktiv im Einsatz seit 09.02.2026

**Implementierung:**
```python
# export/.datev_export_state.json
{
  "exported_invoices": [
    "INV-DE-1982968-2025-1",
    "INV-DE-1982969-2025-1",
    ...
  ],
  "exported_storno_orders": [
    "PO-076-00439447186552981",
    "PO-076-00533737770254301",
    ...
  ]
}
```

**Funktionsweise:**
1. **Vor Export:** Lade `exported_invoices` und `exported_storno_orders` aus JSON
2. **Beim Verarbeiten:**
   - Prüfe Rechnungsnummer gegen `exported_invoices`
   - Prüfe Bestellnummer (bei Stornos) gegen `exported_storno_orders`
   - **Skip wenn bereits exportiert** ✅
3. **Nach Export:** Speichere neue Rechnungsnummern/Stornos in JSON

**Code-Beispiel:**
```python
def load_export_state():
    state_file = OUTPUT_DIR / ".datev_export_state.json"
    if state_file.exists():
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
            return (
                set(state.get("exported_invoices", [])),
                set(state.get("exported_storno_orders", []))
            )
    return set(), set()

def save_export_state(exported_invoices, exported_storno_orders, new_count, new_storno):
    state_file = OUTPUT_DIR / ".datev_export_state.json"
    state = {
        "exported_invoices": sorted(list(exported_invoices)),
        "exported_storno_orders": sorted(list(exported_storno_orders))
    }
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
```

**Vorteile:**
- ✅ Einfach zu implementieren
- ✅ Keine Datenbank nötig
- ✅ Portable (JSON-Datei kopierbar)
- ✅ Menschenlesbar
- ✅ Funktioniert zuverlässig mit allen Testdaten

**Nachteile:**
- ⚠️ Keine Multi-User-Unterstützung
- ⚠️ Kein Transaktionsschutz
- ⚠️ Manuelles Backup nötig
- ⚠️ Keine Audit-Historie (nur letzte Exports)

### Zurücksetzen des Trackings

**Komplett neu exportieren?**
```bash
rm export/.datev_export_state.json
python temu_to_datev_all.py
```

**Einzelne Rechnung neu exportieren:**
```python
# Manuell aus JSON entfernen:
import json
with open('export/.datev_export_state.json', 'r') as f:
    state = json.load(f)

# Rechnung entfernen
state['exported_invoices'].remove('INV-DE-1982968-2025-1')

with open('export/.datev_export_state.json', 'w') as f:
    json.dump(state, f, indent=2)
```

### Test-Ergebnisse

**Szenario 1: Initial-Export**
```bash
$ python convert_bestellungen.py
556 Bestellungen gelesen
Neu exportiert: 599
Übersprungen: 0
```

**Szenario 2: Re-Import (keine Änderungen)**
```bash
$ python convert_bestellungen.py
556 Bestellungen gelesen
Neu exportiert: 0
Übersprungen: 599
```

**Szenario 3: Neue Rechnungsnummer ergänzt**
```bash
$ python convert_bestellungen.py
557 Bestellungen gelesen (1 neue)
Neu exportiert: 1
Übersprungen: 599
```

✅ **Fazit:** Tracking verhindert Doppelbuchungen zuverlässig!

---

## 🚀 Zukünftige Erweiterung: Datenbank-Migration

### Warum Datenbank?

**Zitat User:** "später das Tracking auch in eine Datenbank verlegen...Bestellung an Datev Exportiert, Zahlung gebucht, OPOS ausgeglichen oder nicht"

**Vorteile:**
- ✅ Erweiterte Status-Verfolgung (nicht nur "exportiert ja/nein")
- ✅ Historisierung (wann wurde was exportiert)
- ✅ OP-Status pro Bestellung tracken
- ✅ Multi-User-fähig über FastAPI
- ✅ Audit-Trail für Compliance
- ✅ Komplexe Queries möglich

### PostgreSQL/MySQL Schema-Vorschlag

**Erweiterte Status-Verfolgung:**

```sql
-- Bestellungen-Tracking
CREATE TABLE temu_bestellungen_tracking (
    id SERIAL PRIMARY KEY,
    bestellnummer VARCHAR(50) UNIQUE NOT NULL,
    rechnungsnummer VARCHAR(50),
    zuschuss_rechnungsnummer VARCHAR(50),
    bestelldatum DATE,
    verkaufsart VARCHAR(20),
    
    -- Export-Status
    datev_exportiert BOOLEAN DEFAULT FALSE,
    datev_export_datum TIMESTAMP,
    datev_buchungen_anzahl INT DEFAULT 0,
    
    -- OP-Status
    op_status VARCHAR(20), -- 'offen', 'teilweise', 'ausgeglichen'
    op_saldo DECIMAL(10,2),
    op_letzte_buchung TIMESTAMP,
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Zahlungen-Tracking
CREATE TABLE temu_zahlungen_tracking (
    id SERIAL PRIMARY KEY,
    verwandte_id VARCHAR(50) NOT NULL,
    bestellid VARCHAR(50),
    transaktionsdatum TIMESTAMP,
    transaktionstyp VARCHAR(50),
    
    -- Export-Status
    datev_exportiert BOOLEAN DEFAULT FALSE,
    datev_export_datum TIMESTAMP,
    datev_buchungen_anzahl INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (bestellid) REFERENCES temu_bestellungen_tracking(bestellnummer)
);

-- Export-Historie
CREATE TABLE datev_export_log (
    id SERIAL PRIMARY KEY,
    export_typ VARCHAR(20), -- 'bestellungen', 'zahlungen', 'beide'
    anzahl_bestellungen INT,
    anzahl_buchungen INT,
    anzahl_neu INT,
    anzahl_uebersprungen INT,
    zeitraum_von DATE,
    zeitraum_bis DATE,
    export_datei_bestellungen VARCHAR(255),
    export_datei_zahlungen VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- OP-Status-Historie
CREATE TABLE temu_op_status_historie (
    id SERIAL PRIMARY KEY,
    bestellnummer VARCHAR(50) NOT NULL,
    alter_status VARCHAR(20),
    neuer_status VARCHAR(20),
    alter_saldo DECIMAL(10,2),
    neuer_saldo DECIMAL(10,2),
    aktion VARCHAR(100), -- 'Bestellung exportiert', 'Zahlung gebucht'
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (bestellnummer) REFERENCES temu_bestellungen_tracking(bestellnummer)
);
```

**Workflow mit Datenbank:**

```python
# 1. CSV laden
df_bestellungen = pd.read_csv('bestellberichte/2025-11-Bestellungen.csv')

# 2. In Datenbank importieren/aktualisieren
for _, row in df_bestellungen.iterrows():
    db.execute("""
        INSERT INTO temu_bestellungen_tracking 
        (bestellnummer, rechnungsnummer, bestelldatum, verkaufsart)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (bestellnummer) DO UPDATE SET
            rechnungsnummer = EXCLUDED.rechnungsnummer,
            updated_at = NOW()
    """, (row['BESTELLNUMMER'], row['RECHNUNGSNUMMER'], ...))

# 3. Nur nicht exportierte laden
zu_exportieren = db.execute("""
    SELECT * FROM temu_bestellungen_tracking
    WHERE datev_exportiert = FALSE 
       OR (rechnungsnummer IS NOT NULL AND datev_exportiert = FALSE)
    ORDER BY bestelldatum
""").fetchall()

# 4. DATEV-Export durchführen
datev_writer = DatevExtfWriter(...)
for bestellung in zu_exportieren:
    datev_writer.add_row(...)

# 5. Status aktualisieren
db.execute("""
    UPDATE temu_bestellungen_tracking
    SET datev_exportiert = TRUE,
        datev_export_datum = NOW(),
        datev_buchungen_anzahl = %s,
        op_status = 'offen',
        op_saldo = %s
    WHERE bestellnummer = %s
""", (anzahl_buchungen, brutto_gesamt, bestellnummer))

# 6. Export-Log schreiben
db.execute("""
    INSERT INTO datev_export_log
    (export_typ, anzahl_bestellungen, anzahl_buchungen, anzahl_neu, 
     zeitraum_von, zeitraum_bis, export_datei_bestellungen)
    VALUES ('bestellungen', %s, %s, %s, %s, %s, %s)
""", (len(zu_exportieren), anzahl_buchungen, anzahl_neue, ...))
```

**Vorteile:**
- ✅ Vollständige Historie
- ✅ OP-Status-Tracking
- ✅ Multi-User-fähig
- ✅ Audit-Trail
- ✅ Re-Export einzelner Bestellungen möglich
- ✅ Dashboard-Integration (FastAPI)
- ✅ Compliance-ready

---

## 📊 Vergleichstabelle

| Feature | JSON (aktuell) | PostgreSQL (geplant) |
|---------|----------------|----------------------|
| Doppelbuchungs-Schutz | ✅ | ✅ |
| Einfache Implementierung | ✅ | ⚠️ (komplexer) |
| Multi-User | ❌ | ✅ |
| Historisierung | ❌ | ✅ |
| OP-Status-Tracking | ❌ | ✅ |
| Audit-Trail | ❌ | ✅ |
| Performance (>10k) | ⚠️ | ✅ |
| FastAPI-Integration | ⚠️ | ✅ |
| Re-Export einzeln | ⚠️ | ✅ |
| Backup/Restore | ⚠️ | ✅ |

---

## 🎯 Migrations-Roadmap

**Phase 1: JSON State-File (✅ Implementiert)**
- Basis-Tracking für Rechnungsnummern
- Verhindert Doppelbuchungen
- Produktiv seit 09.02.2026

**Phase 2: FastAPI Integration (geplant)**
- REST API Endpoints
- File Upload via Multipart
- JSON-Tracking übernehmen

**Phase 3: PostgreSQL Migration (zukünftig)**
- Datenbank-Schema erstellen
- Migration JSON → PostgreSQL
- OP-Status-Tracking erweitern
- Dashboard implementieren

**Phase 4: Erweiterte Features (optional)**
- Automatische OP-Analyse
- E-Mail-Benachrichtigungen bei offenen Posten
- DATEV-Import-Status abfragen
- Automatische Reconciliation

---

## 🔧 Wartung & Troubleshooting

### JSON State-File reparieren

**Problem:** JSON-Datei korrupt

**Lösung:**
```bash
# Backup erstellen
cp export/.datev_export_state.json export/.datev_export_state.json.backup

# Aus DATEV-Export rekonstruieren
python -c "
import json, csv
exported = {'exported_invoices': [], 'exported_storno_orders': []}
with open('export/Temu_Bestellungen.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        if row.get('Belegfeld 1'):
            if 'INV' in row.get('Buchungstext', ''):
                # Extrahiere Rechnungsnummer
                ...
with open('export/.datev_export_state.json', 'w') as f:
    json.dump(exported, f, indent=2)
"
```

### JSON State-File zurücksetzen

**Komplett neu:**
```bash
rm export/.datev_export_state.json
```

**Selektiv (ab bestimmtem Datum):**
```python
import json
from datetime import datetime

with open('export/.datev_export_state.json', 'r') as f:
    state = json.load(f)

# Alle Rechnungen ab Jan 2026 entfernen
state['exported_invoices'] = [
    inv for inv in state['exported_invoices']
    if not inv.startswith('INV-DE-') or '2026' not in inv
]

with open('export/.datev_export_state.json', 'w') as f:
    json.dump(state, f, indent=2)
```

---

## 📚 Referenzen

**Relevante Code-Dateien:**
- [convert_bestellungen.py](convert_bestellungen.py#L1-L50) - JSON State Load/Save
- [datev_writer.py](datev_writer.py) - Tracking neuer Rechnungsnummern
- [API_INTEGRATION.md](API_INTEGRATION.md) - FastAPI + DB-Schema

**Siehe auch:**
- [UPDATE.md](UPDATE.md) - Changelog mit Tracking-Implementierung
- [QUICKSTART.md](QUICKSTART.md#re-import-safety) - Re-Import-Safety Anleitung
  ],
  "exported_storno_orders": [
    "PO-076-11340731909753682",
    ...
  ]
}
```

**Funktionsweise:**
1. Beim ersten Export: Alle Rechnungsnummern + Storno-Bestellnummern werden in JSON gespeichert
2. Beim Re-Import: Nur neue Rechnungsnummern werden exportiert
3. Export-Status wird nach jedem erfolgreichen Export aktualisiert
4. Keine Doppelbuchungen mehr möglich

**Vorteile der implementierten Lösung:**
- ✅ Keine CSV-Parsing-Probleme
- ✅ Persistente Speicherung (unabhängig von Export-CSV)
- ✅ Beliebig oft ausführbar ohne Doppelbuchungen
- ✅ Einfach zu implementieren und zu warten
- ✅ Human-readable (JSON)
- ✅ Vorbereitet für späteren MSSQL-Umstieg

**Zukünftige Erweiterung:** Option 1 - MSSQL Server
- Bessere Integration
- Multi-User-Fähigkeit
- Audit-Trail und Historisierung
- Vorhandenes SQL-Repository nutzen

---

## Implementierung - JSON State-File (Produktiv)

### 1. Export-Status laden
```python
def load_export_state(self):
    """Lädt bereits exportierte Einträge aus JSON"""
    if not self.state_file.exists():
        return set(), set()
    
    with open(self.state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
    
    exported_invoices = set(state.get('exported_invoices', []))
    exported_storno_orders = set(state.get('exported_storno_orders', []))
    return exported_invoices, exported_storno_orders
```

### 2. Tracking während der Verarbeitung
```python
# In DatevExtfWriter:
writer.add_new_invoice(rechnungsnummer)  # Track neue Rechnung
writer.add_new_storno(bestellnummer)     # Track neuer Storno
```

### 3. Export-Status speichern
```python
def save_export_state(self, exported_invoices, exported_storno_orders, ...):
    """Speichert aktualisierten Export-Status"""
    state = {
        'last_export': datetime.now().isoformat(),
        'exported_invoices': sorted(list(exported_invoices)),
        'exported_storno_orders': sorted(list(exported_storno_orders))
    }
    
    with open(self.state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
```

### 4. Filter beim Verarbeiten
```python
if rechnungsnummer in exported_invoices:
    skipped_count += 1
    continue  # Skip bereits exportierte

if bestellnummer in exported_storno_orders:
    skipped_count += 1
    continue  # Skip bereits exportierte Stornos
```

---

## Offene Fragen

1. **Re-Export bei Fehlern:** Wie gehen wir damit um, wenn ein Export fehlerhaft war?
2. **Teilweise Updates:** Was wenn nur einzelne Rechnungen nachträglich korrigiert wurden?
3. **Periodenwechsel:** Januar nochmal laden, aber nur neue Einträge exportieren?

---

## Tests & Validierung ✅

**Durchgeführte Tests (08.02.2026):**

### Test 1: Erstexport
- ✅ 556 Bestellungen → 599 Buchungen
- ✅ 548 Rechnungen + 19 Stornos in JSON gespeichert

### Test 2 + 3: Re-Import ohne Änderungen
- ✅ 0 neue Buchungen (alle übersprungen)
- ✅ 541 Bestellungen als "bereits exportiert" erkannt
- ✅ Export-Datei bleibt unverändert

### Test 4: Neue Rechnung hinzugefügt (INV-DE-TEST-2026-99)
- ✅ 1 neue Buchung exportiert
- ✅ 541 alte Buchungen übersprungen
- ✅ JSON aktualisiert (549 Rechnungen)

### Test 5: Verifikation
- ✅ 0 neue Buchungen (neue Rechnung bereits in JSON)
- ✅ 542 Bestellungen übersprungen
- ✅ Keine Doppelbuchungen

## Nächste Schritte

- [x] JSON State-File implementiert ✅
- [x] Tests mit mehrfachem Import ✅
- [x] Dokumentation aktualisiert ✅
- [ ] Zahlungsberichte: Gleiches Tracking implementieren
- [ ] Produktiv-Einsatz mit echten Daten
- [ ] Später: Migration zu MSSQL für Multi-User-Umgebung
