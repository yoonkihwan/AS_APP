from django import forms
from .models import Inventory
from as_app.models import Brand, Tool
from unfold.widgets import (
    UnfoldAdminSelectWidget,
    UnfoldBooleanWidget,
    UnfoldAdminIntegerFieldWidget,
    UnfoldAdminTextInputWidget,
    UnfoldAdminCheckboxSelectMultiple,
)

class InventoryForm(forms.ModelForm):
    """Inventory Inline용 커스텀 폼 - 브랜드 필드 추가"""
    
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all(),
        label="브랜드",
        required=False,
        empty_label="---------",
        widget=UnfoldAdminSelectWidget(),
    )

    no_serial = forms.BooleanField(
        label="시리얼번호 없음",
        required=False,
        widget=UnfoldBooleanWidget(),
    )

    quantity = forms.IntegerField(
        label="수량",
        min_value=1,
        required=False,
        widget=UnfoldAdminIntegerFieldWidget(attrs={
            'style': 'width: 60px; pointer-events: none; opacity: 0.5; background-color: #f3f4f6;', 
            'placeholder': '1', 
            'readonly': 'readonly'
        }),
    )

    class Meta:
        model = Inventory
        fields = ["brand", "tool", "no_serial", "quantity", "serial"]
        widgets = {
            "tool": UnfoldAdminSelectWidget(),
            "serial": UnfoldAdminTextInputWidget(attrs={'style': 'width: 100%;'}),
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

class OutboundTicketForm(forms.ModelForm):
    """OutboundTicket Inline용 커스텀 폼 - 브랜드/장비별 재고(시리얼) 동적 필터링"""
    
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all(),
        label="브랜드",
        required=False,
        empty_label="---------",
        widget=UnfoldAdminSelectWidget(),
    )

    current_stock = forms.CharField(
        label="현재 재고",
        required=False,
        widget=UnfoldAdminTextInputWidget(attrs={
            'readonly': 'readonly', 
            'style': 'width:100px; text-align:center; pointer-events: none;'
        })
    )
    
    class Meta:
        from .models import OutboundTicket
        model = OutboundTicket
        fields = ["brand", "tool", "current_stock", "quantity", "inventories"]
        widgets = {
            "tool": UnfoldAdminSelectWidget(),
            "inventories": UnfoldAdminCheckboxSelectMultiple(attrs={"class": "checkbox-select-multiple"}),
            "quantity": UnfoldAdminIntegerFieldWidget(attrs={'style': 'width: 80px;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 기본적으로 툴 및 재고(시리얼) 목록 비움
        self.fields["tool"].queryset = Tool.objects.none()
        self.fields["inventories"].queryset = Inventory.objects.none()
        self.fields["inventories"].required = False

        # 수정 모드 혹은 에러 복구 시
        if self.instance.pk and getattr(self.instance, 'tool_id', None):
            try:
                tool = self.instance.tool
                brand = tool.brand
                
                self.fields["brand"].initial = brand
                self.fields["tool"].initial = tool
                self.fields["tool"].queryset = Tool.objects.filter(brand=brand)
                
                q = Inventory.objects.filter(tool=tool, status='재고')
                q = q | self.instance.inventories.all()
                self.fields["inventories"].queryset = q.distinct()
            except Exception:
                pass
        
        brand_id = None
        tool_id = None
        
        if "brand" in self.data:
            brand_id = self.data.get("brand")
        elif self.prefix and f"{self.prefix}-brand" in self.data:
            brand_id = self.data.get(f"{self.prefix}-brand")
            
        if "tool" in self.data:
            tool_id = self.data.get("tool")
        elif self.prefix and f"{self.prefix}-tool" in self.data:
            tool_id = self.data.get(f"{self.prefix}-tool")

        try:
            if brand_id:
                self.fields["tool"].queryset = Tool.objects.filter(brand_id=int(brand_id))
            if tool_id:
                q = Inventory.objects.filter(tool_id=int(tool_id), status='재고')
                if self.instance.pk:
                    q = q | self.instance.inventories.all()
                self.fields["inventories"].queryset = q.distinct()
        except (ValueError, TypeError):
            pass
