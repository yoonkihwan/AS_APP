from django.contrib import admin
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, path
from django.utils import timezone
from django.utils.html import format_html
from django import forms
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action as unfold_action, display
from unfold.contrib.filters.admin import RangeDateFilter


class NoRelatedButtonsMixin:
    """모든 FK/M2M 드롭다운 옆의 추가/수정/삭제/보기 버튼을 제거"""

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        for field in form.base_fields.values():
            widget = field.widget
            if hasattr(widget, "can_add_related"):
                widget.can_add_related = False
                widget.can_change_related = False
                widget.can_delete_related = False
                widget.can_view_related = False
        return form



class StatusColorMixin:
    """행 전체에 상태별 배경색을 적용하기 위해 HTML 마커를 삽입하는 믹스인"""
    
    @display(description="상태")
    def display_status(self, obj):
        if obj.status == "inbound":
            return obj.get_status_display()
            
        css_status = obj.status
        if obj.status == "shipped":
            css_status = "repaired"  # 출고는 초록색
        elif obj.status == "repaired":
            css_status = "shipped"   # 수리완료는 파란색
            
        return format_html(
            '<span class="status-marker" data-status="{}">{}</span>',
            css_status,
            obj.get_status_display(),
        )

class CustomTitleMixin:
    """브라우저 탭 및 화면의 메인 제목을 깔끔하게 표기하기 위한 믹스인"""
    custom_title = None

    def get_custom_title(self):
        return self.custom_title or self.model._meta.verbose_name_plural

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = self.get_custom_title()
        return super().changelist_view(request, extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = self.get_custom_title()
        return super().add_view(request, form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = self.get_custom_title()
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

from .models import (
    ASHistory,
    ASTicket,
    Brand,
    Company,
    CompanyCategory,
    EstimateTicket,
    InboundBatch,
    InboundTicket,
    OutboundTicket,
    OutsourceCompany,
    Part,
    RepairPreset,
    RepairTicket,
    TaxInvoiceTicket,
    Tool,
)
from .forms import ASTicketForm


# ──────────────────────────────────────────────
# 마스터 데이터 Admin
# ──────────────────────────────────────────────


@admin.register(CompanyCategory)
class CompanyCategoryAdmin(ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]

    def has_module_permission(self, request):
        """사이드바에 표시하지 않음 (Company Admin에서 통합 관리)"""
        return False


@admin.register(Company)
class CompanyAdmin(CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):
    custom_title = "업체관리"
    list_display = ["name", "region", "price_group"]
    list_filter = ["price_group", "region"]
    search_fields = ["name", "region"]
    list_per_page = 20
    change_list_template = "admin/as_app/company/change_list.html"

    fieldsets = (
        (
            "매출처 기본 정보",
            {
                "fields": (
                    "name",
                    "price_group",
                ),
            },
        ),
        (
            "지역 및 주소",
            {
                "fields": (
                    "region",
                    "address",
                ),
            },
        ),
    )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["active_tab"] = "company"
        return super().changelist_view(request, extra_context)


# ── 브랜드 + 툴 관리 ──

@admin.register(Brand)
class BrandAdmin(CustomTitleMixin, ModelAdmin):
    custom_title = "브랜드 관리"
    """브랜드 관리 - autocomplete 검색용 및 탭 연결"""
    list_display = ["name"]
    search_fields = ["name"]
    change_list_template = "admin/as_app/brand/change_list.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["active_tab"] = "brand"
        return super().changelist_view(request, extra_context)

    def has_module_permission(self, request):
        """사이드바에 표시하지 않음 (Tool Admin에서 통합 관리)"""
        return False


@admin.register(Tool)
class ToolAdmin(CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):
    custom_title = "장비/툴 관리"
    """장비/툴 관리 - 브랜드 & 툴 메인 탭 리스트"""
    list_display = ["brand", "model_name"]
    list_filter = ["brand"]
    search_fields = ["model_name", "brand__name"]
    autocomplete_fields = ["brand"]
    list_per_page = 20
    change_list_template = "admin/as_app/tool/change_list.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["active_tab"] = "tool"
        return super().changelist_view(request, extra_context)


@admin.register(Part)
class PartAdmin(CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):
    custom_title = "수리부품 관리"
    list_display = ["name", "code", "part_type", "display_tools", "price"]
    list_filter = ["part_type", "tools__brand"]
    search_fields = ["name", "code"]
    filter_horizontal = ["tools"]
    list_per_page = 20
    change_list_template = "admin/as_app/part/change_list.html"

    fieldsets = (
        (
            "수리부품 기본 정보",
            {
                "fields": (
                    "name",
                    "code",
                    "part_type",
                    "price",
                ),
            },
        ),
        (
            "적용 장비",
            {
                "fields": ("tools",),
                "description": "이 부품이 사용되는 장비를 선택하세요. 공용 부품은 여러 장비를 선택할 수 있습니다.",
            },
        ),
    )

    @admin.display(description="적용 장비")
    def display_tools(self, obj):
        return obj.tool_list()

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["preset_url"] = reverse("admin:as_app_repairpreset_changelist")
        extra_context["preset_add_url"] = reverse("admin:as_app_repairpreset_add")
        extra_context["preset_count"] = RepairPreset.objects.count()
        return super().changelist_view(request, extra_context)


@admin.register(RepairPreset)
class RepairPresetAdmin(NoRelatedButtonsMixin, ModelAdmin):
    """수리 세트 관리 - 자주 사용하는 부품 조합을 프리셋으로 관리"""
    list_display = ["name", "display_parts", "display_total_price", "display_tools"]
    search_fields = ["name"]
    filter_horizontal = ["parts", "tools"]
    list_per_page = 20

    fieldsets = (
        (
            "세트 기본 정보",
            {
                "fields": ("name",),
            },
        ),
        (
            "포함 부품/공임",
            {
                "fields": ("parts",),
                "description": "이 세트에 포함할 부품과 공임을 선택하세요.",
            },
        ),
        (
            "적용 장비",
            {
                "fields": ("tools",),
                "description": "이 세트가 표시될 장비를 선택하세요. 비워두면 모든 장비에 표시됩니다.",
            },
        ),
    )

    @admin.display(description="포함 부품")
    def display_parts(self, obj):
        parts = obj.parts.all()
        if parts:
            return ", ".join(p.name for p in parts[:4])
        return "-"

    @admin.display(description="합계 금액")
    def display_total_price(self, obj):
        return f"{obj.total_price:,}원"

    @admin.display(description="적용 장비")
    def display_tools(self, obj):
        tools = obj.tools.all()
        if tools:
            return ", ".join(str(t) for t in tools[:3])
        return "전체"

    def has_module_permission(self, request):
        """사이드바에 표시하지 않음 (PartAdmin에서 통합 관리)"""
        return False


# ──────────────────────────────────────────────
# 의뢰업체 Admin
# ──────────────────────────────────────────────

@admin.register(OutsourceCompany)
class OutsourceCompanyAdmin(ModelAdmin):
    """의뢰업체 관리"""
    list_display = ["name", "contact", "memo"]
    search_fields = ["name"]
    list_per_page = 20
    change_list_template = "admin/as_app/outsourcecompany/change_list.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["active_tab"] = "outsource"
        return super().changelist_view(request, extra_context)

    def has_module_permission(self, request):
        """사이드바에 표시하지 않음 (업체관리 탭에서 통합 관리)"""
        return False


# ──────────────────────────────────────────────
# AS 프로세스 Admin
# ──────────────────────────────────────────────


# ── 일괄 입고 등록 ──




class ASTicketInline(NoRelatedButtonsMixin, TabularInline):
    """입고 배치 안에서 개별 품목을 행으로 추가"""
    model = ASTicket
    fk_name = "inbound_batch"
    form = ASTicketForm  # 커스텀 폼 적용
    fields = ["brand", "tool", "serial_number"]  # form에 정의된 순서대로 표시
    # autocomplete_fields = ["tool"]  # JS Cascading을 위해 일반 Select로 변경 (주석 처리)
    extra = 0
    min_num = 1

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        for field in formset.form.base_fields.values():
            if hasattr(field, 'widget'):
                field.widget.can_add_related = False
                field.widget.can_change_related = False
                field.widget.can_delete_related = False
                field.widget.can_view_related = False
                # 브라우저 자동완성 비활성화
                if hasattr(field.widget, 'attrs'):
                    field.widget.attrs['autocomplete'] = 'off'
        # 시리얼번호 안내문을 컬럼 헤더에 직접 표시
        if 'serial_number' in formset.form.base_fields:
            formset.form.base_fields['serial_number'].label = "시리얼 번호 (쉼표로 구분 시 다건 등록)"
        return formset

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("tool", "tool__brand")


@admin.register(InboundBatch)
class InboundBatchAdmin(CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):
    custom_title = "입고 등록"
    """일괄 입고 등록 - 공통 정보 1번 입력 + 품목별 행 추가"""

    list_display = [
        "inbound_date",
        "company",
        "manager",
        "display_ticket_count",
        "display_tools_summary",
        "created_at",
    ]
    list_filter = ["inbound_date", "company"]
    search_fields = ["company__name", "manager", "memo"]
    autocomplete_fields = ["company"]
    date_hierarchy = "inbound_date"
    list_per_page = 20
    inlines = [ASTicketInline]

    class Media:
        css = {"all": ("as_app/css/inline_fix.css", "as_app/css/hide_fab.css")}
        js = ("as_app/js/inbound_form.js",)

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        """저장 부가 버튼 제거"""
        context["show_save_and_add_another"] = False
        context["show_save_and_continue"] = False
        return super().render_change_form(request, context, add, change, form_url, obj)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # 담당자/부서 라벨에 안내문 포함
        if 'manager' in form.base_fields:
            form.base_fields['manager'].label = "담당자/부서 (필수 아님 · 내부 구분용)"
        # 브라우저 자동완성 비활성화
        for field in form.base_fields.values():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs['autocomplete'] = 'off'
        return form

    fieldsets = (
        (
            "입고 공통 정보",
            {
                "fields": (
                    "inbound_date",
                    "company",
                    "manager",
                ),
                "description": "아래 추가하는 모든 품목에 이 정보가 자동 적용됩니다.",
            },
        ),
    )

    @admin.display(description="품목 수")
    def display_ticket_count(self, obj):
        count = obj.tickets.count()
        return "%d건" % count

    @admin.display(description="입고 장비")
    def display_tools_summary(self, obj):
        tools = obj.tickets.select_related("tool", "tool__brand").values_list(
            "tool__brand__name", "tool__model_name"
        ).distinct()
        if tools:
            items = ["%s > %s" % (b, m) for b, m in tools[:3]]
            suffix = " 외 %d건" % (tools.count() - 3) if tools.count() > 3 else ""
            return ", ".join(items) + suffix
        return "-"

    def response_add(self, request, obj, post_url_continue=None):
        """저장 후 목록 대신 새 입고 등록 폼으로 리다이렉트"""
        if getattr(request, "_formset_validation_failed", False):
            # 검증 실패: 빈 배치 삭제 후 에러 메시지만 표시
            if obj.pk and obj.tickets.count() == 0:
                obj.delete()
            return HttpResponseRedirect(
                reverse("admin:as_app_inboundbatch_add")
            )
        from django.contrib import messages
        messages.success(request, "입고 등록이 완료되었습니다. (%s)" % obj)
        return HttpResponseRedirect(
            reverse("admin:as_app_inboundbatch_add")
        )

    def response_change(self, request, obj):
        """수정 저장 후에도 새 입고 등록 폼으로 리다이렉트"""
        if getattr(request, "_formset_validation_failed", False):
            return HttpResponseRedirect(
                reverse("admin:as_app_inboundbatch_add")
            )
        from django.contrib import messages
        messages.success(request, "입고 정보가 수정되었습니다. (%s)" % obj)
        return HttpResponseRedirect(
            reverse("admin:as_app_inboundbatch_add")
        )

    def changelist_view(self, request, extra_context=None):
        """목록 화면 접근 시 새 입고 등록 폼으로 리다이렉트"""
        return HttpResponseRedirect(
            reverse("admin:as_app_inboundbatch_add")
        )

    def _fail_formset_validation(self, request, form, error_message):
        """검증 실패 시: 에러 메시지 + 플래그 설정 (배치 삭제는 response_add에서 처리)"""
        from django.contrib import messages
        messages.error(request, error_message)
        request._formset_validation_failed = True

    def save_formset(self, request, form, formset, change):
        """인라인 저장 시 배치의 공통 정보를 각 티켓에 자동 복사 + 쉼표 시리얼 분리 + 중복 검증"""
        instances = formset.save(commit=False)

        for obj in formset.deleted_objects:
            obj.delete()

        batch = form.instance

        # ── 쉼표로 구분된 시리얼번호를 개별 티켓으로 확장 ──
        expanded = []
        for instance in instances:
            if instance.tool_id and instance.serial_number:
                serials = [s.strip() for s in instance.serial_number.split(",") if s.strip()]
                if len(serials) > 1:
                    # 첫 번째는 원래 인스턴스에 할당
                    instance.serial_number = serials[0]
                    expanded.append(instance)
                    # 나머지는 새 티켓으로 생성
                    for sn in serials[1:]:
                        new_ticket = ASTicket(
                            inbound_batch=batch,
                            tool=instance.tool,
                            serial_number=sn,
                        )
                        expanded.append(new_ticket)
                else:
                    expanded.append(instance)
            elif instance.tool_id:
                expanded.append(instance)

        # ── 중복 검증 ──
        # 1) 같은 배치 내 중복 체크 (tool + serial_number)
        seen = set()
        duplicates_in_batch = []
        for instance in expanded:
            if instance.tool_id and instance.serial_number:
                key = (instance.tool_id, instance.serial_number.strip())
                if key in seen:
                    duplicates_in_batch.append(
                        "%s (S/N: %s)" % (instance.tool, instance.serial_number)
                    )
                seen.add(key)

        if duplicates_in_batch:
            self._fail_formset_validation(
                request, form,
                "같은 배치 내에 중복된 품목이 있습니다: %s" % ", ".join(duplicates_in_batch)
            )
            return

        # 2) 기존 활성 티켓과 중복 체크
        active_statuses = [
            ASTicket.Status.INBOUND,
            ASTicket.Status.REPAIRED,
        ]
        conflicts = []
        for instance in expanded:
            if instance.tool_id and instance.serial_number:
                qs = ASTicket.objects.filter(
                    tool=instance.tool,
                    serial_number=instance.serial_number.strip(),
                    status__in=active_statuses,
                )
                if instance.pk:
                    qs = qs.exclude(pk=instance.pk)
                if qs.exists():
                    conflicts.append(
                        "%s (S/N: %s)" % (instance.tool, instance.serial_number)
                    )

        if conflicts:
            self._fail_formset_validation(
                request, form,
                "이미 입고/수리 중인 장비가 있어 저장할 수 없습니다: %s" % ", ".join(conflicts)
            )
            return

        # ── 검증 통과 → 저장 ──
        saved_count = 0
        for instance in expanded:
            instance.inbound_date = batch.inbound_date
            instance.company = batch.company
            instance.manager = batch.manager
            instance.status = ASTicket.Status.INBOUND
            instance.save()
            saved_count += 1

        formset.save_m2m()

        # 쉼표 분리로 추가 생성된 경우 안내 메시지
        original_count = len(instances)
        if saved_count > original_count:
            from django.contrib import messages
            messages.info(
                request,
                "시리얼번호 분리로 총 %d건의 티켓이 등록되었습니다. (입력 %d행 → %d건)"
                % (saved_count, original_count, saved_count)
            )


@admin.register(InboundTicket)
class InboundTicketAdmin(StatusColorMixin, ModelAdmin):
    """개별 입고 티켓 관리 (사이드바 숨김)"""

    list_display = [
        "inbound_date",
        "company",
        "tool",
        "serial_number",
        "display_status",
    ]
    list_filter = ["status", "inbound_date", "company"]
    search_fields = ["serial_number", "company__name", "tool__model_name"]

    def has_module_permission(self, request):
        return False

    class Media:
        css = {"all": ("as_app/css/row_colors.css",)}

@admin.register(RepairTicket)
class RepairTicketAdmin(StatusColorMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):
    custom_title = "수리 기록 등록"
    """수리 기록 - 목록에서 버튼 클릭으로 수리 등록 페이지 이동"""

    # ── 목록 화면 설정 ──
    list_display = [
        "display_status",
        "inbound_date",
        "company",
        "tool",
        "serial_number",
        "display_repair_button",
    ]
    list_display_links = None  # 행 클릭 비활성화 (버튼으로만 이동)
    search_fields = ["serial_number", "company__name", "tool__model_name"]
    list_per_page = 30
    actions = None  # 체크박스 + 액션 드롭다운 제거 (상태는 자동 관리)

    class Media:
        css = {"all": ("as_app/css/inline_fix.css", "as_app/css/hide_fab.css", "as_app/css/row_colors.css")}

    # ── 수리 등록 폼 설정 ──
    fieldsets = (
        (
            "입고 정보",
            {
                "fields": (
                    "inbound_date",
                    "company",
                    "tool",
                    "serial_number",
                ),
            },
        ),
        (
            "수리 부품 선택",
            {
                "fields": (
                    "used_parts",
                    "repair_content",
                ),
                "description": "해당 장비에 적용 가능한 부품/공임이 표시됩니다. 체크하고 저장하면 AS 비용이 자동 계산되며 수리완료 처리됩니다.",
            },
        ),
    )

    readonly_fields = [
        "inbound_date",
        "company",
        "tool",
        "serial_number",
    ]

    @admin.display(description="수리 기록")
    def display_repair_button(self, obj):
        """목록에서 수리 기록 등록 버튼을 표시"""
        url = reverse("admin:as_app_repairticket_change", args=[obj.pk])
        return format_html(
            '<a href="{}" style="'
            'display:inline-flex; align-items:center; gap:6px; '
            'padding:6px 14px; border-radius:6px; font-size:0.8rem; '
            'font-weight:600; text-decoration:none; '
            'background:#6366f1; color:#fff; '
            'transition:all .15s ease;'
            '" '
            'onmouseover="this.style.background=\'#4f46e5\'" '
            'onmouseout="this.style.background=\'#6366f1\'">'
            '🔧 수리 기록 등록</a>',
            url
        )

    def get_form(self, request, obj=None, **kwargs):
        """수리 편집 폼: 해당 장비 부품만 필터링 + 체크박스 위젯 + 비고 한 줄"""
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.tool_id:
            from django.db.models import Q
            form.base_fields["used_parts"].queryset = Part.objects.filter(
                Q(tools=obj.tool) | Q(tools__isnull=True) | Q(part_type=Part.PartType.LABOR)
            ).distinct().order_by("part_type", "name")
        # 부품 선택을 체크박스 위젯으로 변경 (빠르고 직관적)
        if "used_parts" in form.base_fields:
            form.base_fields["used_parts"].widget = forms.CheckboxSelectMultiple()
            form.base_fields["used_parts"].help_text = "사용한 부품/공임을 체크하세요. 저장 시 자동으로 비용이 계산되고 수리완료 처리됩니다."
        # 비고 필드를 한 줄 입력으로 축소
        if "repair_content" in form.base_fields:
            form.base_fields["repair_content"].widget = forms.TextInput(
                attrs={"placeholder": "추가 메모가 있으면 입력하세요 (선택사항)", "style": "width:100%"}
            )
        return form

    def get_queryset(self, request):
        """입고/수리대기/수리의뢰 상태인 티켓만 표시 (수리 전 단계)"""
        return (
            super()
            .get_queryset(request)
            .filter(
                status__in=[
                    ASTicket.Status.INBOUND,
                ]
            )
            .select_related("company", "tool", "tool__brand")
            .prefetch_related("used_parts")
        )

    # ── 권한 제어 ──
    def has_add_permission(self, request):
        """수리 기록은 신규 추가가 아닌 기존 입고 티켓에서 편집"""
        return False

    def has_delete_permission(self, request, obj=None):
        """삭제 버튼 제거 — 입고 데이터 보호 (Safety First)"""
        return False

    # ── 저장 로직 ──
    def save_related(self, request, form, formsets, change):
        """M2M 저장 후 사용 부품/공임 단가 합산으로 AS 비용 자동 계산 + 수리완료 상태 변경"""
        super().save_related(request, form, formsets, change)
        obj = form.instance
        total_parts = sum(part.price for part in obj.used_parts.all())
        total_with_vat = int(total_parts * 1.1)  # 부품비용에 부가세 10% 포함
        update_fields = []
        if obj.repair_cost != total_with_vat:
            obj.repair_cost = total_with_vat
            update_fields.append("repair_cost")
        # 부품이 선택되어 있으면 자동으로 수리완료 상태로 변경
        if obj.used_parts.exists() and obj.status != ASTicket.Status.REPAIRED:
            obj.status = ASTicket.Status.REPAIRED
            update_fields.append("status")
        if update_fields:
            obj.save(update_fields=update_fields)

    # ── 화면 커스터마이징 ──
    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context["show_save_and_add_another"] = False
        context["show_save_and_continue"] = False
        # 프리셋 데이터를 context에 추가
        if obj and obj.tool_id:
            from django.db.models import Q
            presets = RepairPreset.objects.filter(
                Q(tools=obj.tool) | Q(tools__isnull=True)
            ).distinct().prefetch_related("parts")
            preset_data = []
            for preset in presets:
                preset_data.append({
                    "id": preset.id,
                    "name": preset.name,
                    "part_ids": list(preset.parts.values_list("id", flat=True)),
                    "total_price": preset.total_price,
                })
            context["repair_presets"] = preset_data
        else:
            context["repair_presets"] = []
        return super().render_change_form(request, context, add, change, form_url, obj)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """히스토리 버튼 제거"""
        extra_context = extra_context or {}
        extra_context["show_history"] = False
        return super().change_view(request, object_id, form_url, extra_context)

    def response_change(self, request, obj):
        from django.contrib import messages
        messages.success(request, "수리 정보가 저장되었습니다. (%s)" % obj)
        return HttpResponseRedirect(
            reverse("admin:as_app_repairticket_changelist")
        )

    def get_urls(self):
        """부품 목록 API 엔드포인트 추가"""
        custom_urls = [
            path(
                "api/parts-for-tool/<int:tool_id>/",
                self.admin_site.admin_view(self.api_parts_for_tool),
                name="api_parts_for_tool",
            ),
        ]
        return custom_urls + super().get_urls()

    def api_parts_for_tool(self, request, tool_id):
        """특정 장비에 적용 가능한 부품 목록을 JSON으로 반환"""
        from django.db.models import Q
        parts = Part.objects.filter(
            Q(tools__id=tool_id) | Q(tools__isnull=True) | Q(part_type=Part.PartType.LABOR)
        ).distinct().values("id", "name", "code", "price", "part_type")
        return JsonResponse({"parts": list(parts)})


@admin.register(OutboundTicket)
class OutboundTicketAdmin(StatusColorMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):
    custom_title = "출고 등록"
    """출고 등록 - 수리완료 목록에서 선택하여 출고 처리"""

    list_display = [
        "display_status",
        "inbound_date",
        "company",
        "tool",
        "serial_number",
        "display_used_parts",
        "repair_cost",
    ]
    list_display_links = None  # 행 클릭 시 상세 페이지 이동 안 함 (체크만)
    list_filter = ["company", "tool__brand"]
    search_fields = ["serial_number", "company__name", "tool__model_name", "tool__brand__name"]
    list_per_page = 30
    actions = ["mark_as_shipped_today", "mark_as_shipped_with_date"]
    ordering = ["-inbound_date", "-created_at"]

    class Media:
        css = {"all": ("as_app/css/hide_fab.css", "as_app/css/row_colors.css", "as_app/css/text_truncate.css")}
        js = ("as_app/js/outbound_row_click.js",)

    @admin.display(description="사용 부품")
    def display_used_parts(self, obj):
        parts = obj.used_parts.all()
        if parts:
            full_text = ", ".join(p.name for p in parts)
            return format_html(
                '<span class="truncate-text" title="{}">{}</span>',
                full_text,
                full_text
            )
        return "-"

    def get_queryset(self, request):
        """수리완료 상태인 티켓만 표시"""
        return (
            super()
            .get_queryset(request)
            .filter(status=ASTicket.Status.REPAIRED)
            .select_related("company", "tool", "tool__brand")
            .prefetch_related("used_parts")
        )

    def has_add_permission(self, request):
        """출고는 '신규 추가'가 아니라 기존 티켓의 상태 변경"""
        return False

    def has_change_permission(self, request, obj=None):
        """목록 전용 (개별 편집 불필요)"""
        if obj is None:
            return True  # changelist 접근 허용
        return False

    @unfold_action(description="✅ 선택 항목 출고 처리 (오늘 날짜)")
    def mark_as_shipped_today(self, request, queryset):
        today = timezone.now().date()
        updated = queryset.update(
            status=ASTicket.Status.SHIPPED,
            outbound_date=today,
        )
        from django.contrib import messages
        messages.success(
            request,
            "%d건이 출고 처리되었습니다. (출고일: %s)" % (updated, today.strftime("%Y-%m-%d"))
        )

    @unfold_action(description="📅 선택 항목 출고 처리 (날짜 선택)")
    def mark_as_shipped_with_date(self, request, queryset):
        """날짜 선택 중간 페이지를 통해 출고 처리"""
        from django.template.response import TemplateResponse
        import datetime

        # 중간 페이지에서 날짜를 선택하고 확인 버튼을 눌렀을 때
        if request.POST.get("confirm") == "yes":
            date_str = request.POST.get("outbound_date", "")
            try:
                outbound_date = datetime.date.fromisoformat(date_str)
            except (ValueError, TypeError):
                from django.contrib import messages
                messages.error(request, "올바른 날짜 형식이 아닙니다.")
                return None

            updated = queryset.update(
                status=ASTicket.Status.SHIPPED,
                outbound_date=outbound_date,
            )
            from django.contrib import messages
            messages.success(
                request,
                "%d건이 출고 처리되었습니다. (출고일: %s)" % (updated, outbound_date.strftime("%Y-%m-%d"))
            )
            return None

        # 중간 페이지 표시 (날짜 선택 폼)
        context = {
            **self.admin_site.each_context(request),
            "title": "출고 날짜 선택",
            "ticket_count": queryset.count(),
            "selected_pks": list(queryset.values_list("pk", flat=True)),
            "today": timezone.now().date().isoformat(),
            "opts": self.model._meta,
        }
        return TemplateResponse(
            request,
            "admin/as_app/outbound_date_select.html",
            context,
        )


@admin.register(ASHistory)
class ASHistoryAdmin(StatusColorMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):
    custom_title = "통합 이력"
    """AS 통합 이력 조회 (Read-Only)"""

    list_display = [
        "display_status",
        "inbound_date",
        "outbound_date",
        "company",
        "tool",
        "serial_number",
        "used_parts_summary",
        "repair_cost",
        "estimate_status",
        "tax_invoice",
    ]
    list_filter = [
        "status",
        "company",
        "tool__brand",
        ("inbound_date", RangeDateFilter),
        ("outbound_date", RangeDateFilter),
    ]
    search_fields = [
        "serial_number",
        "company__name",
        "tool__model_name",
        "tool__brand__name",
        "symptom",
        "repair_content",
    ]
    list_per_page = 30

    fieldsets = (
        (
            "입고 정보",
            {
                "fields": (
                    "inbound_date",
                    "company",
                    "manager",
                    "tool",
                    "serial_number",
                    "symptom",
                ),
            },
        ),
        (
            "수리 정보",
            {
                "fields": (
                    "repair_content",
                    "used_parts",
                    "repair_cost",
                    "status",
                ),
            },
        ),
        (
            "출고 및 정산",
            {
                "fields": (
                    "outbound_date",
                    "estimate_status",
                    "tax_invoice",
                ),
            },
        ),
    )

    class Media:
        css = {
            "all": (
                "as_app/css/hide_fab.css",
                "as_app/css/row_colors.css",
                "as_app/css/text_truncate.css",
            )
        }

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="사용 부품")
    def used_parts_summary(self, obj):
        parts = obj.used_parts.all()
        if parts:
            full_text = ", ".join(p.name for p in parts)
            return format_html(
                '<span class="truncate-text" title="{}">{}</span>',
                full_text,
                full_text
            )
        return "-"


@admin.register(EstimateTicket)
class EstimateTicketAdmin(StatusColorMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):
    custom_title = "견적서 발행"
    """견적서 발행 기능 (데모 버전)"""

    list_display = [
        "display_status",
        "inbound_date",
        "outbound_date",
        "company",
        "tool",
        "serial_number",
        "repair_cost",
    ]
    list_filter = [
        "status",
        "company",
        "tool__brand",
        ("inbound_date", RangeDateFilter),
        ("outbound_date", RangeDateFilter),
    ]
    search_fields = [
        "serial_number",
        "company__name",
        "tool__model_name",
        "tool__brand__name",
        "symptom",
        "repair_content",
    ]
    list_per_page = 30
    actions = ["export_estimate"]

    class Media:
        css = {"all": ("as_app/css/hide_fab.css", "as_app/css/row_colors.css")}

    def get_queryset(self, request):
        """견적서 발행은 수리완료 또는 출고 상태인 데이터만 표시"""
        return super().get_queryset(request).filter(
            status__in=[ASTicket.Status.REPAIRED, ASTicket.Status.SHIPPED]
        )

    @unfold_action(description="📄 선택 항목 견적서 출력 (PDF 다운로드)")
    def export_estimate(self, request, queryset):
        from .utils.pdf_export import generate_pdf_estimate
        from django.http import FileResponse
        
        try:
            buffer = generate_pdf_estimate(queryset)
            
            # 견적서 추출 상태 업데이트
            queryset.update(estimate_status=True)
            
            response = FileResponse(
                buffer, 
                as_attachment=True, 
                filename="estimate_demo.pdf",
                content_type="application/pdf"
            )
            return response
            
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f"견적서 추출 중 오류가 발생했습니다: {str(e)}")
            return None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TaxInvoiceTicket)
class TaxInvoiceTicketAdmin(StatusColorMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):
    custom_title = "세금계산서 등록"
    
    list_display = [
        "display_status",
        "inbound_date",
        "outbound_date",
        "company",
        "tool",
        "serial_number",
        "repair_cost",
        "tax_invoice",
    ]
    list_editable = ["tax_invoice"]
    list_filter = [
        "status",
        "company",
        "tool__brand",
        ("inbound_date", RangeDateFilter),
        ("outbound_date", RangeDateFilter),
        "tax_invoice",
    ]
    search_fields = [
        "serial_number",
        "company__name",
        "tool__model_name",
        "tool__brand__name",
        "symptom",
        "repair_content",
    ]
    list_per_page = 30

    class Media:
        css = {"all": ("as_app/css/hide_fab.css", "as_app/css/row_colors.css")}

    def get_queryset(self, request):
        """출고 상태인 데이터만 표시"""
        return super().get_queryset(request).filter(
            status=ASTicket.Status.SHIPPED
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj:
            fields = [f.name for f in self.model._meta.fields]
            if 'tax_invoice' in fields:
                fields.remove('tax_invoice')
            return fields
        return []
