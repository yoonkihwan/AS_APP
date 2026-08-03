"""
AS 관리 다중 선택 필터 시스템 (Multi-Select Filter Bar)

기존 Django Admin의 단일 클릭 사이드바 필터를 대체하여,
상태/매출처/브랜드/날짜를 다중 선택 드롭다운 + [적용] 버튼으로 한 번에 필터링합니다.
"""

from django.contrib.admin import SimpleListFilter
from django.contrib.admin.views.main import ChangeList


class MultiSelectChangeList(ChangeList):
    """Ignore custom `mf_*` params inside Django admin's built-in filter pipeline."""

    def get_filters_params(self, params=None):
        lookup_params = super().get_filters_params(params)
        for key in list(lookup_params.keys()):
            if self.model_admin._is_allowed_multi_filter_lookup(key):
                del lookup_params[key]
        return lookup_params


class MultiSelectFilterMixin:
    """
    다중 선택 필터 바를 Admin changelist에 통합하는 Mixin.

    사용 방법:
        1. Admin 클래스에 이 Mixin을 상속에 추가
        2. `multi_select_filters` 속성을 정의 (필터 구성)
        3. 기존 `list_filter`는 빈 리스트로 설정 (사이드바 필터 비활성화)

    예시:
        class MyAdmin(MultiSelectFilterMixin, ModelAdmin):
            multi_select_filters = [
                {"key": "status", "label": "상태", "type": "choices", "field": "status"},
                {"key": "company", "label": "매출처", "type": "fk", "field": "company", "model": Company},
                {"key": "brand", "label": "브랜드", "type": "fk", "field": "tool__brand", "model": Brand},
                {"key": "inbound_date", "label": "입고일", "type": "date_range"},
                {"key": "outbound_date", "label": "출고일", "type": "date_range"},
            ]
    """
    multi_select_filters = []

    def _is_allowed_multi_filter_lookup(self, lookup):
        """Return True when the query param belongs to this mixin's custom filter set."""
        if not lookup.startswith("mf_"):
            return False

        key = lookup[3:]
        if key.endswith("_from"):
            key = key[:-5]
        elif key.endswith("_to"):
            key = key[:-3]

        return any(f_conf.get("key") == key for f_conf in self.multi_select_filters)

    def lookup_allowed(self, lookup, value, request=None):
        """
        Allow custom filter query params to pass Django admin changelist validation.

        Without this, the admin redirects to `?e=1` and drops the active filters.
        """
        if self._is_allowed_multi_filter_lookup(lookup):
            return True
        return super().lookup_allowed(lookup, value, request)

    def get_changelist(self, request, **kwargs):
        return MultiSelectChangeList

    def get_multi_select_filter_context(self, request):
        """
        필터 바에 필요한 context 데이터를 구성합니다.
        각 필터의 옵션 목록과 현재 선택된 값을 반환합니다.
        """
        from .models import ASTicket
        filters_context = []

        for f_conf in self.multi_select_filters:
            f_type = f_conf.get("type")
            key = f_conf.get("key")
            label = f_conf.get("label", key)

            if f_type == "choices":
                # status 같은 TextChoices/IntegerChoices 필드
                field_name = f_conf.get("field", key)
                # 모델의 choices 가져오기
                model_field = self.model._meta.get_field(field_name)
                choices = list(model_field.choices) if model_field.choices else []
                selected = request.GET.getlist(f"mf_{key}")
                filters_context.append({
                    "key": key,
                    "label": label,
                    "type": "choices",
                    "options": [{"value": v, "label": l, "selected": v in selected} for v, l in choices],
                    "selected_values": selected,
                })

            elif f_type == "fk":
                # ForeignKey 필드 (Company, Brand 등)
                model_cls = f_conf.get("model")
                if model_cls:
                    # distinct한 값만 가져오기 (실제 데이터가 있는 것만)
                    options = model_cls.objects.all().order_by("name")
                    selected = request.GET.getlist(f"mf_{key}")
                    filters_context.append({
                        "key": key,
                        "label": label,
                        "type": "fk",
                        "searchable": f_conf.get("searchable", False),
                        "options": [{"value": str(o.pk), "label": str(o.name), "selected": str(o.pk) in selected} for o in options],
                        "selected_values": selected,
                    })

            elif f_type == "date_range":
                # 날짜 범위 필터
                date_from = request.GET.get(f"mf_{key}_from", "")
                date_to = request.GET.get(f"mf_{key}_to", "")
                filters_context.append({
                    "key": key,
                    "label": label,
                    "type": "date_range",
                    "date_from": date_from,
                    "date_to": date_to,
                })

            elif f_type == "boolean":
                # Boolean 필드 (세금계산서 발행 여부 등)
                selected = request.GET.getlist(f"mf_{key}")
                filters_context.append({
                    "key": key,
                    "label": label,
                    "type": "boolean",
                    "options": [
                        {"value": "true", "label": "✓ 발행", "selected": "true" in selected},
                        {"value": "false", "label": "✗ 미발행", "selected": "false" in selected},
                    ],
                    "selected_values": selected,
                })

        return filters_context

    def get_active_filter_pills(self, request, filters_context):
        """
        현재 적용 중인 필터를 Pill(태그) 형태로 표시하기 위한 데이터를 구성합니다.
        """
        pills = []
        for fc in filters_context:
            if fc["type"] in ("choices", "fk"):
                for opt in fc["options"]:
                    if opt["selected"]:
                        pills.append({
                            "key": fc["key"],
                            "value": opt["value"],
                            "label": f'{fc["label"]}: {opt["label"]}',
                        })
            elif fc["type"] == "date_range":
                if fc.get("date_from") or fc.get("date_to"):
                    date_label_parts = []
                    if fc.get("date_from"):
                        date_label_parts.append(fc["date_from"])
                    else:
                        date_label_parts.append("~")
                    date_label_parts.append("~")
                    if fc.get("date_to"):
                        date_label_parts.append(fc["date_to"])
                    else:
                        date_label_parts.append("~")
                    pills.append({
                        "key": fc["key"],
                        "value": "__date_range__",
                        "label": f'{fc["label"]}: {" ".join(date_label_parts)}',
                    })
            elif fc["type"] == "boolean":
                for opt in fc["options"]:
                    if opt["selected"]:
                        pills.append({
                            "key": fc["key"],
                            "value": opt["value"],
                            "label": f'{fc["label"]}: {opt["label"]}',
                        })
        return pills

    def apply_multi_select_filters(self, request, queryset):
        """
        GET 파라미터에서 다중 선택 필터를 읽어 queryset에 적용합니다.
        """
        for f_conf in self.multi_select_filters:
            key = f_conf.get("key")
            f_type = f_conf.get("type")
            field_name = f_conf.get("field", key)

            if f_type in ("choices", "fk"):
                values = request.GET.getlist(f"mf_{key}")
                if values:
                    queryset = queryset.filter(**{f"{field_name}__in": values})

            elif f_type == "date_range":
                date_from = request.GET.get(f"mf_{key}_from", "")
                date_to = request.GET.get(f"mf_{key}_to", "")
                if date_from:
                    queryset = queryset.filter(**{f"{field_name}__gte": date_from})
                if date_to:
                    queryset = queryset.filter(**{f"{field_name}__lte": date_to})

            elif f_type == "boolean":
                values = request.GET.getlist(f"mf_{key}")
                if values:
                    bool_values = [v == "true" for v in values]
                    queryset = queryset.filter(**{f"{field_name}__in": bool_values})

        return queryset

    def get_queryset(self, request):
        """기본 queryset에 다중 선택 필터를 적용합니다."""
        qs = super().get_queryset(request)
        return self.apply_multi_select_filters(request, qs)

    def changelist_view(self, request, extra_context=None):
        """changelist 뷰에 필터 바 context를 추가합니다."""
        extra_context = extra_context or {}
        filters_context = self.get_multi_select_filter_context(request)
        pills = self.get_active_filter_pills(request, filters_context)

        # 현재 필터 상태를 확인 (활성 여부)
        has_active_filters = any(
            (fc.get("selected_values") and len(fc["selected_values"]) > 0)
            or fc.get("date_from")
            or fc.get("date_to")
            for fc in filters_context
        )

        # 검색어 보존
        search_query = request.GET.get("q", "")

        extra_context.update({
            "multi_filters": filters_context,
            "filter_pills": pills,
            "has_active_filters": has_active_filters,
            "search_query_preserved": search_query,
        })
        return super().changelist_view(request, extra_context=extra_context)
