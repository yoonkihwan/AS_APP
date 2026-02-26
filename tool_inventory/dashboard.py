from django.urls import reverse_lazy

def dashboard_callback(request, context):
    """
    툴 인벤토리 앱 전용 대시보드 데이터 구성
    """
    from .models import Inventory, TodoItem
    
    context.update({
        "total_inventory": Inventory.objects.filter(status='재고').count(),
        "total_released": Inventory.objects.filter(status='출고').count(),
        "recent_in": Inventory.objects.filter(status='재고').order_by('-date')[:5],
        "recent_out": Inventory.objects.filter(status='출고').order_by('-release_date')[:5],
        "todo_items": TodoItem.objects.all()[:10],
        "todo_pending_count": TodoItem.objects.filter(is_done=False).count(),
    })
    
    return context
