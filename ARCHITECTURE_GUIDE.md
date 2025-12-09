# TEMU ERP System - Architecture & Learning Guide

## 📋 Inhaltsverzeichnis

1. [Executive Summary](#executive-summary)
2. [Dein Learning Journey](#dein-learning-journey)
3. [Core Concepts](#core-concepts)
4. [Projekt Struktur](#projekt-struktur)
5. [Architektur Deep Dive](#architektur-deep-dive)
6. [Code Patterns](#code-patterns)
7. [Nächste Schritte](#nächste-schritte)

---

## Executive Summary

Du hast ein **Enterprise-Grade Backend-System** aufgebaut mit:
- ✅ **Repository Pattern** (Datenbankzugriffe isoliert)
- ✅ **Service Layer** (Business Logic zentral)
- ✅ **Marketplace Connector Architecture** (Plugin-System)
- ✅ **Workflow Orchestration** (5-Schritt Prozess)
- ✅ **FastAPI Dashboard** mit APScheduler
- ✅ **Production-Ready** Code

**Status: ALLE TESTS BESTANDEN ✓**

---

## Dein Learning Journey

### Was war dein Ausgangspunkt?

```
PROBLEM: Altes Code-Design
├── services/api_sync_service.py       ← DB Code + Business Logic VERMISCHT
├── services/xml_generator_service.py  ← DB Code + Business Logic VERMISCHT
├── services/tracking_service.py       ← DB Code + Business Logic VERMISCHT
└── services/api_export_service.py     ← DB Code + Business Logic VERMISCHT

RESULTAT: 
├── Nicht testbar (alles ist verkoppelt)
├── Nicht wartbar (änderungen überall nötig)
├── Nicht skalierbar (neue Features = Chaos)
└── Für ERP nicht geeignet
```

### Wo bist du jetzt?

```
LÖSUNG: Neue Clean Architecture
├── src/marketplace_connectors/temu/   ← API Integration (Plugin)
├── src/modules/orders/                ← Business Logic (Orders)
├── src/modules/tracking/              ← Business Logic (Tracking)
├── src/modules/xml_export/            ← Business Logic (XML)
├── src/db/repositories/               ← Data Access Layer
└── workflows/                         ← Orchestration

RESULTAT:
├── ✓ Testbar (jede Schicht isoliert)
├── ✓ Wartbar (änderungen nur in einer Schicht)
├── ✓ Skalierbar (neue Marketplaces/Module einfach)
└── ✓ ERP-ready (Basis für komplexe Systeme)
```

---

## Core Concepts

### 1. Layer Architecture (4-Schicht Modell)

```
┌─────────────────────────────────────┐
│ 1. API Layer (FastAPI Routes)       │ ← Frontend Communication
│    - HTTP Requests/Responses        │
│    - Validierung mit Schemas        │
│    - Status Codes                   │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 2. Service Layer (Business Logic)   │ ← Kernlogik
│    - Order Processing               │
│    - Validierung & Transformation   │
│    - Geschäftsregeln                │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 3. Repository Layer (Data Access)   │ ← DB Zugriff
│    - SELECT/INSERT/UPDATE           │
│    - ORM Operationen                │
│    - Query Building                 │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 4. Database                         │ ← Persistierung
│    - SQL Server (TOCI, JTL)         │
└─────────────────────────────────────┘
```

**Warum ist das wichtig?**

- **Separation of Concerns**: Jede Schicht hat eine Aufgabe
- **Testability**: Jede Schicht kann isoliert getestet werden
- **Maintainability**: Änderungen in einer Schicht beeinflussen andere nicht
- **Scalability**: Neue Features ohne alten Code zu ändern

### 2. Repository Pattern

**Problem:** DB-Code überall im Projekt verteilt

```python
# ❌ SCHLECHT (old)
def import_orders(api_response):
    conn = get_db_connection()  # DB Code hier
    cursor = conn.cursor()
    
    order = parse(api_response)  # Business Logic hier
    
    cursor.execute("INSERT ...")  # DB Code hier
```

**Lösung:** Repository = DB-Abstraktions-Schicht

```python
# ✅ GUT (new)
class OrderRepository:
    """ONLY DB Operationen"""
    def save(self, order: Order) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT ...")
        return cursor.lastrowid

class OrderService:
    """ONLY Business Logic"""
    def __init__(self, repo: OrderRepository):
        self.repo = repo  # Delegiere zu Repository
    
    def import_orders(self, api_response):
        order = self.parse(api_response)  # Business Logic
        return self.repo.save(order)      # DB Zugriff delegiert
```

**Vorteile:**
- DB Code ist zentral
- Service kennt nicht wie DB funktioniert
- Testbar: Mock Repository in Tests
- Datenbankwechsel: Nur Repository anpassen

### 3. Service Layer (Business Logic)

**Aufgabe:** Geschäftslogik zentral

```python
class OrderService:
    def import_from_api_response(self, responses):
        """Business Logic: API Response → Order"""
        imported = 0
        
        for response in responses:
            # Validierung
            if not response.get('success'):
                continue
            
            # Parsing
            order = self.parse_response(response)
            
            # Persistierung (delegiert zu Repository!)
            self.repo.save(order)
            imported += 1
        
        return {'imported': imported}
```

**Nicht die Aufgabe des Service:**
- ❌ SQL Queries schreiben
- ❌ HTTP Requests machen (schon erledigt)
- ❌ Dateien schreiben (andere Services)

### 4. Marketplace Connector Architecture (Plugin System)

**Problem:** Jeder Marketplace (TEMU, Amazon, eBay) hat andere APIs

**Lösung:** Abstract Base Class + Concrete Implementations

```python
# Alle Marketplaces implementieren gleiche Schnittstelle
class BaseMarketplaceConnector(ABC):
    @abstractmethod
    def fetch_orders(self, **kwargs) -> bool:
        pass
    
    @abstractmethod
    def upload_tracking(self, data) -> bool:
        pass

# TEMU implementiert diese Schnittstelle
class TemuMarketplaceService(BaseMarketplaceConnector):
    def fetch_orders(self, parent_order_status, days_back):
        # TEMU spezifische Implementierung
        pass
    
    def upload_tracking(self, tracking_data):
        # TEMU spezifische Implementierung
        pass

# In Zukunft: Amazon implementiert gleiche Schnittstelle
class AmazonMarketplaceService(BaseMarketplaceConnector):
    def fetch_orders(self, ...):
        # Amazon spezifische Implementierung
        pass
```

**Vorteil für ERP-Skalierung:**
- Neue Marketplace = Neue Datei, alte Code unverändert
- Services nutzen `BaseMarketplaceConnector`, nicht spezifische Implementierung
- Easy to add: Shopify, WooCommerce, Ebay, etc.

---

## Projekt Struktur

### Finale Architektur

```
temu/
│
├── main.py                          ← CLI Entry Point (Workflows orchestrieren)
├── config/                          ← Settings & .env
├── db/                              ← Database Connection Layer
│   ├── connection.py
│   └── __init__.py
│
├── src/                             ← Application Code
│   ├── marketplace_connectors/      ← 🆕 Plugin Architecture!
│   │   ├── base_connector.py        ← Abstract Base Class
│   │   └── temu/
│   │       ├── api_client.py        ← HTTP Client
│   │       ├── orders_api.py        ← TEMU Endpoints
│   │       ├── signature.py         ← TEMU Authentifizierung
│   │       ├── service.py           ← TEMU Marketplace Service
│   │       └── __init__.py
│   │
│   ├── db/repositories/             ← 🆕 Data Access Layer
│   │   ├── order_repository.py
│   │   ├── order_item_repository.py
│   │   └── __init__.py
│   │
│   ├── modules/                     ← 🆕 Business Logic Services
│   │   ├── orders/
│   │   │   ├── service.py
│   │   │   └── __init__.py
│   │   ├── tracking/
│   │   │   ├── service.py
│   │   │   └── __init__.py
│   │   ├── xml_export/
│   │   │   ├── service.py
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   └── __init__.py
│
├── dashboard/                       ← APScheduler + Job Management
│   ├── scheduler.py
│   ├── jobs.py
│   └── __init__.py
│
├── api/                             ← FastAPI Dashboard
│   └── main.py
│
├── workflows/                       ← Orchestration Layer
│   ├── api_to_json.py              ← Step 1: TEMU API → JSON
│   ├── json_to_db.py               ← Step 2: JSON → DB
│   ├── db_orders_to_xml.py         ← Step 3: DB → XML/JTL
│   ├── tracking_to_db.py           ← Step 4: JTL → Tracking
│   ├── db_tracking_to_api.py       ← Step 5: Tracking → TEMU API
│   └── __init__.py
│
├── frontend/                        ← Vue3 Dashboard UI
│   └── index.html
│
├── data/                            ← Generated Output
│   └── api_responses/
│
├── tests/                           ← Test Suite
│   └── test_refactored.py
│
└── services/                        ← (leer - für zukünftige Services)
```

### Datenfluss im System

```
┌──────────────────┐
│   TEMU API       │
└────────┬─────────┘
         │
         ↓ (Step 1)
   ┌─────────────┐
   │ api_to_json │ ← TemuMarketplaceService.fetch_orders()
   └──────┬──────┘
          │ (JSON speichern)
          ↓ (Step 2)
    ┌──────────────┐
    │  json_to_db  │ ← OrderService.import_from_api_response()
    └──────┬───────┘
           │ (Insert/Update DB)
           ↓ (Step 3)
     ┌──────────────┐
     │ db_to_xml    │ ← XmlExportService.export_to_xml()
     └──────┬───────┘
            │ (Generate XML + JTL Import)
            ↓ (Step 4)
      ┌──────────────┐
      │ tracking_db  │ ← TrackingService.update_from_jtl()
      └──────┬───────┘
             │ (Update Tracking in DB)
             ↓ (Step 5)
        ┌────────────────┐
        │ db_to_api      │ ← TemuMarketplaceService.upload_tracking()
        └────────┬───────┘
                 │
                 ↓
         ┌───────────────┐
         │   TEMU API    │
         └───────────────┘
```

---

## Architektur Deep Dive

### 1. Repository Pattern Beispiel

**Problem:** Komplexe SQL Queries überall im Code

**Lösung:**

```python
# src/db/repositories/order_repository.py
class Order:
    """Domain Model - unabhängig von DB"""
    def __init__(self, id, bestell_id, email, status):
        self.id = id
        self.bestell_id = bestell_id
        self.email = email
        self.status = status

class OrderRepository:
    """Data Access Layer - ONLY DB Operations"""
    
    def find_by_bestell_id(self, bestell_id: str) -> Optional[Order]:
        """Hole Order aus DB"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ... WHERE bestell_id = ?", bestell_id)
        row = cursor.fetchone()
        return self._map_to_order(row) if row else None
    
    def save(self, order: Order) -> int:
        """INSERT oder UPDATE"""
        # ... DB Code ...
        return order_id
    
    def find_by_status(self, status: str) -> List[Order]:
        """Hole alle Orders mit Status"""
        # ... DB Code ...
        return orders
    
    def _map_to_order(self, row) -> Order:
        """Konvertiere DB Row zu Order Object"""
        return Order(row[0], row[1], row[2], row[3])

# ===== Service Layer =====
# Services wissen NICHT wie DB funktioniert!
class OrderService:
    def __init__(self, repo: OrderRepository):
        self.repo = repo  # Dependency Injection
    
    def import_orders(self, api_data):
        for item in api_data:
            order = Order(
                id=None,
                bestell_id=item['order_sn'],
                email=item['email'],
                status='imported'
            )
            self.repo.save(order)  # Delegiere zu Repo!
```

**Vorteile:**
- ✅ Service hat ZERO DB Code
- ✅ Testbar: Mock Repository
- ✅ Wartbar: DB Logic ist zentral
- ✅ Skalierbar: Neuer Marketplace nutzt same Repo

### 2. Service Layer Beispiel

```python
# src/modules/orders/service.py
class OrderService:
    """Business Logic - ONLY Order Processing"""
    
    def __init__(self, order_repo, item_repo):
        self.order_repo = order_repo
        self.item_repo = item_repo
    
    def import_from_api_response(self, api_responses):
        """Business Logic: API Response → Order"""
        imported = 0
        
        for response in api_responses:
            # 1. Validierung
            if not response.get('success'):
                continue
            
            # 2. Parsing
            result = response.get('result', {})
            order_sn = result.get('orderSn')
            
            # 3. Business Logic: Existing Order?
            existing = self.order_repo.find_by_bestell_id(order_sn)
            
            # 4. Business Logic: Map Status
            status = self._map_status(
                result.get('parentOrderStatus', 2)
            )
            
            # 5. Create Order Model
            order = Order(
                id=existing.id if existing else None,
                bestell_id=order_sn,
                status=status
            )
            
            # 6. Persistierung (delegiert!)
            self.order_repo.save(order)
            imported += 1
        
        return {'imported': imported}
    
    def _map_status(self, status_code):
        """Geschäftslogik: Status Code Mapping"""
        mapping = {
            1: 'pending',
            2: 'processing',
            3: 'cancelled',
            4: 'shipped'
        }
        return mapping.get(status_code, 'unknown')
```

### 3. Marketplace Connector Architecture

```python
# src/marketplace_connectors/base_connector.py
class BaseMarketplaceConnector(ABC):
    """Abstract Interface - alle Marketplaces müssen implementieren"""
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        pass
    
    @abstractmethod
    def fetch_orders(self, **kwargs) -> bool:
        pass
    
    @abstractmethod
    def upload_tracking(self, data) -> bool:
        pass

# ===== TEMU Implementation =====
# src/marketplace_connectors/temu/service.py
class TemuMarketplaceService(BaseMarketplaceConnector):
    """TEMU specific implementation"""
    
    def __init__(self, app_key, app_secret, token, endpoint):
        self.client = TemuApiClient(app_key, app_secret, token, endpoint)
        self.orders_api = TemuOrdersApi(self.client)
    
    def validate_credentials(self) -> bool:
        return all([self.app_key, self.app_secret, self.access_token])
    
    def fetch_orders(self, parent_order_status, days_back):
        """TEMU specific: fetch orders"""
        orders = self.orders_api.get_orders(
            parent_order_status=parent_order_status,
            days_back=days_back
        )
        # Save to JSON
        return True
    
    def upload_tracking(self, tracking_data):
        """TEMU specific: upload tracking"""
        return self.orders_api.upload_tracking_data(tracking_data)

# ===== FUTURE: Amazon Implementation =====
# src/marketplace_connectors/amazon/service.py
class AmazonMarketplaceService(BaseMarketplaceConnector):
    """Amazon specific implementation"""
    
    def validate_credentials(self) -> bool:
        # Amazon validation
        pass
    
    def fetch_orders(self, **kwargs) -> bool:
        # Amazon fetch logic
        pass
    
    def upload_tracking(self, data) -> bool:
        # Amazon upload logic
        pass

# ===== In Workflows: Marketplace-agnostic =====
# workflows/api_to_json.py
def run_api_to_json(marketplace: str = 'temu'):
    if marketplace == 'temu':
        service = TemuMarketplaceService(...)
    elif marketplace == 'amazon':
        service = AmazonMarketplaceService(...)
    
    # Alle implementieren BaseMarketplaceConnector!
    return service.fetch_orders()
```

**SEHR WICHTIG:** Diese Struktur ermöglicht:
- Neue Marketplaces ohne alten Code zu ändern
- Alle nutzen gleiche Schnittstelle
- Leicht zu testen
- Für großes ERP skalierbar!

---

## Code Patterns

### Pattern 1: Dependency Injection

```python
# ❌ SCHLECHT (hardcoded dependencies)
class OrderService:
    def __init__(self):
        self.repo = OrderRepository()  # Fest
    
    def process(self):
        self.repo.save(order)

# ✅ GUT (injected dependencies)
class OrderService:
    def __init__(self, repo: OrderRepository = None):
        self.repo = repo or OrderRepository()  # Injizierbar
    
    def process(self):
        self.repo.save(order)

# Usage:
# Produktion:
service = OrderService()

# Tests:
mock_repo = MockOrderRepository()
service = OrderService(repo=mock_repo)
```

**Warum wichtig?**
- Testbar: Mock Dependencies in Tests
- Flexibel: Verschiedene Implementierungen
- Wartbar: Abhängigkeiten explizit

### Pattern 2: Domain Models

```python
# Domain Model (nicht DB-spezifisch!)
class Order:
    def __init__(self, id, bestell_id, email, status):
        self.id = id
        self.bestell_id = bestell_id
        self.email = email
        self.status = status

# Vorteil:
# - Services arbeiten mit Order (nicht SQL Rows)
# - Order kann überall genutzt werden
# - Leicht zu verstehen & testen
```

### Pattern 3: Service Orchestration

```python
# workflows/main.py - Orchestriert mehrere Services
def run_full_workflow():
    # Step 1: Marketplace Connector
    temu_service = TemuMarketplaceService(...)
    temu_service.fetch_orders()
    
    # Step 2: Business Logic
    order_service = OrderService(order_repo, item_repo)
    order_service.import_from_api_response(api_data)
    
    # Step 3: More Business Logic
    xml_service = XmlExportService(order_repo, item_repo)
    xml_service.export_to_xml()
    
    # Step 4: More Business Logic
    tracking_service = TrackingService(order_repo)
    tracking_service.update_from_jtl()
    
    # Step 5: Export Back
    temu_service.upload_tracking(tracking_data)
```

---

## Nächste Schritte

### Kurzfristig (nächste Sessions)

1. **Option A: Weiteres Learning**
   - Pydantic Schemas (Input Validation)
   - API Routes (modularisierte Endpoints)
   - Testing (Unit Tests schreiben)
   - Logging (Structured Logging)

2. **Option B: Neue Features**
   - Second Marketplace (Amazon, eBay)
   - Inventory Management Module
   - Customer Management
   - Dashboard UI Features

3. **Option C: Dokumentation**
   - README schreiben
   - API Docs (Auto-generated)
   - Architecture Decision Records (ADR)

### Mittelfristig (Wochen)

- [ ] Produktiv gehen (live deployment)
- [ ] Monitoring & Alerts
- [ ] Performance Optimization
- [ ] Error Handling erweitern

### Langfristig (ERP Vision)

```
ERP System Structure:
├── marketplace_connectors/
│   ├── temu/
│   ├── amazon/
│   ├── ebay/
│   └── woocommerce/
├── modules/
│   ├── orders/
│   ├── inventory/
│   ├── customers/
│   ├── accounting/
│   ├── reports/
│   └── ...
├── api/
│   └── routes/
├── dashboard/
└── integrations/
```

---

## Wichtige Lernpunkte zusammengefasst

### 1. Die 4-Schicht Architektur ist GOLD

```
API Routes → Services → Repositories → Database

Jede Schicht hat EINE Aufgabe:
- API: HTTP Kommunikation
- Service: Business Logic
- Repository: DB Operations
- Database: Persistierung
```

### 2. Repository Pattern = Testbar + Wartbar

```
Service kennt nicht wie DB funktioniert!
Service delegiert zu Repository.
Repository isoliert alle DB Operations.
```

### 3. Marketplace Connector = Skalierbar

```
BaseMarketplaceConnector = Interface
TemuMarketplaceService = Implementierung

Neue Marketplace:
1. Create new dir: src/marketplace_connectors/amazon/
2. Implement BaseMarketplaceConnector
3. Workflows nutzen gleiche Schnittstelle
4. Alter Code UNVERÄNDERT!
```

### 4. Workflows = Orchestration

```
main.py ruft Workflows auf
Workflows koordinieren Services
Services machen Business Logic
Repositories machen DB Zugriff

Einfach zu verstehen & erweitern!
```

---

## Ressourcen für tieferes Lernen

### Design Patterns
- **Repository Pattern**: Zentral für Data Access
- **Service Layer Pattern**: Für Business Logic
- **Dependency Injection**: Für Testability
- **Abstract Base Classes**: Für Plugin Architecture

### Best Practices
- **Clean Code**: Jede Klasse = Eine Aufgabe
- **SOLID Principles**: 
  - Single Responsibility
  - Open/Closed (erweiterbar, nicht änderbar)
  - Liskov Substitution
  - Interface Segregation
  - Dependency Inversion

### Testing
- **Unit Tests**: Jede Service isoliert
- **Integration Tests**: Services + Repositories
- **Mock Objects**: Für isolierte Tests

---

## Kontakt & Support

Wenn du Fragen hast:
1. Sieh dir den relevanten Code an
2. Lies diese Dokumentation nochmal
3. Versuche Code zu schreiben (Learning by Doing!)
4. Stelle Fragen in der nächsten Session

---

**Du hast großartige Arbeit geleistet! Diese Architektur ist eine solide Basis für ein großes ERP-System.** 🎉

Viel Erfolg beim Offline-Lesen und bis zur nächsten Session!
