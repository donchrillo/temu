"""
sql.py – Zugriff auf den Microsoft SQL Server per pyodbc

Dieses Modul kapselt alle SQL-bezogenen Funktionen, die für die CSV-Verarbeitung benötigt werden.
Es stellt folgende Hauptfunktionen zur Verfügung:

- Aufbau einer sicheren SQL-Verbindung auf Basis von .env-Variablen.
- Abfrage einer Kundennummer anhand einer Amazon-Bestellnummer.
- Durchführung eines Verbindungstests zur Validierung der Konfiguration.

Die zentrale Datenquelle ist das JTL-Wawi-System (eazybusiness) – insbesondere die Tabelle `tAuftrag`,
aus der die Kundennummer zur Amazon-Bestellnummer extrahiert wird.
"""

# ========== 📦 Standard-/Externe Importe ==========
import pyodbc  # Für ODBC-Datenbankzugriffe (SQL Server etc.)

# ========== 🔐 Zugangsdaten aus .env laden ==========
from config import SQL_SERVER, SQL_PORT, SQL_DB, SQL_USER, SQL_PASS


def get_connection(db_name: str = SQL_DB) -> pyodbc.Connection:
    """
    Baut eine ODBC-Verbindung zu einer SQL Server-Datenbank auf.

    Die Zugangsdaten (Server, Benutzer, Passwort, Datenbankname) werden
    aus einer .env-Datei geladen, um sensible Informationen zu schützen.

    Args:
        db_name (str, optional): Name der Datenbank, auf die zugegriffen werden soll.
            Standardmäßig wird der Wert aus `config.py` verwendet.

    Returns:
        pyodbc.Connection: Aktive Verbindung zum SQL Server.

    Raises:
        pyodbc.Error: Wird ausgelöst, wenn keine Verbindung hergestellt werden kann.
    """
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={SQL_SERVER},{SQL_PORT};"
        f"DATABASE={db_name};"
        f"UID={SQL_USER};"
        f"PWD={SQL_PASS};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)


def hole_kundennummer(order_id: str) -> str | None:
    """
    Ermittelt die zu einer Amazon-Bestellnummer gehörige Kundennummer in der JTL-Datenbank.

    Diese Abfrage wird in der CSV-Verarbeitung verwendet, um Amazon-Bestellnummern
    (z. B. "306-1234567-8910111") durch interne Kundennummern zu ersetzen.

    Args:
        order_id (str): Amazon-Bestellnummer, wie sie im Feld `cExterneAuftragsnummer` gespeichert ist.

    Returns:
        str | None: Die Kundennummer als String, oder None, falls kein Treffer gefunden wird.

    Raises:
        Exception: Gibt alle aufgetretenen Fehler direkt weiter, damit sie zentral behandelt werden können.
    """
    try:
        with get_connection("toci") as conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT cKundennr
                    FROM [eazybusiness].Verkauf.tAuftrag
                    WHERE cExterneAuftragsnummer = ?
                """
                cursor.execute(query, (order_id,))
                result = cursor.fetchone()

                if result:
                    return result[0]  # Gibt die Kundennummer als String zurück
    except Exception as e:
        raise e  # Fehlerbehandlung findet im aufrufenden Modul statt

    return None  # Falls kein Ergebnis gefunden wurde


def teste_verbindung() -> bool | tuple[bool, str]:
    """
    Führt eine einfache Testabfrage (`SELECT 1`) aus, um zu prüfen,
    ob eine Verbindung zum SQL Server erfolgreich hergestellt werden kann.

    Returns:
        bool: True, wenn die Verbindung erfolgreich war.
        tuple[bool, str]: (False, Fehlermeldung) bei Verbindungsfehler.
    """
    try:
        with get_connection("toci") as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")  # Minimalabfrage zur Prüfung der Verbindung
        return True
    except Exception as e:
        return False, str(e)
