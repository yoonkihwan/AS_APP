import os
import sqlite3
import django

# Django 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'as_project.settings')
django.setup()

from tool_inventory.models import Supplier, ReleaseSupplier, ItemName, Inventory

def run():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inventory.db')
    if not os.path.exists(db_path):
        print("inventory.db file not found!")
        return

    conn = sqlite3.connect(db_path)
    cr = conn.cursor()

    # 1. 마스터 데이터 마이그레이션 (Suppliers, ReleaseSuppliers, ItemNames)
    print("Migrating master data...")
    
    cr.execute("SELECT name FROM suppliers")
    for row in cr.fetchall():
        if row[0]:
            Supplier.objects.get_or_create(name=row[0])
            
    cr.execute("SELECT name FROM release_suppliers")
    for row in cr.fetchall():
        if row[0]:
            ReleaseSupplier.objects.get_or_create(name=row[0])
            
    cr.execute("SELECT name FROM item_names")
    for row in cr.fetchall():
        if row[0]:
            ItemName.objects.get_or_create(name=row[0])

    # 2. 메인 인벤토리 데이터 마이그레이션
    print("Migrating inventory data...")
    cr.execute("SELECT id, supplier, date, name, serial, release_date, release_supplier, status FROM inventory")
    
    count = 0
    for row in cr.fetchall():
        uid, sup, dt, itm, seq, rdt, rsup, st = row
        
        # 외래키 객체 찾기
        supplier = Supplier.objects.filter(name=sup).first() if sup else None
        item_name = ItemName.objects.filter(name=itm).first() if itm else None
        release_supplier = ReleaseSupplier.objects.filter(name=rsup).first() if rsup else None
        
        # 빈 문자열 날짜 처리
        r_date = rdt if rdt and rdt.strip() else None
        i_date = dt if dt and dt.strip() else '2000-01-01'  # 빈 날짜 방어코드
        
        try:
            Inventory.objects.update_or_create(
                id=uid,
                defaults={
                    'supplier': supplier,
                    'date': i_date,
                    'name': item_name,
                    'serial': seq if seq else '',
                    'release_date': r_date,
                    'release_supplier': release_supplier,
                    'status': st if st else '재고',
                }
            )
            count += 1
        except Exception as e:
            print(f"Error importing row {uid}: {e}")
            
    print(f"Imported {count} inventory records successfully.")
    conn.close()

if __name__ == '__main__':
    run()
