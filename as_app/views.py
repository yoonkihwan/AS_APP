from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from .models import Tool

def get_tools_by_brand(request):
    """브랜드 ID를 받아 해당 브랜드의 툴 목록을 JSON으로 반환"""
    if not (request.user.is_authenticated and request.user.is_staff):
        return JsonResponse({"tools": []})
    brand_id = request.GET.get("brand_id")
    if not brand_id:
        return JsonResponse({"tools": []})
    
    tools = Tool.objects.filter(brand_id=brand_id).order_by("model_name").values("id", "model_name")
    return JsonResponse({"tools": list(tools)})
