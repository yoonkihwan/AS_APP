from django import forms
from .models import Inventory
from as_app.models import Brand, Tool
from unfold.widgets import UnfoldAdminSelectWidget

class InventoryForm(forms.ModelForm):
    """Inventory Inline용 커스텀 폼 - 브랜드 필드 추가"""
    
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all(),
        label="브랜드",
        required=False,
        empty_label="---------",
        widget=UnfoldAdminSelectWidget(),
    )

    class Meta:
        model = Inventory
        fields = ["brand", "tool", "serial"]
        widgets = {
            "tool": UnfoldAdminSelectWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 기본적으로 툴 목록을 비움
        self.fields["tool"].queryset = Tool.objects.none()

        # 수정 모드 시 또는 오류 시
        if self.instance.pk and self.instance.tool_id:
            try:
                brand = self.instance.tool.brand
                self.fields["brand"].initial = brand
                self.fields["tool"].queryset = Tool.objects.filter(brand=brand)
            except Tool.DoesNotExist:
                pass
        
        if "brand" in self.data:
            try:
                brand_id = int(self.data.get("brand"))
                self.fields["tool"].queryset = Tool.objects.filter(brand_id=brand_id)
            except (ValueError, TypeError):
                pass
        elif self.prefix:
             brand_key = f"{self.prefix}-brand"
             if brand_key in self.data:
                 try:
                     brand_id = int(self.data.get(brand_key))
                     self.fields["tool"].queryset = Tool.objects.filter(brand_id=brand_id)
                 except (ValueError, TypeError):
                     pass
