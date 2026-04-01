"""
Startup Validation - Fail-Fast Checks beim App-Start

Prüft:
1. Erforderliche Umgebungsvariablen
2. Datenbank-Verbindung (optional - nur warnen)
3. Erforderliche Verzeichnisse

Modi:
- production: DB-Verbindung muss funktionieren (fail-fast)
- development: DB-Prüfung optional (kein Fail-Fast)
"""

import os
from pathlib import Path
from typing import List

from modules.shared.config.settings import SQL_SERVER, SQL_USERNAME, SQL_PASSWORD, DB_TOCI

# Environment-Modus
APP_ENV = os.getenv('APP_ENV', 'production')


def validate_startup_config() -> List[str]:
    """
    Validiert App-Konfiguration beim Start.
    
    Returns:
        Liste von Fehlermeldungen (leere Liste = alles OK)
    """
    errors: List[str] = []
    
    # 1. Erforderliche Umgebungsvariablen prüfen
    required_env = [
        ('SQL_SERVER', SQL_SERVER),
        ('SQL_USERNAME', SQL_USERNAME),
        ('SQL_PASSWORD', SQL_PASSWORD),
    ]
    
    for var_name, var_value in required_env:
        if not var_value:
            errors.append(f"Missing required env var: {var_name}")
    
    # 2. Datenbank-Verbindung prüfen (nur in production)
    skip_db_check = APP_ENV == 'development'
    
    if not skip_db_check and SQL_SERVER and SQL_USERNAME and SQL_PASSWORD:
        db_error = _validate_database_connection()
        if db_error:
            errors.append(db_error)
    
    # 3. Erforderliche Verzeichnisse prüfen
    required_dirs = ['data', 'logs']
    project_root = Path(__file__).parent.parent.parent.parent
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            errors.append(f"Required directory missing: {dir_name} (path: {dir_path})")
    
    return errors


def _validate_database_connection() -> str | None:
    """
    Prüft die Datenbank-Verbindung.
    
    Returns:
        Fehlermeldung wenn fehlgeschlagen, None wenn erfolgreich
    """
    try:
        from modules.shared.database.connection import db_connect
        from sqlalchemy import text

        # Test-Verbindung mit kurzem Timeout
        with db_connect(DB_TOCI) as conn:
            conn.execute(text("SELECT 1"))
        return None
    except Exception as e:
        return f"Database connection failed: {str(e)}"
