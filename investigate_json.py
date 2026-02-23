import os
import django
import json
from django.utils import timezone
from django.db.models import Sum

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'as_project.settings')
django.setup()

from as_app.models import ASTicket

def main():
    today_utc = timezone.now().date()
    today_local = timezone.localdate()
    
    shipped_tickets = ASTicket.objects.filter(
        status=ASTicket.Status.SHIPPED,
        outbound_date__month=today_local.month,
        outbound_date__year=today_local.year,
    )
    
    results = {
        "today_utc": str(today_utc),
        "today_local": str(today_local),
        "shipped_month_count": shipped_tickets.count(),
        "tickets": []
    }
    
    for t in shipped_tickets:
        results["tickets"].append({
            "id": t.id,
            "outbound_date": str(t.outbound_date),
            "repair_cost": t.repair_cost,
            "updated_at": str(t.updated_at)
        })

    with open('investigate_out.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    main()
