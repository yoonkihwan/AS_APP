from django import forms
from django.utils.safestring import mark_safe


class PartsTableWidget(forms.CheckboxSelectMultiple):
    """
    부품/공임을 탭 분리 + 테이블 형태로 렌더링하는 커스텀 위젯.
    공임 탭이 먼저, 부품 탭이 두 번째로 표시됩니다.
    단가는 업체의 단가 그룹에 맞게 표시됩니다.
    """

    def __init__(self, parts_data=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # parts_data: {part_id: {name, code, price, part_type}}
        self.parts_data = parts_data or {}

    def render(self, name, value, attrs=None, renderer=None):
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
        """공임 탭(먼저) + 부품 탭 = 테이블 형태 HTML 생성"""

        labor_count = len(labor_items)
        part_count = len(part_items)

        # 탭 헤더
        html = '<div class="parts-table-widget">'
        html += '<div class="parts-tabs">'
        html += (
            '<button type="button" class="parts-tab active" data-tab="labor">'
            f'💰 공임 <span class="parts-tab-count">{labor_count}</span>'
            "</button>"
        )
        html += (
            '<button type="button" class="parts-tab" data-tab="part">'
            f'🔧 부품 <span class="parts-tab-count">{part_count}</span>'
            "</button>"
        )
        html += "</div>"

        # 공임 테이블 (기본 활성)
        html += '<div class="parts-tab-content active" data-tab-content="labor">'
        html += self._build_table(name, labor_items, is_labor=True)
        html += "</div>"

        # 부품 테이블
        html += '<div class="parts-tab-content" data-tab-content="part">'
        html += self._build_table(name, part_items, is_labor=False)
        html += "</div>"

        html += "</div>"
        return html

    def _build_table(self, name, items, is_labor=False):
        """개별 테이블 HTML 생성"""
        type_label = "공임명" if is_labor else "품명"

        if not items:
            empty_text = "등록된 공임이 없습니다." if is_labor else "등록된 부품이 없습니다."
            return (
                '<div class="parts-table-empty">'
                f'<span class="parts-table-empty-icon">📋</span>'
                f"{empty_text}"
                "</div>"
            )

        html = '<table class="parts-select-table">'
        html += "<thead><tr>"
        html += '<th class="col-check">선택</th>'
        html += f'<th class="col-name">{type_label}</th>'
        html += '<th class="col-code">코드</th>'
        html += '<th class="col-price">단가</th>'
        html += "</tr></thead>"
        html += "<tbody>"

        for item in items:
            checked_attr = ' checked="checked"' if item["checked"] else ""
            checked_class = " selected-row" if item["checked"] else ""
            price_formatted = f'{item["price"]:,}원' if item["price"] else "0원"
            code_display = item["code"] if item["code"] else "-"

            html += f'<tr class="parts-row{checked_class}" data-part-id="{item["id"]}">'
            html += (
                f'<td class="col-check">'
                f'<input type="checkbox" name="{name}" value="{item["id"]}"{checked_attr}>'
                f"</td>"
            )
            html += f'<td class="col-name">{item["name"]}</td>'
            html += f'<td class="col-code">{code_display}</td>'
            html += f'<td class="col-price">{price_formatted}</td>'
            html += "</tr>"

        html += "</tbody></table>"
        return html

    def value_from_datadict(self, data, files, name):
        """폼 제출 시 선택된 체크박스 값 추출 (Django 기본 동작 유지)"""
        getter = data.getlist if hasattr(data, "getlist") else lambda k: data.get(k, [])
        return getter(name)
