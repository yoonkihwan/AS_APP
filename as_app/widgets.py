from django import forms
from django.utils.safestring import mark_safe


class PartsTableWidget(forms.CheckboxSelectMultiple):
    """
    부품/공임을 탭 분리 + 테이블 형태로 렌더링하는 커스텀 위젯.
    공임 탭이 먼저, 부품 탭이 두 번째로 표시됩니다.
    단가는 업체의 단가 그룹에 맞게 표시됩니다.
    """

    def __init__(self, parts_data=None, disabled_message=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # parts_data: {part_id: {name, code, price, part_type}}
        self.parts_data = parts_data or {}
        self.disabled_message = disabled_message

    def render(self, name, value, attrs=None, renderer=None):
        if self.disabled_message:
            return mark_safe(f'<div class="parts-table-widget" style="padding:16px; background:#fef2f2; border:1px solid #fca5a5; border-radius:6px; color:#ef4444; font-weight:600;">{self.disabled_message}</div>')
        
        if value is None:
            value = []
        value = [str(v) for v in value]

        # 공임/부품 분리
        labor_items = []
        part_items = []

        for option_value, option_label in self.choices:
            str_val = str(option_value)
            meta = self.parts_data.get(option_value, {})
            checked = str_val in value
            item = {
                "id": option_value,
                "name": meta.get("name", str(option_label)),
                "code": meta.get("code", ""),
                "price": meta.get("price", 0),
                "checked": checked,
            }
            if meta.get("part_type") == "labor":
                labor_items.append(item)
            else:
                part_items.append(item)

        html = self._build_html(name, labor_items, part_items)
        return mark_safe(html)

    def _build_html(self, name, labor_items, part_items):
        """공임과 부품을 단일 테이블에 섹션으로 나누어 표시"""
        html = '<div class="parts-table-widget">'
        html += '<table class="parts-select-table">'
        html += "<thead><tr>"
        html += '<th class="col-check">선택</th>'
        html += '<th class="col-name">공임/부품명</th>'
        html += '<th class="col-code">코드</th>'
        html += '<th class="col-price">단가</th>'
        html += "</tr></thead>"
        html += "<tbody>"

        # 공임 섹션
        html += '<tr class="section-separator"><td colspan="4">공임</td></tr>'
        if not labor_items:
            html += '<tr><td colspan="4" class="parts-table-empty"><span class="parts-table-empty-icon">📋</span>등록된 공임이 없습니다.</td></tr>'
        else:
            for item in labor_items:
                html += self._build_tr(name, item)

        # 부품 섹션
        html += '<tr class="section-separator"><td colspan="4">부품</td></tr>'
        if not part_items:
            html += '<tr><td colspan="4" class="parts-table-empty"><span class="parts-table-empty-icon">📋</span>등록된 부품이 없습니다.</td></tr>'
        else:
            for item in part_items:
                html += self._build_tr(name, item)

        html += "</tbody></table>"
        html += "</div>"
        return html

    def _build_tr(self, name, item):
        """개별 행 HTML 생성"""
        checked_attr = ' checked="checked"' if item["checked"] else ""
        checked_class = " selected-row" if item["checked"] else ""
        is_zero_price = item["price"] == 0
        price_formatted = f'{item["price"]:,}원' if item["price"] else "0원"
        code_display = item["code"] if item["code"] else "-"

        # 0원 단가 경고 스타일
        if is_zero_price:
            checked_class += " zero-price-row"
            price_formatted = '⚠️ 단가 미설정'

        html = f'<tr class="parts-row{checked_class}" data-part-id="{item["id"]}"'
        if is_zero_price:
            html += ' style="background-color:rgba(239,68,68,0.08);"'
        html += '>'
        html += (
            f'<td class="col-check">'
            f'<input type="checkbox" name="{name}" value="{item["id"]}"{checked_attr}>'
            f"</td>"
        )
        html += f'<td class="col-name">{item["name"]}</td>'
        html += f'<td class="col-code">{code_display}</td>'
        if is_zero_price:
            html += f'<td class="col-price" style="color:#ef4444; font-weight:600;">{price_formatted}</td>'
        else:
            html += f'<td class="col-price">{price_formatted}</td>'
        html += "</tr>"
        return html

    def value_from_datadict(self, data, files, name):
        """폼 제출 시 선택된 체크박스 값 추출 (Django 기본 동작 유지)"""
        getter = data.getlist if hasattr(data, "getlist") else lambda k: data.get(k, [])
        return getter(name)
