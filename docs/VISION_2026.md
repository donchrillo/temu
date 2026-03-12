
Hier ist der Entwurf für deine `VISION_2026.md`. Diese Datei ist darauf ausgelegt, dass ein Senior-Agent sie liest und sofort versteht: *"Alles klar, wir bauen hier modular, sicher und mit dem Ziel der totalen JTL-Unabhängigkeit."*
Das ist ein fantastischer „Deep Dive“. Du hast gerade den kompletten Bauplan für das **TOCI ERP** geliefert. Was du beschreibst, ist der klassische Weg von einem überladenen Legacy-System hin zu einer modernen, spezialisierten **Micro-Services-Architektur** (auch wenn sie in einem Monorepo lebt).


---

# 📄 TOCI ERP – Product Vision Master

**Status:** Draft / Vision-Board
**Ziel:** Schlankes OMS/WMS als Ersatz für JTL-Wawi.

## 1. Markt-Kontext

* **Kanäle:** Amazon (MFN & AFN), Kaufland, Otto, eBay, TEMU.
* **Logik:** Multi-Channel-Vertrieb mit Fokus auf Eigenversand aus lokalem Lager.
* **Problemstellung:** JTL ist zu aufgebläht (Beschaffung, Produktion etc. werden nicht benötigt).

## 2. Kern-Module (The Lean Approach)

### A. Kunden-Management (CRM Light)

* **Struktur:** 1 Kunde → 1 Rechnungsadresse → N Lieferadressen.
* **Historie:** Direkte Sicht auf alle zugehörigen Aufträge.
* **B2B:** Spezial-Handling für Amazon-Sammelaufträge.
* **'TEMU Support:** TEMO verkauft die Artikel manchmal günstiger, und da wir einen Fixpreis mit TEMO ausgehandelt haben, werden dann von TEMO aufgestockt. Somit gibt es theoretisch zwei Aufträge:
1. Einmal an den Kunden über den Verkaufspreis
2. Und dann nochmal den Supportauftrag an TEMO, die die Differenz übernehmen

### B. Verkauf & Auftragsabwicklung (OMS)

* **Filter:** Herkunft, Plattform, Zahlungsart, Status.
* **Dokumente:** Belege kommen meist via API von der Plattform (Amazon, TEMU, Otto). Nur für eBay/Kaufland müssen ggf. eigene PDFs erzeugt werden.
* **Retouren:** Simples Handling direkt aus dem Auftrag heraus (Gutschrift-Trigger).

### C. Lager & Versand (WMS)

* **Versand-Logik:** Filter für lieferbar + bezahlt + Bestand vorhanden.
* **Pick-Prozess:** Intelligente Picklisten nach Versandart (DHL, DPD, Post). Hier auch laufwegsoptimierte Picklisten nach Lagerbereichen, Pickbereichen. 
* **Packtisch:** Scan-Vorgang → Label-Druck → Status-Update an Plattform.
* **Struktur:** Physischer Aufbau (Halle → Regal → Platz).

### D. Artikel-Stamm (PIM Light)

* **Zweck:** Mappen von SKUs/EANs der Plattformen auf interne Artikel für Bestand und Versand.
* **Minimalismus:** Keine Pflege von Marktplatz-Beschreibungen (erfolgt manuell auf der Plattform).
* **INHALTE**: Der Name sollte vorhanden sein, Kurzbeschreibung, ein Bild sollte hinterlegt werden, damit wir auch wissen, um was es sich bei dem Artikel natürlich handelt. 

## 3. Datenbank-Architektur (Audit-Proof)

Das Herzstück des Systems folgt dem **"Raw-to-Core"** Prinzip:

1. **Raw-Layer (Stage):** Jede API-Antwort wird 1:1 als JSON/Raw-Datensatz gespeichert (Nachvollziehbarkeit bei Fehlern).
2. **Transformation:** Ein Service übersetzt Raw-Daten in das TOCI-Schema.
3. **Core-Layer:** Relationale Tabellen für:
* `Customers` (UUID, Billing, Shipping)
* `Orders` (ExternalID, Status, PlatformID)
* `OrderItems` (SKU, Qty, Price)
* `Inventory` (Stock, WarehouseLocation)



---

## 🛠️ Strategische Anweisungen für die Agenten

### 1. Lead Architect Agent (Planung)

* **Aufgabe:** Erstelle die API-Spezifikation für den "Packtisch". Wie sieht der Endpunkt aus, der die Pickliste liefert?
* **Ziel:** 80% Layout-Skelett in React entwerfen, das die oben genannten Punkte (Verkauf, Versand, Lager) direkt als Navigation abbildet.

### 2. Database Agent (Schema-Design)

* **Aufgabe:** Entwirf das MSSQL-Schema für `Orders` und `OrderItems`.
* **Wichtig:** Implementiere das **Raw-Storage-Konzept**. Wir brauchen eine Tabelle `PlatformImports`, die den unverarbeiteten JSON-Body speichert, bevor er in die `Orders` wandert.

---

# 🚀 VISION 2026: TEMU ERP to Independent Multi-Channel OMS

**Datum:** 14. Februar 2026

**Status:** In Transition (Vanilla JS → React 19)

**Ziel:** Ablösung von JTL-Wawi durch ein proprietäres, hochperformantes Order Management System (OMS).

---

## 1. Die Mission: "JTL-Independence"

Dieses Projekt entwickelt sich von einem TEMU-Connector zu einer zentralen Verkaufsplattform. Wir nutzen JTL aktuell nur noch als "Legacy-Druckstation". Jede neue Zeile Code muss darauf einzahlen, dass wir JTL theoretisch morgen abschalten könnten.

---

## 2. Roadmap & Phasen-Plan

### Phase 1: Die Brücke (Aktuell)

* **Backend:** FastAPI liefert Daten für TEMU (Orders, Stock, Tracking).
* **Frontend:** Umstellung von Vanilla-Modulen auf **React 19 SPA**.
* **Auth:** Einführung des **JWT-Cookie-Logins** (HttpOnly), wie im PoC erarbeitet.
* **JTL-Status:** Daten fließen per XML nach JTL; Tracking kommt von JTL zurück.

### Phase 2: Multi-Channel Expansion (Q2-Q3 2026)

* **Anbindung:** Integration von eBay API, Kaufland API und Otto API.
* **Abstraktion:** Alle Marktplätze nutzen das gleiche interne `Order`- und `Product`-Modell.
* **Frontend:** Dashboard zeigt aggregierte Verkaufszahlen über alle Kanäle.

### Phase 3: Versand-Autonomie (Q4 2026+)

* **Direkt-Anbindung:** DHL / DPD API Integration.
* **WMS-Light:** Eigene Picklisten-Generierung und Lagerplatzverwaltung.
* **JTL-Exit:** XML-Export wird deaktiviert. Versandlabels werden direkt aus diesem ERP gedruckt.

---

## 3. Frontend-Architektur (React 19)

Wir übernehmen die Prinzipien aus dem Login-PoC (`cloud.md`). Das Frontend wird eine **Single Page Application (SPA)**.

### Kern-Komponenten & Struktur

* **App Shell:** Zentrales Layout mit Sidebar (Apple-style CSS aus `master.css`).
* **Feature-Ordner (`src/features/`):**
* `auth/`: JWT-Handling & Login (Portierung aus PoC).
* `temu/`: Bestehende Logik, jetzt als React-Dashboards.
* `orders/`: Universelle Bestellansicht (Vorbereitet für eBay/Amazon).
* `inventory/`: Bestandsmanagement.
* `shipping/`: (Placeholder) Picklisten & Label-Druck.



### Sicherheits-Standard (aus PoC)

1. **JWT via httpOnly Cookies:** Kein Zugriff durch JavaScript (XSS-proof).
2. **Strict SameSite:** Schutz vor CSRF.
3. **TypeScript Interfaces:** Jedes API-Objekt (Order, Customer) muss ein TS-Interface haben.

---

## 4. Anweisungen für Frontend-Agenten

Wenn du an diesem Frontend arbeitest, beachte:

1. **Modularität:** Baue Komponenten so, dass sie für TEMU *und* später für eBay funktionieren.
2. **UI/UX:** Bleibe beim "Apple-style" (clean, weiß/grau, abgerundete Ecken, gute Typografie).
3. **Platzhalter:** Erstelle die Navigation bereits für alle Phasen. Module, die noch nicht existieren (z.B. Amazon), werden als `disabled` angezeigt, um die Vision visuell zu festigen.
4. **State Management:** Nutze React Hooks (useState/useEffect) und bei Bedarf Context API für globale Daten (z.B. eingeloggter User).

---

## 5. Backend-Anpassungen (Vorbereitung)

Das Backend muss für React folgende Anforderungen erfüllen:

* **JSON-Only:** Alle Endpunkte müssen strikt `application/json` liefern.
* **CORS:** Erlaube Zugriff vom React-Port (Standard 3000/5173).
* **Auth-Middleware:** Schütze alle `/api/v1/` Routen mit dem JWT-Validator aus dem PoC.

---

### Was du jetzt tun musst (Next Steps):

Damit deine Agenten das umsetzen können, schlage ich folgendes Vorgehen vor:

1. **Datei erstellen:** Speichere den obigen Text als `docs/ARCHITECTURE/VISION_2026.md`.
2. **PoC-Dateien umziehen:** Kopiere die wichtigen Code-Teile aus deinem Login-PoC (besonders `auth.py` fürs Backend und `authService.ts` + `LoginPage.tsx` fürs Frontend) in einen neuen Ordner namens `migration_assets/`.
3. **Den "Senior Frontend Agent" briefen:**
* Gib ihm die `VISION_2026.md`.
* Gib ihm Zugriff auf die Dateien im `migration_assets/` Ordner.
* **Befehl:** *"Initialisiere die neue React-Struktur im Ordner `frontend-new/`. Nutze die Auth-Logik aus den Assets und baue die App-Shell (Navigation) basierend auf der Vision Roadmap."*



**Soll ich dir noch einen spezifischen "System-Prompt" für diesen Senior-Migrations-Agenten schreiben, damit er beim Umzug der Auth-Logik keine Fehler macht?**