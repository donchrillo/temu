"""Workflow: Update Tracking"""

from src.services.tracking_service import update_tracking_from_jtl

def run_update_tracking():
    """Holt Tracking aus JTL"""
    return update_tracking_from_jtl()

if __name__ == "__main__":
    run_update_tracking()
