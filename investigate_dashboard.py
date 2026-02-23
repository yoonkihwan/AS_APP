import os
import django
from django.utils import timezone
from django.db.models import Sum

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'as_project.settings')
django.setup()

from as_app.models import ASTicket

def main():
    today_utc = timezone.now().date()
    today_local = timezone.localdate()
    
    print(f"UTC Today: {today_utc}")
    print(f"Local Today: {today_local}")
    
    # Check shipped month count
    shipped_month_count = ASTicket.objects.filter(
        status=ASTicket.Status.SHIPPED,
        outbound_date__month=today_local.month,
        outbound_date__year=today_local.year,
    ).count()
    
    print(f"\nShipped this month (Local, count only): {shipped_month_count}")
    
    tickets = ASTicket.objects.filter(
        status=ASTicket.Status.SHIPPED,
        outbound_date__month=today_local.month,
        outbound_date__year=today_local.year,
    )
    for t in tickets:
        print(f" - ID: {t.id}, Outbound Date: {t.outbound_date}, Status: {t.status}, Repair Cost: {t.repair_cost}")

    # Check for ones that are NOT shipped but have an outbound date in this month
    other_outbound = ASTicket.objects.filter(
        outbound_date__month=today_local.month,
        outbound_date__year=today_local.year,
    ).exclude(status=ASTicket.Status.SHIPPED)
    
    print(f"\nTickets with outbound date this month but NOT shipped: {other_outbound.count()}")
    for t in other_outbound:
        print(f" - ID: {t.id}, Outbound Date: {t.outbound_date}, Status: {t.status}")

    # Check for shipped items without an outbound date
    no_date_shipped = ASTicket.objects.filter(
        status=ASTicket.Status.SHIPPED,
        outbound_date__isnull=True
    ).count()
    print(f"\nShipped tickets with NO outbound date: {no_date_shipped}")

if __name__ == '__main__':
    main()
