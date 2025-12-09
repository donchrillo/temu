"""Database Connection Manager - SQL Server mit Connection Pooling"""

import pyodbc
from config.settings import SQL_SERVER, SQL_USERNAME, SQL_PASSWORD

# ===== Connection Pool =====
# Wiederverwendbare Connections statt für jeden Call neu zu erstellen
_connection_pools = {}

def get_db_connection(database='toci', use_pool=True):
    """
    Hole SQL Server Connection (mit optionalem Pooling)
    
    Args:
        database: 'toci' oder 'eazybusiness'
        use_pool: True = Connection Pooling (empfohlen), False = Neue Connection
    
    Returns:
        pyodbc.Connection
    """
    try:
        # Parse Server (handle both "192.168.178.2,50000" und "192.168.178.2:50000")
        server_parts = SQL_SERVER.replace(':', ',').split(',')
        server_host = server_parts[0]
        server_port = server_parts[1] if len(server_parts) > 1 else '1433'
        
        # Connection String
        conn_string = (
            'DRIVER={SQL Server};'
            f'SERVER={server_host},{server_port};'
            f'DATABASE={database};'
            f'UID={SQL_USERNAME};'
            f'PWD={SQL_PASSWORD}'
        )
        
        # ===== Connection Pooling =====
        if use_pool:
            pool_key = database
            
            # Pool existiert & Connection ist noch aktiv?
            if pool_key in _connection_pools:
                try:
                    conn = _connection_pools[pool_key]
                    # Test ob noch aktiv
                    conn.cursor().execute("SELECT 1")
                    # ✓ Pool Connection ist OK
                    return conn
                except:
                    # ✗ Pool Connection ist tot - neu erstellen
                    del _connection_pools[pool_key]
            
            # Neue Connection erstellen & in Pool speichern
            print(f"  → Neue Connection zu {database}...")
            print(f"    Server: {server_host}:{server_port}")
            print(f"    User: {SQL_USERNAME}")
            
            conn = pyodbc.connect(conn_string, timeout=10)
            conn.autocommit = True  # ✅ AutoCommit ON für Pooling!
            
            _connection_pools[pool_key] = conn
            print(f"  ✓ {database} Connection (gepooled)\n")
            return conn
        else:
            # Ohne Pooling (für Tests/Debug)
            conn = pyodbc.connect(conn_string, timeout=10)
            conn.autocommit = False
            return conn
    
    except pyodbc.Error as e:
        error_code = e.args[0] if e.args else 'Unknown'
        error_msg = e.args[1] if len(e.args) > 1 else str(e)
        
        print(f"  ✗ DB Verbindungsfehler: {error_code}")
        print(f"     Message: {error_msg}")
        print(f"\n  Überprüfe:")
        print(f"    1. SQL Server läuft:")
        print(f"       PowerShell: Get-Service | Select-String MSSQL")
        print(f"")
        print(f"    2. Server erreichbar:")
        print(f"       PowerShell: Test-NetConnection {server_host} -Port {server_port}")
        print(f"       Sollte zeigen: TcpTestSucceeded : True")
        print(f"")
        print(f"    3. Credentials korrekt in .env:")
        print(f"       SQL_SERVER={SQL_SERVER}")
        print(f"       SQL_USERNAME={SQL_USERNAME}")
        print(f"")
        raise

def close_connection(conn):
    """Schließe Connection (nur wenn nicht gepoolt)"""
    if conn:
        try:
            conn.close()
        except:
            pass

def close_all_connections():
    """Schließe ALLE gepoolten Connections (z.B. beim Shutdown)"""
    global _connection_pools
    
    for database, conn in _connection_pools.items():
        try:
            conn.close()
            print(f"✓ {database} Connection geschlossen")
        except:
            pass
    
    _connection_pools = {}
