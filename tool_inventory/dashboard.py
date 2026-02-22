from django.urls import reverse_lazy

def dashboard_callback(request, context):
    """
    툴 인벤토리 앱 전용 대시보드 데이터 구성
    """
    from .models import Inventory
    
    context.update({
        "total_inventory": Inventory.objects.filter(status='재고').count(),
        "total_released": Inventory.objects.filter(status='출고').count(),
        "recent_in": Inventory.objects.filter(status='재고').order_by('-date')[:5],
        "recent_out": Inventory.objects.filter(status='출고').order_by('-release_date')[:5],
    })
    
    return context
