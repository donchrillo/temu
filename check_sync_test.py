
from modules.shared import db_connect
from sqlalchemy import text
from modules.shared.config.settings import DB_TOCI

def check_sync():
    with db_connect(DB_TOCI) as conn:
        sql = text("""
            SELECT TOP 10 p.sku, inv.jtl_stock, inv.temu_stock, inv.needs_sync 
            FROM temu_inventory inv 
            JOIN temu_products p ON inv.product_id = p.id 
            WHERE inv.needs_sync = 1
        """)
        result = conn.execute(sql).fetchall()
        for row in result:
            print(f"SKU: {row[0]} | JTL: {row[1]} | TEMU: {row[2]} | Sync: {row[3]}")

if __name__ == '__main__':
    check_sync()
