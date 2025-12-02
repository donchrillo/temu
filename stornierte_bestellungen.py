"""
Zeigt stornierte TEMU-Bestellungen an.
Hilft bei der manuellen Stornierung in JTL falls bereits importiert.
"""

import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

SQL_SERVER = os.getenv('SQL_SERVER')
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')
DB_TOCI = 'toci'
TABLE_ORDERS = os.getenv('TABLE_ORDERS', 'temu_orders')

def get_db_connection():
    """Erstellt SQL Server Verbindung."""
    drivers = [
        'ODBC Driver 18 for SQL Server',
        'ODBC Driver 17 for SQL Server',
        'SQL Server Native Client 11.0',
        'SQL Server'
    ]
    
    available_drivers = [d for d in pyodbc.drivers() if 'SQL Server' in d]
    driver = next((d for d in drivers if d in available_drivers), available_drivers[0] if available_drivers else None)
    
    if not driver:
        raise Exception("Kein SQL Server ODBC-Treiber gefunden!")
    
    return pyodbc.connect(
        f'DRIVER={{{driver}}};SERVER={SQL_SERVER};DATABASE={DB_TOCI};'
        f'UID={SQL_USERNAME};PWD={SQL_PASSWORD};TrustServerCertificate=yes;'
    )

def show_stornierte_bestellungen():
    """Zeigt alle stornierten Bestellungen an."""
    
    print("=" * 70)
    print("Stornierte TEMU-Bestellungen")
    print("=" * 70)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Stornierte Bestellungen holen
    cursor.execute(f"""
        SELECT 
            bestell_id,
            bestellstatus,
            kaufdatum,
            xml_erstellt,
            nachname_empfaenger,
            created_at,
            updated_at
        FROM {TABLE_ORDERS}
        WHERE status = 'storniert' OR bestellstatus = 'Storniert'
        ORDER BY updated_at DESC
    """)
    
    orders = cursor.fetchall()
    
    if not orders:
        print("✓ Keine stornierten Bestellungen gefunden")
        cursor.close()
        conn.close()
        return
    
    print(f"\n{len(orders)} stornierte Bestellungen gefunden:\n")
    
    for order in orders:
        bestell_id, status, kaufdatum, xml_erstellt, nachname, created, updated = order
        
        jtl_status = "✗ IN JTL IMPORTIERT - MANUELL STORNIEREN!" if xml_erstellt else "✓ Nicht in JTL"
        
        print(f"Bestell-ID:    {bestell_id}")
        print(f"Status:        {status}")
        print(f"Kunde:         {nachname}")
        print(f"Kaufdatum:     {kaufdatum.strftime('%d.%m.%Y %H:%M')}")
        print(f"JTL-Status:    {jtl_status}")
        print(f"Aktualisiert:  {updated.strftime('%d.%m.%Y %H:%M')}")
        print("-" * 70)
    
    # Zusammenfassung
    bereits_in_jtl = sum(1 for o in orders if o[3])  # xml_erstellt
    
    if bereits_in_jtl > 0:
        print(f"\n⚠ ACHTUNG: {bereits_in_jtl} Bestellung(en) wurden bereits nach JTL exportiert!")
        print("  Diese müssen manuell in JTL storniert werden.")
    
    cursor.close()
    conn.close()
    print()

if __name__ == "__main__":
    show_stornierte_bestellungen()
