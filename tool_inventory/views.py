from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from .models import Inventory

@staff_member_required
def get_inventory_by_tool(request):
    """툴 ID를 받아 현재 '재고' 상태인 시리얼 번호 목록을 JSON으로 반환"""
    tool_id = request.GET.get("tool_id")
    if not tool_id:
        return JsonResponse({"inventory": []})
    
    # status='재고' 인 아이템들만
    inventory_items = Inventory.objects.filter(tool_id=tool_id, status='재고').values("id", "serial")
    return JsonResponse({"inventory": list(inventory_items)})
