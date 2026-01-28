# 📘 TEMU Integration – Architektur-Dokumentation: Basis-Layer (Database)

**Status:** 🟢 STABLE / VERIFIED  
**Datum:** 23. Januar 2026  
**Bereich:** Database Connectivity & Configuration

---

## Über diesen Layer
Dieser Layer bildet das Fundament der Anwendung. Er stellt sicher, dass die Verbindung zu den SQL-Servern (JTL & TOCI) performant, sicher und stabil ist. Alte Implementierungen (raw `pyodbc`) wurden durch eine moderne `SQLAlchemy`-Architektur ersetzt.

---

## 1. Konfiguration
**Datei:** `config/settings.py`

Diese Datei ist die zentrale Steuerzentrale der Anwendung. Sie trennt Code von Konfiguration gemäß den *12-Factor App* Prinzipien.

* **Funktion:**
    * Lädt Environment-Variablen via `python-dotenv`.
    * Definiert Tabellennamen und Datenbank-Konstanten.
    * Erstellt automatisch benötigte Ordnerstrukturen (`data/`).
* **Architektur-Highlights:**
    * ✅ **Plattformunabhängigkeit:** Nutzung von `pathlib` statt String-Pfaden (läuft auf Windows, Linux & Docker).
    * ✅ **Robustheit:** `mkdir(exist_ok=True)` verhindert Abstürze beim ersten Start auf neuen Systemen.
    * ✅ **Security:** Keine Hardcoded-Passwords im Code.

---

## 2. Datenbank-Engine & Pooling
**Datei:** `src/db/connection.py`

Das Herzstück der Datenhaltung. Hier wurde von "Single Connection" auf "Enterprise Connection Pooling" umgestellt.

* **Funktion:**
    * Erstellt und verwaltet die `SQLAlchemy Engine`.
    * Verwaltet den Connection Pool (Queue von offenen Verbindungen).
    * Bietet `db_connect` als Context Manager für Transaktionen.
* **Architektur-Highlights:**
    * ✅ **Self-Healing:** `pool_pre_ping=True` erkennt "tote" Verbindungen (z.B. nach nächtlichem SQL-Server-Neustart) und stellt sie automatisch wieder her.
    * ✅ **Smart Driver Selection:** Wählt automatisch `ODBC Driver 18` (Linux/Docker) oder `SQL Server` (Windows Legacy).
    * ✅ **Transaktionssicherheit:** Der `db_connect` Context Manager garantiert **Atomarität** (Automatisches `COMMIT` bei Erfolg, `ROLLBACK` bei Fehler).
    * ✅ **Thread-Safety:** Ermöglicht parallele Zugriffe durch FastAPI und Background-Worker ohne "Cursor-Konflikte".

---

## 3. Modul-Schnittstelle
**Datei:** `src/db/__init__.py`

Die saubere Schnittstelle nach außen.

* **Funktion:**
    * Exportiert nur die notwendigen Funktionen (`get_engine`, `db_connect`).
    * Versteckt interne Implementierungsdetails.
* **Status:**
    * ✅ **Bereinigt:** Keine Referenzen mehr auf veraltete `get_db_connection` Funktionen.

---

## 4. Praktische Verwendung: Context Manager Pattern

### Transaktions-Beispiel mit Rollback
```python
from src.db.connection import db_connect
from config.settings import DB_JTL

# Automatisches COMMIT bei Erfolg, ROLLBACK bei Fehler
with db_connect(DB_JTL) as conn:
    result = conn.execute(text("""
        UPDATE tArtikel SET nPuffer = :puffer WHERE kArtikel = :id
    """), {"puffer": 100, "id": 5})
    # Bei Exception hier → Automatischer ROLLBACK
    # Bei erfolgreichem Ende → Automatischer COMMIT
```

### Verschachtelte Transaktionen (Mehrere DBs)
```python
with db_connect(DB_TOCI) as toci_conn:
    with db_connect(DB_JTL) as jtl_conn:
        # Wenn eine DB crasht, rollback beide automatisch
        # Saubere Fehlerbehandlung ohne explizites ROLLBACK
        inventory_data = jtl_conn.execute(...)
        toci_conn.execute(...)  # Schreib in TOCI
```

### Ohne Context Manager (selten nötig)
```python
from src.db.connection import get_engine

engine = get_engine(DB_JTL)
with engine.connect() as conn:
    result = conn.execute(text("SELECT ..."))
    # Keine Transaktion! Nur für READ-ONLY
```

---

## 5. Repository Pattern Integration

### Struktur: Repository mit injizierter Connection
Alle Repositories (`JtlRepository`, `ProductRepository`, `InventoryRepository`) folgen diesem Pattern:

```python
from sqlalchemy import text
from src.db.connection import get_engine
from config.settings import DB_JTL

class JtlRepository:
    def __init__(self, connection=None):
        """Optional injizierte Connection für Transaktionen"""
        self._conn = connection
    
    def _execute_sql(self, sql_text, params=None):
        """Hilfsmethode: Nutzt injizierte Connection ODER neue"""
        if params is None:
            params = {}
        
        if self._conn:
            # Benutze bestehende Connection (Transaktion)
            return self._conn.execute(text(sql_text), params)
        else:
            # Erstelle neue Connection (Auto-Commit)
            engine = get_engine(DB_JTL)
            with engine.connect() as conn:
                result = conn.execute(text(sql_text), params)
                conn.commit()
                return result
```

### Nutzung in Workflows (mit Transaktionssicherheit)
```python
from src.db.repositories.jtl_common.jtl_repository import JtlRepository
from src.db.connection import db_connect
from config.settings import DB_JTL

with db_connect(DB_JTL) as jtl_conn:
    # Injiziere die Transaktion ins Repository
    jtl_repo = JtlRepository(connection=jtl_conn)
    
    # Alle Operationen sind jetzt Teil einer Transaktion
    stocks = jtl_repo.get_stocks_by_article_ids([1, 2, 3])
    # Bei Fehler hier → ROLLBACK aller Queries
```

---

## 6. Batch-Query Optimierungen

### Das 2100-Parameter-Problem
SQL Server akzeptiert maximal **2100 Parameter** pro Query. Bei 5000 Produkten crasht eine simple `IN`-Klausel:

```python
# ❌ FALSCH - Crasht bei > 2100 Artikeln:
sql = text("""
    SELECT kArtikel, fBestand FROM vLagerbestandProLager
    WHERE kArtikel IN (:ids)
""").bindparams(bindparam('ids', expanding=True))

# Wenn len(ids) > 2100 → SQL Server wirft Fehler!
```

### ✅ Chunking-Strategie
```python
def get_stocks_by_article_ids(self, article_ids: List[int]) -> Dict[int, int]:
    """Batch-Abfrage mit automatischem Chunking"""
    CHUNK_SIZE = 1000  # 1000 pro Chunk = Sicherheitsmarge
    stock_map = {}
    
    # Teile in Chunks auf
    for i in range(0, len(article_ids), CHUNK_SIZE):
        chunk = article_ids[i:i+CHUNK_SIZE]
        
        sql = text("""
            SELECT kArtikel, fBestand FROM vLagerbestandProLager
            WHERE kArtikel IN :ids AND kWarenlager = 2
        """).bindparams(bindparam('ids', expanding=True))
        
        result = self._execute_sql(sql, {"ids": chunk})
        for row in result:
            stock_map[row[0]] = max(0, row[1] - nPuffer)
    
    return stock_map
```

### Performance-Vergleich
| Strategie | 1000 Items | 5000 Items | Problem |
| --- | --- | --- | --- |
| Loop (N+1) | 5s | 25s | 5000 Queries! |
| Single IN (> 2100) | 1s | ❌ CRASH | Parameter-Limit |
| Chunking (1000er) | 0.8s | 4s | ✅ Optimal |

---

## 7. Error Handling & Debugging

### Häufige Fehler und Lösungen

#### A) Connection Pool Exhaustion
```
Fehler: "QueuePool limit exceeded with overflow"
```
**Ursache:** Zu viele gleichzeitige Queries ohne Context Manager  
**Lösung:**
```python
# ❌ FALSCH - Connection wird nie freigegeben:
conn = get_engine(DB_JTL).connect()
result = conn.execute(...)
# conn wird nicht geschlossen!

# ✅ RICHTIG - Context Manager:
with db_connect(DB_JTL) as conn:
    result = conn.execute(...)
    # Auto-close nach Block
```

#### B) "Dead Connection" Nach Server-Restart
```
Fehler: "Connection was reset"
```
**Ursache:** SQL-Server wurde neu gestartet, Pool kennt das nicht  
**Lösung:** Bereits gebaut! `pool_pre_ping=True` in `connection.py`
```python
# connection.py - Zeile 20:
engine = create_engine(connection_string, pool_pre_ping=True)
# Prüft Connection vor Nutzung, erstellt neue falls nötig
```

#### C) Type Mismatch in Updates
```
Fehler: "Error converting nvarchar value '2021451277-4' to int"
```
**Ursache:** Falsche Parameter in WHERE-Klausel (z.B. SKU statt ID)  
**Lösung:** Typprüfung im Repository:
```python
def update_jtl_article_id(self, product_id: int, jtl_article_id: int) -> bool:
    """product_id MUSS int sein, nicht string/sku!"""
    sql = text("UPDATE temu_products SET jtl_article_id = :jtl_id WHERE id = :product_id")
    self._execute_sql(sql, {"jtl_id": jtl_article_id, "product_id": product_id})
```

### Logging & Debugging
```python
from src.modules.temu.logger import temu_logger  # Modul-spezifischer Logger

try:
    result = repository.execute_query()
except Exception as e:
    # Detailliertes Error-Logging
    temu_logger.error(f"Repository xyz failed: {e}", exc_info=True)
    # exc_info=True → Vollständiger Traceback ins Log
```

---

## 8. Performance Best Practices

### Text-Queries vs. ORM

| Ansatz | Verwendung | Vorteil | Nachteil |
| --- | --- | --- | --- |
| **text()** | Komplexe JOINs, Batch | Direkt, schnell | Manuelle Parameter |
| **ORM Models** | CRUD auf 1-2 Tabellen | Type-Safe, auto | Langsamer bei Batch |

**Regel:** 
- ✅ Batch & Complex Queries → `text()`
- ✅ Single Insert/Update → ORM (wenn Zeit)
- ✅ Report-Queries (Read-Only) → ORM

### Query-Reihenfolge (wichtig!)

```python
# 🐢 LANGSAM - N+1 Problem:
products = fetch_all_products()  # 1 Query
for p in products:
    stock = get_stock(p.id)  # 5000 Queries! 💥
    print(stock)

# 🚀 SCHNELL - Batch:
all_product_ids = [p.id for p in products]
stock_map = get_stocks_batch(all_product_ids)  # 5 Queries (Chunking)
for p in products:
    stock = stock_map.get(p.id, 0)
    print(stock)
```

### Connection Pool Tuning
**Datei:** `src/db/connection.py`

```python
# Aktuelle Settings:
pool_size=10        # Ständig offene Connections
max_overflow=20     # Zusätzlich bei Lastspitzen
pool_recycle=3600   # Verbindungen nach 1h erneuern

# Für High-Load:
pool_size=20        # Mehr Connections
max_overflow=30
```

### Messung & Benchmarking
```python
import time
from src.modules.temu.logger import temu_logger

start = time.time()
result = repository.get_stocks_by_article_ids(article_ids)
duration = time.time() - start

temu_logger.info(f"Batch query took {duration:.3f}s for {len(article_ids)} items")
# Output: "Batch query took 0.081s for 2100 items"
```

---

## Technische Parameter (Aktuell)

| Parameter | Wert | Beschreibung |
| :--- | :--- | :--- |
| **Pool Size** | 10 | Anzahl dauerhaft offener Verbindungen pro DB |
| **Max Overflow** | 20 | Maximale zusätzliche Verbindungen bei Lastspitzen |
| **Pool Recycle** | 3600s | Verbindungen nach 1h erneuern |
| **Drivers** | ODBC 18 / SQL Server | Automatische Wahl je nach OS |
| **Batch Chunk Size** | 1000 | Items pro SQL-Query (SQL Server 2100-Limit Puffer) |
| **Connection Timeout** | Standard | Via SQLAlchemy verwaltet |

---

## Häufig gestellte Fragen

**F: Wann sollte ich `db_connect` verwenden vs. `get_engine`?**  
A: `db_connect` = Wenn Transaktionen wichtig sind (Write-Ops).  
`get_engine` = Nur für Read-Only oder wenn Auto-Commit OK ist.

**F: Was passiert, wenn die Connection in der Mitte einer Transaktion crasht?**  
A: Automatischer ROLLBACK. Das ist der Sinn des Context Managers.

**F: Kann ich mehrere Repos in einer Transaktion nutzen?**  
A: Ja! Einfach alle Repos mit derselben Connection initialisieren:
```python
with db_connect(DB_TOCI) as conn:
    repo1 = ProductRepository(connection=conn)
    repo2 = InventoryRepository(connection=conn)
    # Beide in EINER Transaktion
```

**F: Wie viel RAM braucht der Connection Pool?**  
A: ~2-5 MB pro Connection. Bei 30 Connections max. ~150 MB extra.

---

## 5. Strukturiertes Logging – scheduler_logs Tabelle (28. Januar 2026)

### Übersicht
Die `scheduler_logs` Tabelle speichert strukturierte Logs aller TEMU-Jobs (Inventar-Sync, Auftrags-Sync, etc.) mit Meta-Informationen.

**Datei:** `src/db/repositories/common/log_repository.py`

### Tabellen-Schema
```sql
CREATE TABLE [dbo].[scheduler_logs] (
    [log_id] INT PRIMARY KEY IDENTITY(1,1),
    [job_id] VARCHAR(255) NOT NULL,
    [job_type] VARCHAR(100) NOT NULL,
    [level] VARCHAR(20) NOT NULL,
    [message] NVARCHAR(MAX) NOT NULL,
    [timestamp] DATETIME2 NOT NULL DEFAULT GETDATE(),
    [duration_seconds] FLOAT NULL,
    [status] VARCHAR(20) NULL,
    [error_text] NVARCHAR(MAX) NULL,
    
    INDEX idx_job_id (job_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_level (level)
);
```

### Master-Jobs & Sub-Jobs

**Master-Jobs** haben eindeutige job_ids mit Timestamp:
- `temu_orders_1769614356`
- `temu_inventory_1769613860`
- `sync_orders_1769612871`

**Sub-Jobs** teilen die gleiche job_id:
```
temu_orders_1769614356
├── order_service
├── order_workflow
├── tracking_service
└── temu_service
```

### LIKE-Filter Pattern Matching

**Backend:** `job_id LIKE 'temu_orders%'` zeigt alle Sub-Jobs mit dieser job_id

### Verwendung im Code

```python
# Log schreiben
log_repository.insert_log(
    job_id="temu_orders_1769614356",
    job_type="order_workflow",
    level="INFO",
    message="Bestellung verarbeitet",
    status="success",
    duration_seconds=2.5
)

# Logs mit Filter laden
logs = log_repository.get_logs(job_id="temu_orders%", level="ERROR")
```

---

> **Nächste Schritte:** Spezifische Repository-Dokumentation, Workflow-Patterns, Deployment-Konfiguration.
