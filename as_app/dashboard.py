from django.utils import timezone
def dashboard_callback(request, context):
    """
    Django Unfold 대시보드 콜백 함수
    KPI 통계 및 차트 데이터를 생성하여 컨텍스트에 추가합니다.
    """
    from .models import ASTicket, InboundBatch
    
    today = timezone.now().date()
    
    # ── KPI 통계 ──
    # 1. 수리 대기 (Waiting)
    waiting_count = ASTicket.objects.filter(status=ASTicket.Status.WAITING).count()

    # 2. 금일 입고 (Inbound Today)
    inbound_today_count = ASTicket.objects.filter(
        inbound_date=today,
        status=ASTicket.Status.INBOUND
    ).count()

    # 3. 이번 달 입고 (Inbound This Month)
    inbound_month_count = ASTicket.objects.filter(
        inbound_date__month=today.month,
        inbound_date__year=today.year
    ).count()

    # ── 차트 데이터 (최근 7일 입/출고 추이) ──
    # 날짜별 데이터 집계는 복잡할 수 있으므로 간단히 예시 데이터 혹은 
    # django ORM aggregation을 사용해야 함.
    # 여기서는 간단히 KPI만 우선 전달하고, 차트는 navigation에 설정된 방식 따름.
    # Unfold에서는 'kpi' 키에 리스트를 전달하면 상단 카드로 표시됨.

    kpi = [
        {
            "title": "수리 대기",
            "metric": waiting_count,
            "footer": "현재 수리 대기 건수",
            "chart": [],
        },
        {
            "title": "금일 입고",
            "metric": inbound_today_count,
            "footer": "오늘 입고된 장비 수",
        },
        {
            "title": "이번 달 입고",
            "metric": inbound_month_count,
            "footer": f"{today.month}월 입고 누적",
        },
    ]

    context.update({
        "kpi": kpi,
    })
    return context
