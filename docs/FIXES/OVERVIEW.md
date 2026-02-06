# Fixes Overview & Lessons Learned

**Datum:** 6. Februar 2026
**Zweck:** Konsolidierte Übersicht über wichtige behobene Fehler und daraus abgeleitete Best Practices im TEMU-Integrationsprojekt.

---

## 1. Inventory Sync Fixes (2026-02-06)

*   **Problem 1 (Sync Loop):** Die `needs_sync`-Logik im `InventoryRepository` war fehlerhaft. Sie setzte das Flag bei jedem Durchlauf auf `1`, solange der JTL-Bestand `> 0` war, selbst wenn der Bestand bei TEMU bereits korrekt war. Dies führte zu einer unnötigen Endlosschleife. Zudem wurden Bestände von `0` nicht synchronisiert.
*   **Lösung 1:** Anpassung des `MERGE`-Statements. `needs_sync` wird nun nur noch auf `1` gesetzt, wenn `jtl_stock <> temu_stock`. Neue Artikel werden initial mit `needs_sync=1` markiert. Nullbestände werden nun korrekt übertragen.

*   **Problem 2 (JTL Mapping Overwrite):** Beim "Full Sync" (Import neuer Produkte von TEMU) wurden bestehende Verknüpfungen (`jtl_article_id`) in der Datenbank mit `NULL` überschrieben, da die TEMU-API diese Information nicht liefert. Dies zwang das System, bei jedem Lauf alle Mappings neu (und langsam) aufzubauen.
*   **Lösung 2:** Nutzung von `COALESCE(src.jtl_article_id, target.jtl_article_id)` im `MERGE`-Statement des `ProductRepository`. Bestehende IDs bleiben nun erhalten, wenn die Quelle `NULL` liefert.

*   **Problem 3 (Transaktions-Locks):** Der gesamte Inventory-Workflow lief in einer einzigen, langen Datenbank-Transaktion. Dies führte zu potenziellen Locks und blockierte Updates.
*   **Lösung 3:** Umbau des `InventoryWorkflowService` auf **Transaction Splitting**. Der Workflow ist nun in drei unabhängige Blöcke unterteilt (Import, JTL-Update, API-Sync), die jeweils separat committen.

*   **Problem 4 (API Batching & Robustheit):**
    *   *Erkenntnis:* Der TEMU-Endpunkt `bg.local.goods.stock.edit` unterstützt **keine** gemischten Batches mit unterschiedlichen `goodsId` (Vater-Artikel-IDs) in einem einzigen Request, wenn die `goodsId` nicht im Top-Level-Parameter steht. Ein Versuch, dies zu implementieren, führte zum Fehler `Invalid Request Parameters`.
    *   *Lösung:* Rückkehr zur Gruppierung der Updates nach `goodsId` (ein Request pro Vater-Artikel).
    *   *Optimierung:* Um Datenverlust bei Verbindungsabbrüchen zu vermeiden, wird der Status `mark_synced` in der Datenbank nun **sofort nach jedem erfolgreichen Teil-Update** (pro `goodsId`-Gruppe) geschrieben, anstatt erst am Ende des gesamten Jobs.

---

## 2. Frontend Cache Fix (2026-02-03)

*   **Problem:** Ein Multi-Layer-Caching-Problem (Caddy Reverse Proxy, Service Worker, Browser HTTP Cache) verhinderte, dass Frontend-Updates und Logs im Browser korrekt angezeigt wurden. Dies führte zu einer inkonsistenten Benutzererfahrung.
*   **Lösung:**
    *   **Caddy:** Explizite `no-cache`-Regeln für `/api/*`-Endpunkte und reduzierte Cache-Zeiten für statische Moduldateien.
    *   **Service Worker:** Erhöhung der Cache-Version und Hinzufügen von Query-Parametern (`?v=YYYYMMDD`) zu allen statischen Assets, um Cache-Invalidierung zu erzwingen und URL-Mismatches zu vermeiden. API-Aufrufe wurden explizit vom Caching ausgeschlossen.
    *   **Frontend HTML:** Anpassung der `<script>`- und `<link>`-Tags in HTML-Dateien zur Verwendung von Query-Parametern für Cache-Busting.
*   **Lessons Learned:** Multi-Layer-Caching ist komplex; konsistente Cache-Busting-Strategien über alle Schichten hinweg sind unerlässlich. Caddy Matcher-Reihenfolge ist kritisch. API-Responses sollten niemals gecacht werden. Der Inkognito-Modus des Browsers ist ein nützliches Debugging-Tool.

---

## 3. PDF Reader Fixes

### 3.1 Vereinfachung Dateinamen-Handling (2026-02-05)
*   **Problem:** Die ursprüngliche Implementierung nutzte ein komplexes `filename_mapping.json` System, um temporäre Dateien umzubenennen, was zu unnötiger Komplexität führte.
*   **Lösung:** Das Mapping wurde entfernt. Extrahierte Seiten werden nun direkt unter dem Originaldateinamen im `TMP_ORDNER` gespeichert. Dies vereinfacht den Workflow massiv und eliminiert eine Fehlerquelle.
*   **Lessons Learned:** Keep it simple. Wenn der Originalname erhalten bleiben soll, speichere ihn direkt so, statt Mapping-Layer zu bauen.

### 3.2 Import-Fehler `app_logger`
*   **Problem:** Der Server startete aufgrund eines `ImportError` (`cannot import name 'app_logger' from 'src.services.logger'`).
*   **Lösung:** Die Logging-Architektur wurde am 05.02.2026 komplett refactored. Es gibt nun einen zentralen `log_service` (DB) für Business-Events und `app_logger` (File) für technische Errors. Redundante Logger-Dateien wurden entfernt.
*   **Lessons Learned:** Zentrale Infrastruktur (`modules/shared`) muss sauber definiert sein. Circular Imports vermeiden durch strikte Trennung von Factory und Instanz.

### 3.3 Dezimaltrennzeichen für GBP/USD
*   **Problem:** UK-Rechnungen (GBP) mit Dezimalpunkten wurden in Excel falsch geparst.
*   **Lösung:** Eine währungsbewusste Hilfsfunktion `parse_amount` wurde implementiert. Zusätzlich wurde am 05.02.2026 eine `parse_amount_local` Funktion ergänzt, die anhand des Ländercodes (z.B. 'de' vs 'uk') entscheidet, ob Punkt oder Komma das Dezimaltrennzeichen ist.

### 3.4 Verbesserte Erkennung & Extraktion (2026-02-05)
*   **Problem:** Bestimmte deutsche Rechnungen (z.B. Amazon VCS Layouts) und UK-Werberechnungen wurden nicht als solche erkannt oder die Beträge wurden nicht extrahiert, da sie von den Standard-Patterns abwichen (z.B. "Rechnung Nr." statt "Rechnungsnummer:", tabellarisches Layout statt Zeilen-Format).
*   **Lösung:**
    *   **Erkennung:** Robuste Fallback-Regeln in `document_identifier.py` hinzugefügt (z.B. Prüfung auf "Gesamtbetrag" oder "Rechnung Nr.").
    *   **Extraktion:** Neue Fallback-Logik in `rechnungen_service.py` implementiert, die gezielt nach Einzelwerten (Netto, Steuer, Brutto) sucht, falls das strikte Zeilen-Regex fehlschlägt.

---

## 4. Transaction Isolation Bug Fix (2026-01-26)

*   **Problem:** Ein kritischer Fehler aufgrund des `READ COMMITTED` Transaktions-Isolationslevels des SQL Servers führte dazu, dass Bestellartikel-Positionen, die in einem Schritt geschrieben, aber noch nicht committed wurden, nicht vom nachfolgenden Schritt innerhalb derselben Transaktion gelesen werden konnten. Dies resultierte in unvollständigen XML-Exporten für JTL.
*   **Lösung:** Die Transaktionsgrenzen im `order_workflow_service.py` wurden angepasst. Ein expliziter `COMMIT` wurde nach dem Schreiben der Daten in die Datenbank (Step 2) eingefügt. Der nachfolgende Schritt (Step 3: XML-Export) operiert nun in einer neuen Transaktion auf bereits committeden Daten.
*   **Lessons Learned:**
    *   **Transaktionsgrenzen bewusst setzen:** Bei `Read-After-Write`-Operationen ist es entscheidend, einen `COMMIT` zwischen den Schreib- und Leseschritten durchzuführen.
    *   **Vermeidung langer Transaktionen:** Lange Transaktionen können die Concurrency beeinträchtigen und das Risiko von Locks oder Rollbacks erhöhen.
    *   **Zusätzliche Failsafes:** Fallback-Lookups sind nützliche Sicherheitsnetze, ersetzen aber nicht die Notwendigkeit einer korrekten Transaktionsverwaltung.
*   **Details:** Keine DB-Schema-, Config- oder Dependency-Änderungen erforderlich; es war eine reine Code-Architektur-Anpassung.