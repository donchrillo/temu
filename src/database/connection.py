"""SQL Server Verbindungsverwaltung"""

import pyodbc
from config.settings import SQL_SERVER, SQL_USERNAME, SQL_PASSWORD, DB_TOCI

def get_db_connection(database=DB_TOCI):
    """Erstellt SQL Server Verbindung zu einer bestimmten Datenbank."""
    
    drivers = [
        'ODBC Driver 18 for SQL Server',
        'ODBC Driver 17 for SQL Server',
        'ODBC Driver 13 for SQL Server',
        'SQL Server Native Client 11.0',
        'SQL Server'
    ]
    
    available_drivers = [d for d in pyodbc.drivers() if 'SQL Server' in d]
    
    driver = None
    for d in drivers:
        if d in available_drivers:
            driver = d
            break
    
    if not driver and available_drivers:
        driver = available_drivers[0]
    
    if not driver:
        raise Exception("Kein SQL Server ODBC-Treiber gefunden!")
    
    conn_str = (
        f'DRIVER={{{driver}}};'
        f'SERVER={SQL_SERVER};'
        f'DATABASE={database};'
        f'UID={SQL_USERNAME};'
        f'PWD={SQL_PASSWORD};'
        f'TrustServerCertificate=yes;'
    )
    return pyodbc.connect(conn_str)
