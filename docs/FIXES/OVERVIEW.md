# Fixes Overview & Lessons Learned

**Datum:** 5. Februar 2026
**Zweck:** Konsolidierte Übersicht über wichtige behobene Fehler und daraus abgeleitete Best Practices im TEMU-Integrationsprojekt.

---

## 1. Frontend Cache Fix (2026-02-03)

*   **Problem:** Ein Multi-Layer-Caching-Problem (Caddy Reverse Proxy, Service Worker, Browser HTTP Cache) verhinderte, dass Frontend-Updates und Logs im Browser korrekt angezeigt wurden. Dies führte zu einer inkonsistenten Benutzererfahrung.
*   **Lösung:**
    *   **Caddy:** Explizite `no-cache`-Regeln für `/api/*`-Endpunkte und reduzierte Cache-Zeiten für statische Moduldateien.
    *   **Service Worker:** Erhöhung der Cache-Version und Hinzufügen von Query-Parametern (`?v=YYYYMMDD`) zu allen statischen Assets, um Cache-Invalidierung zu erzwingen und URL-Mismatches zu vermeiden. API-Aufrufe wurden explizit vom Caching ausgeschlossen.
    *   **Frontend HTML:** Anpassung der `<script>`- und `<link>`-Tags in HTML-Dateien zur Verwendung von Query-Parametern für Cache-Busting.
*   **Lessons Learned:** Multi-Layer-Caching ist komplex; konsistente Cache-Busting-Strategien über alle Schichten hinweg sind unerlässlich. Caddy Matcher-Reihenfolge ist kritisch. API-Responses sollten niemals gecacht werden. Der Inkognito-Modus des Browsers ist ein nützliches Debugging-Tool.

---

## 2. PDF Reader Fixes (2026-02-02)

### 2.1 Dateinamen-Mapping für Werbungsrechnungen
*   **Problem:** Die Excel-Ausgabe von Werbungsrechnungen zeigte den intern umbenannten Dateinamen (`country_code_start_date_end_date.pdf`) anstelle des ursprünglichen Dateinamens der hochgeladenen PDF-Datei.
*   **Lösung:** Eine `filename_mapping.json`-Datei wurde im temporären Verzeichnis (`TMP_ORDNER`) implementiert, die den umbenannten Pfad dem ursprünglichen Dateinamen zuordnet. Der `werbung_extraction_service.py` erstellt dieses Mapping, und der `werbung_service.py` verwendet es, um den ursprünglichen Dateinamen im Excel-Export anzuzeigen.
*   **Lessons Learned:** Sicherstellung der Datenkonsistenz und -nachvollziehbarkeit über verschiedene Verarbeitungsstufen hinweg, insbesondere bei Dateiumbenennungen.

### 2.2 Import-Fehler `app_logger`
*   **Problem:** Der Server startete aufgrund eines `ImportError` (`cannot import name 'app_logger' from 'src.services.logger'`).
*   **Lösung:** Der Importpfad in `api/server.py` wurde von `from src.services.logger import app_logger` zu `from src.services import app_logger` korrigiert.
*   **Lessons Learned:** Die genaue Kenntnis der Modulstruktur und der korrekten Importpfade ist entscheidend, besonders in komplexen Projekten. (Hinweis: Die Struktur wurde im Zuge der Monorepo-Migration weiter geändert; der korrekte Pfad ist nun `modules.shared.logging.logger` oder `modules.shared.logging`).

### 2.3 Dezimaltrennzeichen für GBP/USD
*   **Problem:** UK-Rechnungen (GBP) mit Dezimalpunkten (z.B. `121.22 GBP`) wurden in Excel falsch geparst und angezeigt (z.B. `12.122,00 GBP`), da die Logik das Komma als standardmäßiges Dezimaltrennzeichen annahm.
*   **Lösung:** Eine währungsbewusste Hilfsfunktion `parse_amount(amount_str, currency)` wurde in `src/modules/pdf_reader/werbung_service.py` (jetzt `modules/pdf_reader/services/werbung_service.py`) implementiert, die das korrekte Dezimaltrennzeichen basierend auf der Währung erkennt und anwendet (Punkt für GBP/USD, Komma für EUR/SEK/PLN).
*   **Lessons Learned:** Bei der Verarbeitung internationaler Daten müssen lokale Formatierungskonventionen (insbesondere für Zahlen und Währungen) explizit berücksichtigt werden, um Datenintegrität zu gewährleisten.

---

## 3. Transaction Isolation Bug Fix (2026-01-26)

*   **Problem:** Ein kritischer Fehler aufgrund des `READ COMMITTED` Transaktions-Isolationslevels des SQL Servers führte dazu, dass Bestellartikel-Positionen, die in einem Schritt geschrieben, aber noch nicht committed wurden, nicht vom nachfolgenden Schritt innerhalb derselben Transaktion gelesen werden konnten. Dies resultierte in unvollständigen XML-Exporten für JTL.
*   **Lösung:** Die Transaktionsgrenzen im `order_workflow_service.py` wurden angepasst. Ein expliziter `COMMIT` wurde nach dem Schreiben der Daten in die Datenbank (Step 2) eingefügt. Der nachfolgende Schritt (Step 3: XML-Export) operiert nun in einer neuen Transaktion auf bereits committeden Daten.
*   **Lessons Learned:**
    *   **Transaktionsgrenzen bewusst setzen:** Bei `Read-After-Write`-Operationen ist es entscheidend, einen `COMMIT` zwischen den Schreib- und Leseschritten durchzuführen.
    *   **Vermeidung langer Transaktionen:** Lange Transaktionen können die Concurrency beeinträchtigen und das Risiko von Locks oder Rollbacks erhöhen.
    *   **Zusätzliche Failsafes:** Fallback-Lookups sind nützliche Sicherheitsnetze, ersetzen aber nicht die Notwendigkeit einer korrekten Transaktionsverwaltung.
*   **Details:** Keine DB-Schema-, Config- oder Dependency-Änderungen erforderlich; es war eine reine Code-Architektur-Anpassung.
