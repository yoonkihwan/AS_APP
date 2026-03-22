from django import forms
from .models import ASTicket, Brand, Tool
from unfold.admin import ModelAdmin, TabularInline
from unfold.widgets import UnfoldAdminSelectWidget

class ASTicketForm(forms.ModelForm):
    """ASTicket Inline용 커스텀 폼 - 브랜드 필드 추가"""
    
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all(),
        label="브랜드",
        required=False,
        empty_label="---------",
        widget=UnfoldAdminSelectWidget(),  # Unfold 스타일 적용
    )
    no_serial_number = forms.BooleanField(
        label="시리얼 없음",
        required=False,
    )
    quantity = forms.IntegerField(
        label="개수",
        min_value=1,
        initial=1,
        required=False,
        widget=forms.NumberInput(attrs={'style': 'width: 60px;'}),
    )

    class Meta:
        model = ASTicket
        fields = ["brand", "tool", "no_serial_number", "quantity", "serial_number"]
        widgets = {
            "tool": UnfoldAdminSelectWidget(),  # Tool 필드에도 동일 위젯 명시(일관성)
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 기본적으로 툴 목록을 비움 (브랜드 선택 전까지)
        self.fields["tool"].queryset = Tool.objects.none()
        
        # 기본적으로 시리얼 번호 필드를 필수가 아니도록 변경 (clean에서 수동 검증)
        if "serial_number" in self.fields:
            self.fields["serial_number"].required = False

        # 1. 인스턴스가 있고(수정 모드), 툴이 이미 저장되어 있는 경우
        if self.instance.pk and self.instance.tool_id:
            try:
                brand = self.instance.tool.brand
                self.fields["brand"].initial = brand
                # 저장된 툴이 속한 브랜드의 툴 목록만 로드
                self.fields["tool"].queryset = Tool.objects.filter(brand=brand)
            except Tool.DoesNotExist:
                pass
        
        # 2. 폼 데이터(POST)가 있는 경우 (저장 실패 후 다시 렌더링 시 등)
        # 사용자가 브랜드를 선택하고 제출했을 때, 해당 브랜드의 툴 목록을 유지해야 함
        if "brand" in self.data:
            try:
                brand_id = int(self.data.get("brand"))
                self.fields["tool"].queryset = Tool.objects.filter(brand_id=brand_id)
            except (ValueError, TypeError):
                pass
        elif self.prefix:
             # Formset의 경우 prefix(예: tickets-0)가 있음
             # tickets-0-brand 식의 데이터를 찾아야 함
             brand_key = f"{self.prefix}-brand"
             if brand_key in self.data:
                 try:
                     brand_id = int(self.data.get(brand_key))
                     self.fields["tool"].queryset = Tool.objects.filter(brand_id=brand_id)
                 except (ValueError, TypeError):
                     pass
                         
    def clean(self):
        cleaned_data = super().clean()
        no_serial = cleaned_data.get("no_serial_number")
        serial = cleaned_data.get("serial_number")
        qty = cleaned_data.get("quantity") or 1

        if no_serial:
            # 시리얼 번호 에러 무시
            if "serial_number" in self._errors:
                del self._errors["serial_number"]
            cleaned_data["serial_number"] = "[NO-SN]"
            if not qty or qty < 1:
                self.add_error("quantity", "수량을 1 이상 입력해주세요.")
        else:
            if not serial:
                self.add_error("serial_number", "시리얼 번호를 입력하거나 '시리얼 없음'을 체크해주세요.")
        return cleaned_data

from .models import Part, CompanyCategory

class PartForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = [
            "brand",
            "part_type",
            "name",
            "code",
            "remarks",
            "tools",
        ]
        widgets = {
            "remarks": forms.TextInput(attrs={'class': 'vTextField', 'placeholder': '비고 입력 (선택)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.categories = list(CompanyCategory.objects.all().order_by('name'))
        for cat in self.categories:
            field_name = f'price_group_{cat.id}'
            if self.instance and self.instance.pk:
                pp = self.instance.group_prices.filter(category=cat).first()
                if pp:
                    self.initial[field_name] = pp.price

