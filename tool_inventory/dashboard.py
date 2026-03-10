from django.urls import reverse_lazy
from django.db.models import Count


def dashboard_callback(request, context):
    """
    툴 인벤토리 앱 전용 대시보드 데이터 구성
    - 최근 입고/출고: 날짜+품목+업체별 그룹핑 (수량 표시)
    """
    from .models import Inventory, TodoItem

    # 최근 입고: 날짜 + 품목 + 입고처별로 묶어서 수량 집계 (최근 10건)
    recent_in = (
        Inventory.objects
        .filter(status='재고')
        .values('date', 'tool__model_name', 'supplier__name')
        .annotate(count=Count('id'))
        .order_by('-date', 'tool__model_name')[:10]
    )

    # 최근 출고: 날짜 + 품목 + 출고처별로 묶어서 수량 집계 (최근 10건)
    recent_out = (
        Inventory.objects
        .filter(status='출고')
        .values('release_date', 'tool__model_name', 'release_company__name')
        .annotate(count=Count('id'))
        .order_by('-release_date', 'tool__model_name')[:10]
    )

    context.update({
        "recent_in": recent_in,
        "recent_out": recent_out,
        "todo_items": TodoItem.objects.all()[:10],
        "todo_pending_count": TodoItem.objects.filter(is_done=False).count(),
    })

    return context
