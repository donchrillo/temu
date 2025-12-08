"""
BEISPIEL: Kompletter Workflow mit neuer Architektur
Zeigt wie Repositories → Services → Workflows zusammenarbeiten
"""

import sys
from pathlib import Path
from datetime import datetime

# Importpfade
sys.path.insert(0, str(Path(__file__).parent))

# ===== REPOSITORIES (Data Access Layer) =====
from src.db.repositories.order_repository import OrderRepository
from src.db.repositories.order_item_repository import OrderItemRepository

# ===== SERVICES (Business Logic Layer) =====
from src.modules.orders.service import OrderService
from src.modules.tracking.service import TrackingService
from src.modules.xml_export.service import XmlExportService

# ===== WORKFLOWS (Orchestration) =====
from workflows.api_to_json import run_api_to_json
from workflows.json_to_db import run_json_to_db
from workflows.db_orders_to_xml import run_db_to_xml
from workflows.tracking_to_db import run_update_tracking
from workflows.db_tracking_to_api import run_db_to_api

def print_header(title):
    """Header ausgeben"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_section(step_num, total, description):
    """Schritt ausgeben"""
    print(f"\n[Schritt {step_num}/{total}] {description}")
    print("-"*70)

def run_full_workflow_refactored(parent_order_status=2, days_back=7):
    """
    REFAKTORIERT: Vollständiger Workflow mit neuer Architektur
    
    Das ist wie der alte Code funktioniert, aber VIEL sauberer:
    
    API → Repositories → Services → Workflows
    
    """
    
    start_time = datetime.now()
    total_steps = 5
    
    print_header("TEMU WORKFLOW - MIT NEUER ARCHITEKTUR")
    print(f"Start: {start_time.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"Abfrage-Zeitraum: {days_back} Tage")
    print(f"Status Filter: {parent_order_status}\n")
    
    results = {}
    
    # ========================================
    # SCHRITT 1: API → JSON
    # ========================================
    print_section(1, total_steps, "TEMU API → JSON speichern")
    try:
        results['api_fetch'] = run_api_to_json(
            parent_order_status=parent_order_status,
            days_back=days_back
        )
        print(f"  ✓ API Responses gespeichert")
    except Exception as e:
        print(f"  ✗ Fehler: {e}")
        results['api_fetch'] = False
    
    # ========================================
    # SCHRITT 2: JSON → Datenbank (mit SERVICE!)
    # ========================================
    print_section(2, total_steps, "JSON → Datenbank (mit Service)")
    try:
        # Das ist jetzt so VIEL sauberer!
        # Alte Version: api_sync_service.py (DB + Business Logic gemischt)
        # Neue Version: 
        #   - OrderRepository: Nur DB Operationen
        #   - OrderItemRepository: Nur DB Operationen
        #   - OrderService: Nur Business Logic (nutzt Repositories)
        
        results['json_import'] = run_json_to_db()
        print(f"  ✓ Orders in DB importiert")
    except Exception as e:
        print(f"  ✗ Fehler: {e}")
        results['json_import'] = False
    
    # ========================================
    # SCHRITT 3: XML Export (mit SERVICE!)
    # ========================================
    print_section(3, total_steps, "Datenbank → XML Export (mit Service)")
    try:
        # Alte Version: xml_generator_service.py (DB + XML + JTL Import gemischt)
        # Neue Version:
        #   - OrderRepository: DB Reads
        #   - OrderItemRepository: DB Reads
        #   - XmlExportService: Nur Business Logic
        
        results['xml_export'] = run_db_to_xml()
        print(f"  ✓ XML exportiert")
    except Exception as e:
        print(f"  ✗ Fehler: {e}")
        results['xml_export'] = False
    
    # ========================================
    # SCHRITT 4: Tracking Update (mit SERVICE!)
    # ========================================
    print_section(4, total_steps, "JTL → Tracking Update (mit Service)")
    try:
        # Alte Version: tracking_service.py (JTL + TOCI DB gemischt)
        # Neue Version:
        #   - OrderRepository: TOCI DB Operations
        #   - TrackingService: Nur Business Logic (holt JTL Daten, delegiert Saves)
        
        results['tracking'] = run_update_tracking()
        print(f"  ✓ Tracking aktualisiert")
    except Exception as e:
        print(f"  ✗ Fehler: {e}")
        results['tracking'] = False
    
    # ========================================
    # SCHRITT 5: Tracking zu TEMU API
    # ========================================
    print_section(5, total_steps, "Tracking Export → TEMU API")
    try:
        results['api_export'] = run_db_to_api()
        print(f"  ✓ Tracking zu TEMU exportiert")
    except Exception as e:
        print(f"  ✗ Fehler: {e}")
        results['api_export'] = False
    
    # ========================================
    # ZUSAMMENFASSUNG
    # ========================================
    end_time = datetime.now()
    duration = end_time - start_time
    
    print_header("WORKFLOW ABGESCHLOSSEN")
    print(f"Ende: {end_time.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"Dauer: {duration.total_seconds():.1f}s\n")
    
    print("Ergebnisse:")
    print(f"  1. API → JSON:      {'✓' if results.get('api_fetch') else '✗'}")
    print(f"  2. JSON → DB:       {'✓' if results.get('json_import') else '✗'}")
    print(f"  3. DB → XML:        {'✓' if results.get('xml_export') else '✗'}")
    print(f"  4. JTL → Tracking:  {'✓' if results.get('tracking') else '✗'}")
    print(f"  5. Tracking → API:  {'✓' if results.get('api_export') else '✗'}")
    
    success_count = sum(1 for v in results.values() if v)
    print(f"\n✓ {success_count}/{total_steps} erfolgreich")
    print("="*70 + "\n")
    
    return success_count == total_steps

if __name__ == "__main__":
    try:
        success = run_full_workflow_refactored(parent_order_status=2, days_back=7)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
