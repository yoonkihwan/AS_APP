from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from .models import Tool

@staff_member_required
def get_tools_by_brand(request):
    """브랜드 ID를 받아 해당 브랜드의 툴 목록을 JSON으로 반환"""
    brand_id = request.GET.get("brand_id")
    if not brand_id:
        return JsonResponse({"tools": []})
    
    tools = Tool.objects.filter(brand_id=brand_id).values("id", "model_name")
    return JsonResponse({"tools": list(tools)})
