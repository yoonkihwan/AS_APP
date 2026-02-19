from django.utils import timezone
from django.db.models import Count


def dashboard_callback(request, context):
    """
    Django Unfold 대시보드 콜백 함수
    KPI 통계, 수리 대기 목록, 최근 출고 목록 데이터를 생성하여 컨텍스트에 추가합니다.
    """
    from .models import ASTicket

    today = timezone.now().date()

    # ── KPI 통계 ──
    # 1. 금일 입고
    inbound_today_count = ASTicket.objects.filter(
        inbound_date=today,
        status=ASTicket.Status.INBOUND,
    ).count()

    # 2. 수리 대기 (입고 상태)
    waiting_count = ASTicket.objects.filter(
        status=ASTicket.Status.INBOUND,
    ).count()

    # 3. 이번 달 입고 누적
    inbound_month_count = ASTicket.objects.filter(
        inbound_date__month=today.month,
        inbound_date__year=today.year,
    ).count()

    # 4. 수리 완료 (미출고)
    repaired_count = ASTicket.objects.filter(
        status=ASTicket.Status.REPAIRED,
    ).count()

    # 5. 이번 달 출고
    shipped_month_count = ASTicket.objects.filter(
        status=ASTicket.Status.SHIPPED,
        outbound_date__month=today.month,
        outbound_date__year=today.year,
    ).count()

    kpi = [
        {
            "title": "금일 입고",
            "metric": inbound_today_count,
            "footer": "오늘 입고된 장비 수",
            "icon": "inbox",
            "color": "#3b82f6",  # blue
        },
        {
            "title": "수리 대기",
            "metric": waiting_count,
            "footer": "현재 수리 대기 건수",
            "icon": "pending_actions",
            "color": "#f59e0b",  # amber
        },
        {
            "title": "이번 달 입고",
            "metric": inbound_month_count,
            "footer": f"{today.month}월 입고 누적",
            "icon": "calendar_month",
            "color": "#8b5cf6",  # violet
        },
        {
            "title": "수리 완료 (미출고)",
            "metric": repaired_count,
            "footer": "출고 대기 중인 건수",
            "icon": "check_circle",
            "color": "#10b981",  # emerald
        },
        {
            "title": "이번 달 출고",
            "metric": shipped_month_count,
            "footer": f"{today.month}월 출고 누적",
            "icon": "local_shipping",
            "color": "#06b6d4",  # cyan
        },
    ]

    # ── ③ 수리 대기 목록 (최근 10건) ──
    pending_tickets = (
        ASTicket.objects.filter(status=ASTicket.Status.INBOUND)
        .select_related("company", "tool", "tool__brand")
        .order_by("-inbound_date", "-created_at")[:10]
    )

    # ── ④ 최근 출고 목록 (최근 10건) ──
    recent_shipped = (
        ASTicket.objects.filter(status=ASTicket.Status.SHIPPED)
        .select_related("company", "tool", "tool__brand")
        .order_by("-outbound_date", "-updated_at")[:10]
    )

    context.update({
        "kpi": kpi,
        "pending_tickets": pending_tickets,
        "recent_shipped": recent_shipped,
    })
    return context
