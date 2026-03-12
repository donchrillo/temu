---
name: backend-refactor
description: Code Smells erkennen und nach Best Practices beheben mit detaillierten Pattern-Beispielen.
---

# 🎯 Backend Refactoring Patterns

## 🎯 Refactoring-Scope (3 Kategorien)

### 🔴 HIGH IMPACT (Immer fixen)

**Strukturelle Probleme die Wartung blockieren:**

#### 1. God Classes (>300 Zeilen oder >10 Methoden)
**Symptom:** Klasse hat zu viele Verantwortlichkeiten  
**Fix:** Split by Domain

```python
# ❌ BEFORE: OrderService macht ALLES (450 Zeilen)
class OrderService:
    def create_order(self, data): ...     # 80 Zeilen
    def validate_order(self, data): ...   # 60 Zeilen
    def calculate_tax(self, order): ...   # 40 Zeilen
    def send_confirmation(self, order): ... # 50 Zeilen
    def generate_invoice_pdf(self, order): ... # 70 Zeilen

# ✅ AFTER: Split by Domain
class OrderService:
    """Orchestrates order creation workflow."""
    def __init__(self, 
                 validator: OrderValidator,
                 tax_calculator: TaxCalculator,
                 notifier: OrderNotifier,
                 invoice_generator: InvoiceGenerator):
        self.validator = validator
        self.tax_calculator = tax_calculator
        self.notifier = notifier
        self.invoice_generator = invoice_generator
    
    def create_order(self, data: dict) -> Order:
        """Main workflow - delegates to specialists."""
        self.validator.validate(data)
        tax = self.tax_calculator.calculate(data)
        order = Order.create(data, tax)
        self.notifier.send_confirmation(order)
        self.invoice_generator.generate(order)
        return order

class OrderValidator:
    """Focused on validation logic only."""
    def validate(self, data: dict) -> None:
        # ... 60 Zeilen Validierung

class TaxCalculator:
    """Focused on tax calculation only."""
    def calculate(self, data: dict) -> Decimal:
        # ... 40 Zeilen Tax-Logic
```

**Vorteile:**
- Jede Klasse <100 Zeilen
- Einfacher zu testen (Mock Dependencies)
- Klare Verantwortlichkeiten

---

#### 2. Lange Funktionen (>50 Zeilen)
**Symptom:** Schwer zu verstehen, schwer zu testen  
**Fix:** Extract Helper Functions (1 Function = 1 Responsibility)

```python
# ❌ BEFORE: process_invoice() ist 85 Zeilen
def process_invoice(pdf_path: str) -> Invoice:
    # Validation (15 Zeilen)
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if not pdf_path.endswith('.pdf'):
        raise ValueError("Not a PDF file")
    # ... 10 mehr Zeilen
    
    # Extraction (30 Zeilen)
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    # ... Regex Extraction 25 Zeilen
    
    # Database (20 Zeilen)
    with db_connect(DB_NAME) as conn:
        repo = InvoiceRepository(conn)
        # ... 18 Zeilen DB Logic
    
    return invoice

# ✅ AFTER: Split in fokussierte Funktionen
def process_invoice(pdf_path: str) -> Invoice:
    """Main workflow - orchestrates steps."""
    _validate_pdf_path(pdf_path)
    text = _extract_text_from_pdf(pdf_path)
    data = _parse_invoice_data(text)
    invoice = _save_to_database(data)
    return invoice

def _validate_pdf_path(path: str) -> None:
    """Validates PDF file path exists and has correct extension."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF not found: {path}")
    if not path.endswith('.pdf'):
        raise ValueError("Not a PDF file")

def _extract_text_from_pdf(path: str) -> str:
    """Extracts all text from PDF pages."""
    with pdfplumber.open(path) as pdf:
        return "".join(page.extract_text() for page in pdf.pages)

def _parse_invoice_data(text: str) -> dict:
    """Parses invoice data from text using regex."""
    # ... 25 Zeilen Regex Logic
    return {"invoice_number": ..., "amount": ...}

def _save_to_database(data: dict) -> Invoice:
    """Persists invoice data to database."""
    with db_connect(DB_NAME) as conn:
        repo = InvoiceRepository(conn)
        return repo.create(data)
```

**Vorteile:**
- Jede Funktion <20 Zeilen
- Testbar in Isolation
- Main-Function liest wie Dokumentation

---

#### 3. Duplizierter Code (>5 Zeilen identisch an 3+ Stellen)
**Symptom:** DRY-Verletzung, Bug-Magnets  
**Fix:** Extract Function oder Shared Helper Module

```python
# ❌ BEFORE: Duplikation an 3 Stellen
def process_order_a(order):
    if not order.customer:
        raise ValueError("No customer")
    if not order.customer.email:
        raise ValueError("No email")
    if not validate_email(order.customer.email):
        raise ValueError("Invalid email")
    # ... weitere Logik

def process_order_b(order):
    if not order.customer:
        raise ValueError("No customer")
    if not order.customer.email:
        raise ValueError("No email")
    if not validate_email(order.customer.email):
        raise ValueError("Invalid email")
    # ... andere Logik

# ✅ AFTER: Extracted Helper
def _validate_customer_email(order: Order) -> None:
    """Validates order has customer with valid email."""
    if not order.customer:
        raise ValueError("No customer")
    if not order.customer.email:
        raise ValueError("No email")
    if not validate_email(order.customer.email):
        raise ValueError("Invalid email")

def process_order_a(order):
    _validate_customer_email(order)
    # ... weitere Logik

def process_order_b(order):
    _validate_customer_email(order)
    # ... andere Logik
```

---

#### 4. Tiefe Verschachtelung (>3 Ebenen)
**Symptom:** Unlesbar, fehleranfällig  
**Fix:** Guard Clauses, Early Returns

```python
# ❌ BEFORE: 4 Ebenen Verschachtelung
def process_order(order):
    if order is not None:
        if order.items:
            if order.customer:
                if order.customer.is_active:
                    # Actual logic 20 Zeilen hier
                    return True
                else:
                    raise ValueError("Inactive customer")
            else:
                raise ValueError("No customer")
        else:
            raise ValueError("No items")
    else:
        raise ValueError("No order")

# ✅ AFTER: Early Returns (Guard Clauses)
def process_order(order):
    # Guard Clauses - fail fast
    if order is None:
        raise ValueError("No order")
    
    if not order.items:
        raise ValueError("No items")
    
    if not order.customer:
        raise ValueError("No customer")
    
    if not order.customer.is_active:
        raise ValueError("Inactive customer")
    
    # Happy Path - no nesting!
    # Actual logic 20 Zeilen hier
    return True
```

---

### 🟡 MEDIUM IMPACT (Nächster Sprint)

**Lesbarkeits- und Wartbarkeitsprobleme:**

#### 1. Magic Numbers/Strings
**Symptom:** Hardcoded Values ohne Kontext  
**Fix:** Constants in `settings.py` oder Modulkonstanten

```python
# ❌ BEFORE: Hardcoded Values überall
def process_batch(items):
    if len(items) > 1000:  # Warum 1000?
        raise ValueError("Batch too large")
    
    for i in range(0, len(items), 1000):  # 1000 wieder!
        batch = items[i:i+1000]
        # Process...

def export_to_csv(data):
    if len(data) > 1000:  # Schon wieder 1000!
        # Chunk...

# ✅ AFTER: Shared Constants
# modules/temu/constants.py
BATCH_SIZE = 1000
MAX_EXPORT_ROWS = 10000
CHUNK_SIZE = 500

# modules/temu/services/batch_service.py
from modules.temu.constants import BATCH_SIZE

def process_batch(items):
    if len(items) > BATCH_SIZE:
        raise ValueError(f"Batch too large (max: {BATCH_SIZE})")
    
    for i in range(0, len(items), BATCH_SIZE):
        batch = items[i:i+BATCH_SIZE]
        # Process...
```

---

#### 2. Zu viele Parameter (>5)
**Symptom:** Schwer zu nutzen, schwer zu erweitern  
**Fix:** Dataclasses, Config-Objekte, Pydantic Models

```python
# ❌ BEFORE: 8 Parameter!
def create_order(customer_id, product_id, quantity, price, 
                 tax_rate, shipping_address, billing_address, notes):
    pass

# ✅ AFTER: Pydantic Model
from pydantic import BaseModel

class OrderCreate(BaseModel):
    customer_id: int
    product_id: int
    quantity: int
    price: Decimal
    tax_rate: Decimal
    shipping_address: str
    billing_address: str
    notes: str | None = None

def create_order(order_data: OrderCreate) -> Order:
    pass
```

---

#### 3. Missing Dependency Injection
**Symptom:** Hard Dependencies (untestbar)  
**Fix:** Constructor Injection

```python
# ❌ BEFORE: Hard Dependencies (untestbar)
class OrderService:
    def process(self, order_id: int):
        repo = OrderRepository()  # Direkte Instanziierung!
        email = EmailService()    # Hard dependency!
        
        order = repo.get(order_id)
        email.send(order.customer.email, "Order processed")

# ✅ AFTER: Dependency Injection
class OrderService:
    def __init__(self, 
                 repo: OrderRepository,
                 email_service: EmailService):
        """Inject dependencies via constructor."""
        self.repo = repo
        self.email_service = email_service
    
    def process(self, order_id: int):
        order = self.repo.get(order_id)
        self.email_service.send(order.customer.email, "Order processed")

# Usage (in main.py oder setup)
repo = OrderRepository()
email = EmailService()
service = OrderService(repo, email)  # Inject
```

**Test-Vorteil:**
```python
def test_order_service():
    # Mock dependencies
    mock_repo = Mock(spec=OrderRepository)
    mock_email = Mock(spec=EmailService)
    
    service = OrderService(mock_repo, mock_email)
    service.process(123)
    
    mock_email.send.assert_called_once()  # Testbar!
```

---

#### 4. Feature Envy
**Symptom:** Methode nutzt andere Klasse mehr als eigene  
**Fix:** Move Method zur richtigen Klasse

```python
# ❌ BEFORE: Feature Envy
class OrderReport:
    def calculate_order_total(self, order: Order) -> Decimal:
        # Diese Methode nutzt nur Order-Daten!
        total = Decimal("0")
        for item in order.items:
            total += item.price * item.quantity
        return total * (1 + order.tax_rate)

# ✅ AFTER: Move Method
class Order:
    def calculate_total(self) -> Decimal:
        """Calculate total including tax."""
        subtotal = sum(item.price * item.quantity for item in self.items)
        return subtotal * (1 + self.tax_rate)

class OrderReport:
    def generate(self, order: Order):
        total = order.calculate_total()  # Nutzt Order's eigene Methode
        # ... Report-Logik
```

---

### 🔵 LOW IMPACT (Nice-to-Have)

**Code-Style und Idiomatik:**

#### 1. Un-Pythonic Code

```python
# ❌ BEFORE: Java-Style Python
def get_active_orders(orders):
    result = []
    for order in orders:
        if order.status == "active":
            result.append(order)
    return result

def get_order_ids(orders):
    ids = []
    index = 0
    for order in orders:
        ids.append((index, order.id))
        index += 1
    return ids

# ✅ AFTER: Pythonic Comprehensions & Built-ins
def get_active_orders(orders: list[Order]) -> list[Order]:
    return [order for order in orders if order.status == "active"]

def get_order_ids(orders: list[Order]) -> list[tuple[int, int]]:
    return [(i, order.id) for i, order in enumerate(orders)]

# ❌ BEFORE: Manual File Handling
def read_config():
    f = open('config.json')
    data = f.read()
    f.close()  # Vergessen = Resource Leak!
    return json.loads(data)

# ✅ AFTER: Context Manager
def read_config() -> dict:
    with open('config.json') as f:  # Auto-close
        return json.load(f)

# ❌ BEFORE: os.path
import os
config_path = os.path.join(base_dir, "config", "settings.json")

# ✅ AFTER: pathlib (objektorientiert)
from pathlib import Path
config_path = Path(base_dir) / "config" / "settings.json"
```

---

#### 2. Fehlende Type Hints

```python
# ❌ BEFORE: Keine Type Hints
def process_order(order_id):
    order = get_order(order_id)
    return calculate_total(order)

# ✅ AFTER: Vollständige Type Hints
def process_order(order_id: int) -> Decimal:
    order: Order = get_order(order_id)
    return calculate_total(order)
```

---

#### 3. Suboptimale Logging

```python
# ❌ BEFORE: print() in Production
def process_payment(amount):
    print(f"Processing payment: {amount}")  # Nicht loggbar!
    # ...

# ✅ AFTER: Strukturiertes Logging
from modules.shared.logging import app_logger

def process_payment(amount: Decimal) -> None:
    app_logger.info("Processing payment", extra={"amount": float(amount)})
    # ...
```

---

## 🚫 Anti-Patterns (NEVER do this)

```python
# ❌ BAD: Global State
_cache = {}  # Global mutable state!

def get_data(key):
    return _cache.get(key)

# ✅ GOOD: Encapsulated State
class DataCache:
    def __init__(self):
        self._cache = {}
    
    def get(self, key):
        return self._cache.get(key)

# ❌ BAD: Mixing Concerns
def process_order(order):
    validate(order)  # Validation
    tax = calculate_tax(order)  # Business Logic
    send_email(order.customer)  # Side Effect
    log_to_db(order)  # Persistence
    # 4 Verantwortlichkeiten in 1 Funktion!

# ✅ GOOD: Separated Concerns
class OrderService:
    def process(self, order):
        self.validator.validate(order)
        tax = self.tax_calculator.calculate(order)
        order.tax = tax
        self.notifier.send(order.customer)
        return self.repository.save(order)

# ❌ BAD: Leaky Abstractions
def get_users():
    conn = sqlite3.connect('db.sqlite')  # DB Details leaked!
    cursor = conn.execute("SELECT * FROM users")
    return cursor.fetchall()

# ✅ GOOD: Repository Pattern
class UserRepository:
    def get_all(self) -> list[User]:
        with self.db.connect() as conn:
            return conn.query(User).all()
```

---

## 📋 Quick Reference Katalog

### Extract Function
**Trigger:** Funktion >50 Zeilen ODER Duplikate  
**Steps:**
1. Identifiziere zusammenhängenden Code-Block
2. Extrahiere in neue Funktion mit klarem Namen
3. Pass nur notwendige Parameter
4. Return nur was gebraucht wird
5. Update Docstring

### Extract Class
**Trigger:** Klasse >300 Zeilen ODER >10 Methoden  
**Steps:**
1. Identifiziere zusammenhängende Methoden
2. Erstelle neue Klasse mit fokussiertem Namen
3. Move Methods zur neuen Klasse
4. Inject neue Klasse als Dependency
5. Update Tests

### Replace Magic Number with Constant
**Trigger:** Gleicher Wert >2x im Code  
**Steps:**
1. Erstelle `constants.py` oder nutze `settings.py`
2. Definiere benannte Konstante (UPPERCASE)
3. Replace alle Occurrences
4. Update Comments/Docstrings

### Introduce Guard Clause
**Trigger:** Nesting >3 Ebenen  
**Steps:**
1. Identifiziere Error-Cases
2. Move Error-Cases an Funktionsstart
3. Use Early Returns
4. Happy Path bleibt un-nested

### Replace Conditional with Polymorphism
**Trigger:** Viele `if/elif` basierend auf Type  
**Steps:**
1. Erstelle Base Class mit abstract method
2. Erstelle Subclasses für jeden Type
3. Replace if/elif mit Polymorphism
4. Nutze Factory Pattern für Instanziierung

---

## 💡 Pro-Tipps

1. **Klein anfangen:** Lieber 10 kleine Refactorings als 1 großes
2. **Tests zuerst:** Charakterisierungs-Tests vor Refactoring
3. **Commit oft:** 1 Refactoring-Typ = 1 Commit
4. **Review Code:** Lass andere drüberschauen vor Merge
5. **Dokumentiere:** Update Docstrings wenn Signatur ändert
6. **Performance:** Benchmark vor/nach bei kritischem Code
7. **Rückwärtskompatibilität:** Deprecate statt Breaking Changes