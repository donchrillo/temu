"""Test: Services Migration"""

import sys
from pathlib import Path

# Füge root zum Path hinzu
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

def test_imports():
    """Test: Alle Service-Imports funktionieren"""
    print("\n✓ Testing Service Imports...")
    
    try:
        from services.temu_signature import calculate_signature
        print("  ✓ temu_signature importiert")
        
        from services.temu_client import TemuApiClient
        print("  ✓ temu_client importiert")
        
        from services.temu_orders_api import TemuOrdersApi
        print("  ✓ temu_orders_api importiert")
        
        from services.api_fetch_service import fetch_and_save_orders
        print("  ✓ api_fetch_service importiert")
        
        from services.api_sync_service import import_api_responses_to_db
        print("  ✓ api_sync_service importiert")
        
        from services.api_export_service import export_to_temu_api
        print("  ✓ api_export_service importiert")
        
        from services.xml_generator_service import generate_xml_for_orders
        print("  ✓ xml_generator_service importiert")
        
        from services.tracking_service import update_tracking_from_jtl
        print("  ✓ tracking_service importiert")
        
        print("\n✓ Alle Service-Imports erfolgreich!\n")
        return True
    except ImportError as e:
        print(f"\n✗ Import Fehler: {e}\n")
        return False

def test_workflow_imports():
    """Test: Workflows funktionieren"""
    print("✓ Testing Workflow Imports...")
    
    try:
        from workflows.api_to_json import run_api_to_json
        print("  ✓ api_to_json importiert")
        
        from workflows.json_to_db import run_json_to_db
        print("  ✓ json_to_db importiert")
        
        from workflows.db_orders_to_xml import run_db_to_xml
        print("  ✓ db_orders_to_xml importiert")
        
        from workflows.tracking_to_db import run_update_tracking
        print("  ✓ tracking_to_db importiert")
        
        from workflows.db_tracking_to_api import run_db_to_api
        print("  ✓ db_tracking_to_api importiert")
        
        print("\n✓ Alle Workflow-Imports erfolgreich!\n")
        return True
    except ImportError as e:
        print(f"\n✗ Import Fehler: {e}\n")
        return False

def test_dashboard_imports():
    """Test: Dashboard funktioniert"""
    print("✓ Testing Dashboard Imports...")
    
    try:
        from dashboard.jobs import JobType, JobStatusEnum
        print("  ✓ dashboard.jobs importiert")
        
        from dashboard.scheduler import SchedulerService
        print("  ✓ dashboard.scheduler importiert")
        
        print("\n✓ Alle Dashboard-Imports erfolgreich!\n")
        return True
    except ImportError as e:
        print(f"\n✗ Import Fehler: {e}\n")
        return False

def test_db_imports():
    """Test: Database Layer funktioniert"""
    print("✓ Testing Database Imports...")
    
    try:
        from db.connection import get_db_connection
        print("  ✓ db.connection importiert")
        
        print("\n✓ Alle Database-Imports erfolgreich!\n")
        return True
    except ImportError as e:
        print(f"\n✗ Import Fehler: {e}\n")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TEMU PROJECT - REFACTORING TESTS")
    print("=" * 60)
    
    results = {
        "Services": test_imports(),
        "Workflows": test_workflow_imports(),
        "Dashboard": test_dashboard_imports(),
        "Database": test_db_imports(),
    }
    
    print("=" * 60)
    print("ERGEBNISSE")
    print("=" * 60)
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name}: {status}")
    
    success = all(results.values())
    print("=" * 60)
    if success:
        print("✓ Alle Tests bestanden!")
    else:
        print("✗ Einige Tests sind fehlgeschlagen!")
    print("=" * 60 + "\n")
    
    sys.exit(0 if success else 1)
