"""
TEMU Workflow - CLI Entry Point
Alle Ausgaben gehen direkt in SQL Server [dbo].[scheduler_logs]
"""

import sys
import argparse
from pathlib import Path

# Importpfade
sys.path.insert(0, str(Path(__file__).parent))

from workflows.temu_orders import run_temu_orders
from src.services.logger import app_logger


def parse_arguments():
    """Parse Command Line Arguments"""
    parser = argparse.ArgumentParser(
        description='TEMU ERP Workflow - Order Sync',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python main.py
  python main.py --status 2 --days 7
  python main.py --status 4 --days 30 -v
  python main.py -s 3 -d 90 --verbose

TEMU Status Codes (GÜLTIG):
  2 = UN_SHIPPING (nicht versendet)
  3 = CANCELLED (storniert)
  4 = SHIPPED (versendet)
  5 = RECEIPTED (Order received)

Alle Logs werden automatisch in [dbo].[scheduler_logs] gespeichert.
        """
    )
    
    parser.add_argument(
        '--status', '-s',
        type=int,
        default=2,
        help='TEMU Order Status (2, 3, 4, 5) [default: 2]'
    )
    
    parser.add_argument(
        '--days', '-d',
        type=int,
        default=7,
        help='Anzahl Tage zurück [default: 7]'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose Output (Debug-Modus)'
    )
    
    return parser.parse_args()


def run(args):
    """Hauptfunktion - führt TEMU Order Sync aus"""
    success = run_temu_orders(
        parent_order_status=args.status,
        days_back=args.days,
        verbose=args.verbose
    )
    return success


if __name__ == "__main__":
    try:
        args = parse_arguments()
        success = run(args)
        sys.exit(0 if success else 1)
    
    except Exception as e:
        app_logger.error(f"FATAL ERROR: {e}", exc_info=True)
        sys.exit(1)