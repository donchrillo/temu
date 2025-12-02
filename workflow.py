"""
TEMU Order Processing Workflow
Führt alle Schritte des TEMU-Prozesses nacheinander aus:
1. CSV Import → Datenbank
2. XML Erstellung → JTL Import
3. Tracking Update aus JTL
4. Excel Export für TEMU
5. Stornierte Bestellungen anzeigen
"""

import sys
from datetime import datetime

# Module importieren
import import_orders
import create_xml_from_db
import update_tracking
import export_tracking
import stornierte_bestellungen

def print_header(title):
    """Gibt einen formatierten Header aus."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_step(step_num, total_steps, description):
    """Gibt den aktuellen Schritt aus."""
    print(f"\n[Schritt {step_num}/{total_steps}] {description}")
    print("-" * 70)

def run_workflow():
    """Führt den kompletten TEMU-Workflow aus."""
    
    start_time = datetime.now()
    
    print_header("TEMU ORDER PROCESSING WORKFLOW")
    print(f"Start: {start_time.strftime('%d.%m.%Y %H:%M:%S')}")
    
    total_steps = 5  # Erhöht auf 5 Schritte
    results = {
        'import_orders': False,
        'create_xml': False,
        'update_tracking': False,
        'export_tracking': False,
        'stornierte': True  # Immer True, da nur Anzeige
    }
    
    # ========== SCHRITT 1: CSV Import ==========
    print_step(1, total_steps, "CSV Import → Datenbank (inkl. TEMU-Bestätigungen)")
    try:
        results['import_orders'] = import_orders.import_csv_to_database(
            import_orders.CSV_DATEINAME
        )
        if results['import_orders']:
            print("✓ CSV Import erfolgreich abgeschlossen")
            print("  (Bestellungen mit Status 'Versandt'/'Zugestellt' werden als 'temu_gemeldet' markiert)")
        else:
            print("⚠ CSV Import fehlgeschlagen (aber Workflow wird fortgesetzt)")
    except Exception as e:
        print(f"✗ FEHLER beim CSV Import: {e}")
        print("⚠ Workflow wird fortgesetzt...")
    
    # ========== SCHRITT 2: XML Erstellung ==========
    print_step(2, total_steps, "XML Erstellung → JTL Import")
    try:
        results['create_xml'] = create_xml_from_db.create_xml_for_orders()
        if results['create_xml']:
            print("✓ XML Erstellung erfolgreich abgeschlossen")
        else:
            print("⚠ XML Erstellung fehlgeschlagen (aber Workflow wird fortgesetzt)")
    except Exception as e:
        print(f"✗ FEHLER bei XML Erstellung: {e}")
        print("⚠ Workflow wird fortgesetzt...")
    
    # ========== SCHRITT 3: Tracking Update ==========
    print_step(3, total_steps, "Tracking Update aus JTL")
    try:
        results['update_tracking'] = update_tracking.update_tracking_from_jtl()
        if results['update_tracking']:
            print("✓ Tracking Update erfolgreich abgeschlossen")
        else:
            print("⚠ Tracking Update fehlgeschlagen (aber Workflow wird fortgesetzt)")
    except Exception as e:
        print(f"✗ FEHLER beim Tracking Update: {e}")
        print("⚠ Workflow wird fortgesetzt...")
    
    # ========== SCHRITT 4: Excel Export ==========
    print_step(4, total_steps, "Excel Export für TEMU")
    try:
        results['export_tracking'] = export_tracking.export_tracking_to_excel()
        if results['export_tracking']:
            print("✓ Excel Export erfolgreich abgeschlossen")
        else:
            print("⚠ Excel Export fehlgeschlagen")
    except Exception as e:
        print(f"✗ FEHLER beim Excel Export: {e}")
    
    # ========== SCHRITT 5: Stornierte Bestellungen ==========
    print_step(5, total_steps, "Stornierte Bestellungen prüfen")
    try:
        stornierte_bestellungen.show_stornierte_bestellungen()
        print("✓ Stornierte Bestellungen geprüft")
    except Exception as e:
        print(f"✗ FEHLER beim Prüfen stornierter Bestellungen: {e}")
        results['stornierte'] = False
    
    # ========== ZUSAMMENFASSUNG ==========
    end_time = datetime.now()
    duration = end_time - start_time
    
    print_header("WORKFLOW ABGESCHLOSSEN")
    print(f"Ende: {end_time.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"Dauer: {duration.total_seconds():.1f} Sekunden")
    print("\nErgebnisse:")
    print(f"  1. CSV Import:       {'✓ Erfolgreich' if results['import_orders'] else '✗ Fehlgeschlagen'}")
    print(f"  2. XML Erstellung:   {'✓ Erfolgreich' if results['create_xml'] else '✗ Fehlgeschlagen'}")
    print(f"  3. Tracking Update:  {'✓ Erfolgreich' if results['update_tracking'] else '✗ Fehlgeschlagen'}")
    print(f"  4. Excel Export:     {'✓ Erfolgreich' if results['export_tracking'] else '✗ Fehlgeschlagen'}")
    print(f"  5. Stornierte Check: {'✓ Erfolgreich' if results['stornierte'] else '✗ Fehlgeschlagen'}")
    
    success_count = sum(results.values())
    print(f"\n{success_count}/{total_steps} Schritte erfolgreich")
    print("=" * 70 + "\n")
    
    # Rückgabewert für Automation
    return success_count == total_steps

if __name__ == "__main__":
    try:
        success = run_workflow()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ Workflow wurde vom Benutzer abgebrochen")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n✗ FATALER FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
