"""
TEMU Order Processing - Haupteinstiegspunkt
"""

import sys
from workflows.full_workflow import run_full_workflow

if __name__ == "__main__":
    try:
        success = run_full_workflow()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠ Abgebrochen")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
