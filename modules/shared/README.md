# Shared Module

Re-Export Layer für gemeinsame Funktionen, die von allen Modulen benötigt werden.

## Zweck

Dieses Modul bietet einen einfachen, einheitlichen Import-Layer für:
- **Database:** SQLAlchemy Engine, Connection Pooling, Repository Pattern
- **Logging:** Modul-spezifische Logger, DB-Logging mit WebSocket
- **Config:** Zentrale Konfiguration aus .env

## Verwendung

```python
# Einfache Imports für neue Module
from modules.shared import db_connect, BaseRepository, create_module_logger, log_service

# Database verwenden
with db_connect('toci') as conn:
    # Transaction handling automatisch
    result = conn.execute("SELECT * FROM temu_orders")

# Logger erstellen
logger = setup_logger("mein_modul")
logger.info("Modul gestartet")

# DB-Logging mit WebSocket Broadcasting
log_service.log("job_123", "mein_modul", "INFO", "Job abgeschlossen")
```

## Architektur

Dieses Modul ist ein **Re-Export Layer** - es ändert NICHTS an der bestehenden
Architektur in `src/`, sondern macht sie nur einfacher zugänglich.

```
modules/shared/          # Re-Export Layer
    ↓
src/db/                  # Bestehende DB-Logik
src/services/            # Bestehende Services
config/settings.py       # Bestehende Config
```

## Vorteile

✅ Neue Module haben einfache Imports
✅ Bestehende Architektur bleibt intakt
✅ Kein Umbau von src/ nötig
✅ Rückwärtskompatibel mit bestehendem Code

## Verfügbare Funktionen

### Database (`from modules.shared import ...`)
- `get_engine(database='toci')` - SQLAlchemy Engine mit Pooling
- `db_connect(database='toci')` - Context Manager für Transaktionen
- `get_db(database='toci')` - FastAPI Dependency für DB-Zugriff
- `BaseRepository` - Basis-Klasse für Repositories mit Batch-Operations

### Logging (`from modules.shared import ...`)
- `setup_logger(name)` - Modul-spezifischen Logger erstellen
- `log_service` - DB-Logging mit WebSocket-Broadcasting
- `app_logger` - Allgemeiner Application Logger

### Config (`from modules.shared import ...`)
- Alle Settings aus `config/settings.py`
- SQL Server Credentials
- Database Names (DB_TOCI, DB_JTL)
- TEMU API Credentials
- JTL Configuration

## Beispiel: Neues Modul erstellen

```python
# modules/amazon/services.py
from modules.shared import db_connect, BaseRepository, create_module_logger, log_service

logger = create_module_logger("AMAZON", "amazon")

class AmazonOrderRepository(BaseRepository):
    def __init__(self):
        super().__init__('toci', 'amazon_orders')

def sync_amazon_orders(job_id="amazon_sync"):
    logger.info("Starte Amazon Order Sync")
    log_service.log(job_id, "amazon", "INFO", "Sync gestartet")

    with db_connect('toci') as conn:
        repo = AmazonOrderRepository()
        orders = fetch_from_amazon()
        repo.insert_batch(orders, conn)

    log_service.log(job_id, "amazon", "INFO", f"{len(orders)} Orders importiert")
    logger.info("Amazon Order Sync abgeschlossen")
```

## Version

0.1.0 - Initial Release
