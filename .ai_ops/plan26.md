Das ist ein hervorragender Plan. Wir bauen jetzt das **architektonische Bindeglied** zwischen deinem hochgradig funktionalen Backend-Dampfhammer (dem TEMU ERP) und deiner neuen, modernen React-Steuereinheit.

Hier ist der Entwurf für deine `docs/ARCHITECTURE/VISION_2026.md`. Diese Datei ist darauf ausgelegt, dass ein Senior-Agent sie liest und sofort versteht: *"Alles klar, wir bauen hier modular, sicher und mit dem Ziel der totalen JTL-Unabhängigkeit."*

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