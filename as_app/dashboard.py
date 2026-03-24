from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from django.urls import reverse


def dashboard_callback(request, context):
    """
    Django Unfold 대시보드 콜백 함수
    KPI 통계, 수리 매출 요약, 수리 대기 목록, 최근 출고 목록 데이터를 생성하여 컨텍스트에 추가합니다.
    """
    from .models import ASTicket

    today = timezone.localdate()
    thirty_days_ago = today - timedelta(days=30)
    
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    start_of_month = today.replace(day=1)
    start_of_year = today.replace(month=1, day=1)

    # ── KPI 통계 ──
    # 1. 장기 미처리 (30일 이상 경과)
    long_pending_count = ASTicket.objects.filter(
        inbound_date__lte=thirty_days_ago,
        status=ASTicket.Status.INBOUND,
    ).count()

    # 2. 수리 대기 (입고 상태이거나 수리대기 상태)
    waiting_count = ASTicket.objects.filter(
        status=ASTicket.Status.INBOUND,
    ).count()



    # 4. 수리 완료 (미출고)
    repaired_count = ASTicket.objects.filter(
        status=ASTicket.Status.REPAIRED,
    ).count()

    # 4-1. 수리의뢰 중 (외주 의뢰 중)
    outsourced_count = ASTicket.objects.filter(
        status=ASTicket.Status.OUTSOURCED,
    ).count()

    # 4-2. 수리보류 중
    hold_count = ASTicket.objects.filter(
        status=ASTicket.Status.HOLD,
    ).count()



    # ── KPI 카드 링크 생성 ──
    history_url = reverse("admin:as_app_ashistory_changelist")
    long_pending_url = f"{history_url}?status__exact=inbound&inbound_date__lte={thirty_days_ago.isoformat()}"
    waiting_url = f"{history_url}?status__exact=inbound"
    outsourced_url = f"{history_url}?status__exact=outsourced"
    repaired_url = f"{history_url}?status__exact=repaired"
    hold_url = f"{history_url}?status__exact=hold"

    kpi = [
        {
            "title": "장기 미처리 대기",
            "metric": long_pending_count,
            "footer": "30일 이상 방치된 건수",
            "icon": "warning",
            "color": "#ef4444",  # red
            "link": long_pending_url,
        },
        {
            "title": "수리 대기",
            "metric": waiting_count,
            "footer": "현재 수리 대기 중",
            "icon": "pending_actions",
            "color": "#f59e0b",  # amber
            "link": waiting_url,
        },
        {
            "title": "수리의뢰 중",
            "metric": outsourced_count,
            "footer": "현재 외주 의뢰 중인 건수",
            "icon": "send",
            "color": "#eab308",  # yellow
            "link": outsourced_url,
        },
        {
            "title": "수리 완료 (미출고)",
            "metric": repaired_count,
            "footer": "출고 대기 중인 건수",
            "icon": "check_circle",
            "color": "#10b981",  # emerald
            "link": repaired_url,
        },
        {
            "title": "수리보류",
            "metric": hold_count,
            "footer": "견적 발송 후 결정 대기 중",
            "icon": "pause_circle",
            "color": "#9333ea",  # purple
            "link": hold_url,
        },
    ]

    # ── 수리 매출 요약 (출고 완료 기준) ──
    shipped_qs = ASTicket.objects.filter(status=ASTicket.Status.SHIPPED)


    week_rev = shipped_qs.filter(outbound_date__gte=start_of_week, outbound_date__lte=end_of_week).aggregate(Sum('repair_cost'))['repair_cost__sum'] or 0
    # "이번 달" 통계 기준을 출고 건수 조회 기준과 동일하게 맞춤 (outbound_date__lte=today -> __month=today.month)
    month_rev = shipped_qs.filter(outbound_date__month=today.month, outbound_date__year=today.year).aggregate(Sum('repair_cost'))['repair_cost__sum'] or 0
    year_rev = shipped_qs.filter(outbound_date__year=today.year).aggregate(Sum('repair_cost'))['repair_cost__sum'] or 0

    revenue_data = [
        {"title": "이번 주 수리매출", "amount": f"{week_rev:,}", "icon": "date_range", "color": "#3b82f6"},  # blue
        {"title": "이번 달 수리매출", "amount": f"{month_rev:,}", "icon": "calendar_month", "color": "#8b5cf6"},  # violet
        {"title": "이번 년도 수리매출", "amount": f"{year_rev:,}", "icon": "event_note", "color": "#6366f1"},     # indigo
    ]

    # ── ③ 수리 대기 목록 (최근 10건) ──
    pending_tickets = (
        ASTicket.objects.filter(status=ASTicket.Status.INBOUND)
        .select_related("company", "tool", "tool__brand")
        .order_by("inbound_date", "created_at")[:10]
    )

    # ── ④ 최근 출고 목록 (최근 10건) ──
    recent_shipped = (
        ASTicket.objects.filter(status=ASTicket.Status.SHIPPED)
        .select_related("company", "tool", "tool__brand")
        .order_by("-outbound_date", "-updated_at")[:10]
    )

    context.update({
        "kpi": kpi,
        "revenue_data": revenue_data,
        "pending_tickets": pending_tickets,
        "recent_shipped": recent_shipped,
    })
    return context
