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
        
        # Alte Services sind gelöscht - nicht mehr testen!
        # from services.api_sync_service import import_api_responses_to_db
        # from services.api_export_service import export_to_temu_api
        # from services.xml_generator_service import generate_xml_for_orders
        # from services.tracking_service import update_tracking_from_jtl
        
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

def test_new_repositories_and_services():
    """Test: Neue Repositories & Services funktionieren"""
    print("✓ Testing New Architecture (Repositories + Services)...")
    
    try:
        from src.db.repositories.order_repository import OrderRepository
        print("  ✓ OrderRepository importiert")
        
        from src.db.repositories.order_item_repository import OrderItemRepository
        print("  ✓ OrderItemRepository importiert")
        
        from src.modules.orders.service import OrderService
        print("  ✓ OrderService importiert")
        
        from src.modules.tracking.service import TrackingService
        print("  ✓ TrackingService importiert")
        
        from src.modules.xml_export.service import XmlExportService
        print("  ✓ XmlExportService importiert")
        
        print("\n✓ Alle neuen Imports erfolgreich!\n")
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
        "New Architecture": test_new_repositories_and_services(),
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
