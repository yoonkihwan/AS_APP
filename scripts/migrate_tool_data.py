import os
import sys
import django

# Setup Django environment
sys.path.append(r"c:\Users\rlao1\AS_APP")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'as_project.settings')
django.setup()

from tool_inventory.models import Inventory, InventoryBatch, Supplier, ReleaseSupplier, ItemName
from as_app.models import OutsourceCompany, Company, Tool, Brand

def migrate_data():
    print("Starting data migration from Tool Inventory legacy tables to AS_APP direct refs...")

    # Define a default brand for items if not specified
    default_brand, _ = Brand.objects.get_or_create(name="기타 (미분류)")

    # Phase 1: Create master records in AS_APP for unmapped Tool Inventory ones
    for supplier in Supplier.objects.all():
        OutsourceCompany.objects.get_or_create(name=supplier.name)

    for r_supplier in ReleaseSupplier.objects.all():
        Company.objects.get_or_create(name=r_supplier.name)

    for item in ItemName.objects.all():
        Tool.objects.get_or_create(brand=default_brand, model_name=item.name)

    print("Master record synced.")

    # Phase 2: Update existing Inventory records to point to AS_APP models
    inventories = Inventory.objects.all()
    updated_count = 0
    for inv in inventories:
        dirty = False
        if inv.supplier_id:
            # Look up by name
            out_comp = OutsourceCompany.objects.filter(name=inv.supplier_id).first()
            if out_comp:
                inv.as_supplier = out_comp
                dirty = True
        
        if inv.name_id:
            tool = Tool.objects.filter(model_name=inv.name_id, brand=default_brand).first()
            if tool:
                inv.as_tool = tool
                dirty = True

        if inv.release_supplier_id:
            company = Company.objects.filter(name=inv.release_supplier_id).first()
            if company:
                inv.as_release_company = company
                dirty = True

        if dirty:
            inv.save(update_fields=['as_supplier', 'as_tool', 'as_release_company'])
            updated_count += 1
            
    print(f"Updated {updated_count} Inventory records.")

    # Phase 3: Update existing InventoryBatch records to point to AS_APP models
    batches = InventoryBatch.objects.all()
    batch_count = 0
    for batch in batches:
        if batch.supplier_id:
            out_comp = OutsourceCompany.objects.filter(name=batch.supplier_id).first()
            if out_comp:
                batch.as_supplier = out_comp
                batch.save(update_fields=['as_supplier'])
                batch_count += 1

    print(f"Updated {batch_count} InventoryBatch records.")
    print("Migration completed.")

if __name__ == '__main__':
    migrate_data()
