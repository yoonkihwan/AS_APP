import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'as_project.settings')
django.setup()

from as_app.models import ASTicket

tickets = ASTicket.objects.all()
updated_count = 0
for ticket in tickets:
    total_parts = sum(p.price for p in ticket.used_parts.all())
    total_with_vat = int(total_parts * 1.1)
    if ticket.repair_cost != total_with_vat:
        ticket.repair_cost = total_with_vat
        ticket.save(update_fields=['repair_cost'])
        updated_count += 1

print(f"Updated {updated_count} tickets with 10% VAT.")
