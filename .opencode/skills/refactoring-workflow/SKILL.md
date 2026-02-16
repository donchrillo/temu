---
name: refactoring-workflow
description: Systematischer Prozess für sichere und effektive Refactorings mit Analyse, Planung und Verifikation.
---

# 🔄 Refactoring Workflow

## ⚡ Quick Start Checklist

**Vor JEDEM Refactoring (3 Minuten):**

1. ✅ **Funktioniert der Code?** → Pylance Syntax-Check
2. ✅ **Gibt es Tests?** → Falls nein: Erst Tests, dann Refactoring
3. ✅ **Wie groß/kritisch?** → <200 Zeilen + unkritisch = aggressive Refactorings OK
4. ✅ **Deployment bald?** → <1 Woche = WARTEN
5. ✅ **Last Modified?** → Vor <7 Tagen = konservativ refactoren

**Dann entscheiden:**
- Tests ✅ + Unkritisch → Auto-Refactor möglich
- Keine Tests ❌ + Kritisch → Erst absichern
- Production + Kritisch → Nur High-Impact Changes

---

## 🚦 Refactoring-Ampel (Decision Helper)

### 🟢 Grün - Refactoren ohne Bedenken

**Bedingungen:**
- ✅ Code hat Unit-Tests (>80% Coverage)
- ✅ Unkritische Helper-Funktionen
- ✅ Neue Features (noch nicht in Production)
- ✅ Kleine, isolierte Module (<200 Zeilen)

**Action:** Aggressive Refactorings OK, Auto-Refactor möglich

---

### 🟡 Gelb - Vorsichtig refactoren

**Bedingungen:**
- ⚠️ Code ohne Tests
- ⚠️ Mittlere Kritikalität (Reports, Exports)
- ⚠️ Mehrere Dependencies
- ⚠️ Performance-kritischer Code

**Action:** Inkrementelle Refactorings
1. Erst Charakterisierungs-Tests schreiben
2. Kleine Refactorings (1 pro Commit)
3. Nach jedem Schritt verifizieren
4. Benchmark Performance vor/nach

---

### 🔴 Rot - STOP, erst absichern

**Bedingungen:**
- ❌ Production-kritisch (Payment, Auth) ohne Tests
- ❌ Legacy-Code mit unbekannten Side-Effects
- ❌ Deployment in <1 Woche
- ❌ Code mit externen Dependencies (APIs)

**Action:** Nicht direkt refactoren!
1. **Dokumentiere** aktuellen Zustand (Docstrings, Kommentare)
2. **Characterization Tests:** Beschreibe aktuelles Verhalten
3. **Code Review:** Mit Team besprechen
4. **Nach Deployment:** Dann schrittweise refactoren

---

## 📝 Workflow (4 Phasen)

### Phase 1: Analyse (Quick Scan)

**Input:** Datei oder Modul  
**Output:** Priorisierte Liste von Code Smells

```python
# Nutze MCP Pylance für Syntax-Check
mcp_pylance_mcp_s_pylanceSyntaxErrors(file="order_service.py")

# Metriken sammeln
- Zeilen-Count
- Funktionen-Count
- Max Function Length
- Max Nesting Level
- Test Coverage (falls verfügbar)
```

**Quick-Scan-Template:**
```
## ⚡ Quick Scan: order_service.py

Metriken:
- Zeilen: 450
- Funktionen: 12
- Max Function Length: 120 Zeilen (❌ sollte <50)
- Max Nesting: 5 Ebenen (❌ sollte <3)
- Test Coverage: 45% (⚠️ niedrig)

Top 3 Issues:
1. 🔴 God Class - OrderService hat 12 Methoden
2. 🔴 Lange Funktion - process_order() ist 120 Zeilen
3. 🟡 Magic Numbers - "1000" kommt 5x vor

Recommendation: Split OrderService, dann extract helpers
```

---

### Phase 2: Planung

**Output:** Refactoring-Plan mit Prioritäten

```
## 📋 Refactoring Plan für order_service.py

### Scope: High-Impact Refactorings (2-3 Stunden)

**Phase 1: Split God Class** (1h)
- [ ] Extract OrderValidator
- [ ] Extract TaxCalculator
- [ ] Extract OrderNotifier
- [ ] Update Tests

**Phase 2: Extract Helpers** (45min)
- [ ] process_order() → 5 helper functions
- [ ] Reduce nesting mit Guard Clauses

**Phase 3: Constants** (15min)
- [ ] Create BATCH_SIZE constant
- [ ] Replace 5 occurrences

### Risks:
- ⚠️ Test Coverage nur 45% → Erst mehr Tests
- ⚠️ Dependencies zu PaymentService → Careful

### Expected Outcome:
- From: 450 Zeilen God Class
- To: 5 focused classes (50-100 Zeilen each)
- Test Coverage: 45% → 75%
```

---

### Phase 3: Implementierung (Schrittweise)

**1 Refactoring pro Schritt, verifizieren, dann nächster:**

```bash
# Step 1: Extract OrderValidator
git checkout -b refactor/order-service-validator
[Code ändern]
pytest tests/test_order_service.py -v
git commit -m "refactor(order-service): extract OrderValidator class"

# Step 2: Extract TaxCalculator
[Code ändern]
pytest tests/test_order_service.py -v
git commit -m "refactor(order-service): extract TaxCalculator class"

# Step 3: Extract helpers from process_order()
[Code ändern]
pytest tests/test_order_service.py -v
git commit -m "refactor(order-service): extract helper functions"
```

**Template für jeden Schritt:**
```
✅ Step N/M: [Refactoring Name]

Code Changes:
- Before: [Snippet]
- After: [Snippet]

Verification:
- ✅ Syntax OK (Pylance)
- ✅ Tests Passed (pytest)
- ✅ Imports OK (python -c "import ...")
- ⚠️ Performance: +5% (acceptable)

Commit:
refactor(scope): description
```

---

### Phase 4: Verifizierung (Checkliste)

**Vor Git Push:**

#### 1. Syntax Check (IMMER)
```bash
# Via Pylance MCP
mcp_pylance_mcp_s_pylanceSyntaxErrors --file refactored_file.py
```

#### 2. Unit Tests (falls vorhanden)
```bash
pytest tests/test_refactored_module.py -v --cov
```

**Falls KEINE Tests:**
```
⚠️ WARNUNG: Keine Tests gefunden!

Empfehlung:
1. Erstelle Charakterisierungs-Tests (beschreiben aktuelles Verhalten)
2. Oder: Manuelle Verifikation mit Stakeholder

Soll ich Unit-Tests generieren? (y/n)
```

#### 3. Import Check
```python
python -c "from modules.refactored import RefactoredClass"
```

#### 4. Performance Check (nur bei kritischem Code)
```python
import timeit

# Before Refactoring
old_time = timeit.timeit(lambda: old_function(), number=1000)

# After Refactoring
new_time = timeit.timeit(lambda: new_function(), number=1000)

if new_time > old_time * 1.2:  # >20% Regression
    print("⚠️ Performance Regression detected!")
    print(f"Old: {old_time:.4f}s, New: {new_time:.4f}s")
```

#### 5. Git Diff Review
```bash
git diff --stat                    # Wie viel geändert?
git diff modules/refactored_file.py  # Was genau?
```

#### 6. Commit mit Conventional Commits
```
refactor(order-service): extract OrderValidator class

- Moved validation logic from OrderService to new OrderValidator
- Reduces OrderService from 450 to 180 lines
- Improves testability via dependency injection
- No behavior change

BREAKING CHANGE: None
```

---

## 📋 Output-Modi (3 Levels)

### Modus 1: Quick Feedback (Default)

**Verwendung:** `"Quick review of order_service.py"`

```
## ⚡ Quick Analysis: order_service.py

Top 3 Issues:
1. 🔴 God Class - 450 Zeilen, 12 Methoden
2. 🟡 Long Function - process_order() ist 120 Zeilen
3. 🟡 Magic Numbers - "1000" 5x

Quick Wins:
- Split OrderService in 3 Klassen
- Extract helpers von process_order()
- Create BATCH_SIZE constant

Detailed Analysis? → Antwort "detailed"
Auto-Refactor? → Antwort "refactor"
```

---

### Modus 2: Detaillierte Analyse

**Verwendung:** `"Detailed refactoring analysis of order_service.py"`

```
## 🔍 Detailed Code Analysis: order_service.py

### Metriken:
- Lines: 450
- Functions: 12
- Classes: 2
- Avg Function Length: 37 Zeilen
- Max Function Length: 120 Zeilen (❌)
- Max Nesting: 5 Ebenen (❌)
- Complexity Score: 8/10 (hoch)
- Test Coverage: 45% (niedrig)

### Code Smells (priorisiert):

#### 🔴 HIGH IMPACT
1. **God Class - OrderService**
   - Zeilen: 1-450
   - Verantwortlichkeiten: Validation, Tax, Email, PDF, DB
   - Empfehlung: Split in OrderService, OrderValidator, TaxCalculator, OrderNotifier, InvoiceGenerator

2. **Long Function - process_order()**
   - Zeilen: 50-170 (120 Zeilen!)
   - Komplexität: 15 (sollte <10)
   - Empfehlung: Extract 5 helper functions

#### 🟡 MEDIUM IMPACT
3. **Duplicated Code**
   - Zeilen: 80-95 ähnlich zu 210-225
   - Duplikation: 85% Similarity
   - Empfehlung: Extract _validate_customer_data()

4. **Magic Numbers**
   - "1000" appears in: Zeilen 45, 89, 156, 234, 389
   - Empfehlung: Create BATCH_SIZE = 1000 constant

### Refactoring Plan:
[Detaillierter 4-Phasen Plan]

Continue with implementation? (y/n)
```

---

### Modus 3: Auto-Refactor

**Verwendung:** `"Refactor order_service.py automatically"`

```
## 🤖 Auto-Refactoring: order_service.py

Applying safe refactorings (non-breaking)...

✅ Step 1/6: Create BATCH_SIZE constant
   - Created: modules/temu/constants.py
   - Replaced: 5 occurrences
   - Tests: ✅ 12/12 passed

✅ Step 2/6: Extract _validate_customer_data() helper
   - Removed duplication in lines 80-95, 210-225
   - New function: 15 lines
   - Tests: ✅ 12/12 passed

✅ Step 3/6: Introduce Guard Clauses in process_order()
   - Reduced nesting from 5 to 2 levels
   - Improved readability score: 6.2 → 7.8
   - Tests: ✅ 12/12 passed

✅ Step 4/6: Extract OrderValidator class
   - Moved 3 validation methods
   - OrderService: 450 → 320 lines
   - Tests: ✅ 14/14 passed (2 new tests)

⚠️ Step 5/6: Extract TaxCalculator class
   - WARNING: Complex tax logic detected
   - Recommendation: Manual review needed
   - SKIPPED (requires human approval)

✅ Step 6/6: Add type hints
   - Added annotations to 8 public functions
   - Mypy compliance: 100%
   - Tests: ✅ 14/14 passed

---

## Summary:
- ✅ 5/6 refactorings applied
- ✅ 0 breaking changes
- ✅ All tests passing (14/14)
- ⚠️ 1 requires manual review (TaxCalculator)
- 📊 Improvements:
  * Lines: 450 → 320 (-29%)
  * Functions: 12 → 9 (-25%)
  * Max Nesting: 5 → 2 (-60%)
  * Complexity: 8 → 5 (-37.5%)
  * Test Coverage: 45% → 62% (+17%)

Ready to commit? Suggested message:

```
refactor(order-service): improve structure and readability

- Extract BATCH_SIZE constant (DRY)
- Extract _validate_customer_data() helper (DRY)
- Introduce Guard Clauses (reduce nesting)
- Extract OrderValidator class (SRP)
- Add type hints (type safety)

BREAKING CHANGE: None
Tests: 14/14 passing
Coverage: 45% → 62%
```

Push to branch refactor/order-service? (y/n)
```

---

## 🛠️ Integration mit MCP Tools

### Vor Refactoring:

```typescript
// 1. Syntax Check
await mcp_pylance_mcp_s_pylanceSyntaxErrors({
  file: "modules/temu/services/order_service.py"
});

// 2. Find Duplicates (Code Search)
await grep_search({
  pattern: "validate.*order",  // Regex
  path: "modules/temu/"
});

// 3. Find Related Functions (Semantic Search)
await semantic_search({
  query: "order validation logic",
  scope: "modules/"
});
```

### Nach Refactoring:

```bash
# 4. Verify Imports
python -c "from modules.temu.services.order_service import OrderService"

# 5. Run Tests
pytest tests/temu/services/test_order_service.py -v --tb=short

# 6. Type Check (optional)
mypy modules/temu/services/order_service.py
```

---

## 🎯 Best Practices

### Refactoring-Strategie

1. **Rot-Grün-Refactor-Zyklus**
   - Rot: Test schreiben (fail)
   - Grün: Code implementieren (pass)
   - Refactor: Code verbessern (still pass)

2. **Baby Steps**
   - Kleine Änderungen
   - Nach jedem Schritt Tests laufen lassen
   - Bei Fehler: Zurückrollen ist einfach

3. **Branch per Refactoring-Type**
   - `refactor/extract-validator`
   - `refactor/add-type-hints`
   - `refactor/remove-duplication`

4. **Pair Programming bei kritischem Code**
   - Review vor Merge
   - Zwei Augen sehen mehr

### Wann NICHT refactoren

- ❌ Deployment in <3 Tagen
- ❌ Code funktioniert nicht (erst fixen)
- ❌ Keine Tests vorhanden (erst Tests schreiben)
- ❌ Unter Zeitdruck (technische Schuld akzeptieren)
- ❌ Fremder Legacy-Code ohne Kontext

### Wann UNBEDINGT refactoren

- ✅ Bug durch schlechte Code-Struktur
- ✅ Feature-Request blockiert durch God Class
- ✅ Neue Entwickler verstehen Code nicht
- ✅ Tests sind unmöglich zu schreiben
- ✅ Performance-Problem durch ineffiziente Struktur
