from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action as unfold_action


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

from .models import (
    ASHistory,
    ASTicket,
    Brand,
    Company,
    CompanyCategory,
    InboundBatch,
    InboundTicket,
    OutboundTicket,
    OutsourceCompany,
    Part,
    RepairTicket,
    Tool,
)


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
class CompanyAdmin(NoRelatedButtonsMixin, ModelAdmin):
    list_display = ["name", "region", "company_type", "price_group"]
    list_filter = ["company_type", "price_group", "region"]
    search_fields = ["name", "region"]
    list_per_page = 20

    fieldsets = (
        (
            "업체 기본 정보",
            {
                "fields": (
                    "name",
                    "company_type",
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


# ── 브랜드 + 툴 관리 ──

@admin.register(Brand)
class BrandAdmin(ModelAdmin):
    """브랜드 Admin - autocomplete 검색용"""
    list_display = ["name"]
    search_fields = ["name"]

    def has_module_permission(self, request):
        """사이드바에 표시하지 않음 (Tool Admin에서 통합 관리)"""
        return False


@admin.register(Tool)
class ToolAdmin(NoRelatedButtonsMixin, ModelAdmin):
    """브랜드 & 툴 관리 - 메인 리스트"""
    list_display = ["brand", "model_name"]
    list_filter = ["brand"]
    search_fields = ["model_name", "brand__name"]
    autocomplete_fields = ["brand"]
    list_per_page = 20


@admin.register(Part)
class PartAdmin(NoRelatedButtonsMixin, ModelAdmin):
    list_display = ["name", "code", "part_type", "display_tools", "price"]
    list_filter = ["part_type", "tools__brand"]
    search_fields = ["name", "code"]
    filter_horizontal = ["tools"]
    list_per_page = 20

    fieldsets = (
        (
            "부품 기본 정보",
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


# ──────────────────────────────────────────────
# 의뢰업체 Admin
# ──────────────────────────────────────────────

@admin.register(OutsourceCompany)
class OutsourceCompanyAdmin(ModelAdmin):
    """의뢰업체 관리"""
    list_display = ["name", "contact", "memo"]
    search_fields = ["name"]
    list_per_page = 20


# ──────────────────────────────────────────────
# AS 프로세스 Admin
# ──────────────────────────────────────────────


# ── 일괄 입고 등록 ──

class ASTicketInline(NoRelatedButtonsMixin, TabularInline):
    """입고 배치 안에서 개별 품목을 행으로 추가"""
    model = ASTicket
    fk_name = "inbound_batch"
    fields = ["tool", "serial_number"]
    autocomplete_fields = ["tool"]
    extra = 2
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
class InboundBatchAdmin(NoRelatedButtonsMixin, ModelAdmin):
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
        css = {"all": ("as_app/css/inline_fix.css",)}

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
        from django.contrib import messages
        messages.success(request, "입고 등록이 완료되었습니다. (%s)" % obj)
        return HttpResponseRedirect(
            reverse("admin:as_app_inboundbatch_add")
        )

    def response_change(self, request, obj):
        """수정 저장 후에도 새 입고 등록 폼으로 리다이렉트"""
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
            from django.contrib import messages
            messages.error(
                request,
                "같은 배치 내에 중복된 품목이 있습니다: %s" % ", ".join(duplicates_in_batch)
            )
            return

        # 2) 기존 활성 티켓과 중복 체크
        active_statuses = [
            ASTicket.Status.INBOUND,
            ASTicket.Status.WAITING,
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
            from django.contrib import messages
            messages.error(
                request,
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
class InboundTicketAdmin(ModelAdmin):
    """개별 입고 티켓 관리 (사이드바 숨김)"""

    list_display = [
        "inbound_date",
        "company",
        "tool",
        "serial_number",
        "status",
    ]
    list_filter = ["status", "inbound_date", "company"]
    search_fields = ["serial_number", "company__name", "tool__model_name"]

    def has_module_permission(self, request):
        return False


@admin.register(RepairTicket)
class RepairTicketAdmin(NoRelatedButtonsMixin, ModelAdmin):
    """수리 기록 등록 - 목록에서 바로 편집 가능"""

    list_display = [
        "inbound_date",
        "company",
        "tool",
        "serial_number",
        "display_repair_content",
        "status",
    ]
    list_display_links = ["serial_number"]
    list_editable = ["status"]
    list_filter = ["status", "company"]
    search_fields = ["serial_number", "company__name", "tool__model_name"]
    list_per_page = 30
    actions = ["mark_as_waiting", "mark_as_repaired", "mark_as_outsourced", "mark_as_disposed"]

    class Media:
        css = {"all": ("as_app/css/inline_fix.css?v=2",)}

    fieldsets = (
        (
            "입고 정보 (읽기 전용)",
            {
                "fields": (
                    "inbound_date",
                    "company",
                    "tool",
                    "serial_number",
                    "symptom",
                ),
            },
        ),
        (
            "수리 내역",
            {
                "fields": (
                    "used_parts",
                    "repair_cost",
                    "repair_content",
                    "status",
                ),
                "description": "사용한 부품/공임을 선택하면 AS 비용이 자동 계산됩니다.",
            },
        ),
        (
            "수리 의뢰",
            {
                "fields": ("outsource_company",),
                "description": "외부 업체에 수리를 의뢰하는 경우 의뢰업체를 선택하고 상태를 '수리의뢰'로 변경하세요.",
            },
        ),
    )

    readonly_fields = [
        "inbound_date",
        "company",
        "tool",
        "serial_number",
        "symptom",
        "repair_cost",
    ]
    filter_horizontal = ["used_parts"]

    @admin.display(description="수리 내역")
    def display_repair_content(self, obj):
        parts = obj.used_parts.all()
        if parts:
            names = ", ".join(p.name for p in parts)
            return names[:50] + "…" if len(names) > 50 else names
        return "-"

    def get_queryset(self, request):
        """입고 상태인 티켓만 표시"""
        return (
            super()
            .get_queryset(request)
            .filter(status=ASTicket.Status.INBOUND)
            .prefetch_related("used_parts")
        )

    def save_related(self, request, form, formsets, change):
        """M2M 저장 후 사용 부품/공임 단가 합산으로 AS 비용 자동 계산"""
        super().save_related(request, form, formsets, change)
        obj = form.instance
        total = sum(part.price for part in obj.used_parts.all())
        if obj.repair_cost != total:
            obj.repair_cost = total
            obj.save(update_fields=["repair_cost"])

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context["show_save_and_add_another"] = False
        context["show_save_and_continue"] = False
        return super().render_change_form(request, context, add, change, form_url, obj)

    def response_change(self, request, obj):
        from django.contrib import messages
        messages.success(request, "수리 정보가 저장되었습니다. (%s)" % obj)
        return HttpResponseRedirect(
            reverse("admin:as_app_repairticket_changelist")
        )

    @unfold_action(description="선택된 항목 → 수리대기로 변경")
    def mark_as_waiting(self, request, queryset):
        updated = queryset.update(status=ASTicket.Status.WAITING)
        self.message_user(request, "%d건이 수리대기로 변경되었습니다." % updated)

    @unfold_action(description="선택된 항목 → 수리완료로 변경")
    def mark_as_repaired(self, request, queryset):
        updated = queryset.update(status=ASTicket.Status.REPAIRED)
        self.message_user(request, "%d건이 수리완료 처리되었습니다." % updated)

    @unfold_action(description="선택된 항목 → 수리의뢰로 변경")
    def mark_as_outsourced(self, request, queryset):
        updated = queryset.update(status=ASTicket.Status.OUTSOURCED)
        self.message_user(request, "%d건이 수리의뢰로 변경되었습니다." % updated)

    @unfold_action(description="선택된 항목 → 자체폐기 처리")
    def mark_as_disposed(self, request, queryset):
        updated = queryset.update(status=ASTicket.Status.DISPOSED)
        self.message_user(request, "%d건이 자체폐기 처리되었습니다." % updated)


@admin.register(OutboundTicket)
class OutboundTicketAdmin(NoRelatedButtonsMixin, ModelAdmin):
    """출고 등록 - 목록에서 바로 편집 가능"""

    list_display = [
        "inbound_date",
        "company",
        "tool",
        "serial_number",
        "display_repair_summary",
        "outbound_date",
        "estimate_status",
        "tax_invoice",
    ]
    list_display_links = ["serial_number"]
    list_editable = ["outbound_date", "estimate_status", "tax_invoice"]
    list_filter = ["estimate_status", "tax_invoice"]
    search_fields = ["serial_number", "company__name", "tool__model_name"]
    list_per_page = 30
    actions = ["mark_as_shipped"]

    fieldsets = (
        (
            "장비 정보 (읽기 전용)",
            {
                "fields": (
                    "inbound_date",
                    "company",
                    "tool",
                    "serial_number",
                    "repair_content",
                    "repair_cost",
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

    readonly_fields = [
        "inbound_date",
        "company",
        "tool",
        "serial_number",
        "repair_content",
        "repair_cost",
    ]

    @admin.display(description="수리 내용")
    def display_repair_summary(self, obj):
        if obj.repair_content:
            return obj.repair_content[:25] + "…" if len(obj.repair_content) > 25 else obj.repair_content
        return "-"

    def get_queryset(self, request):
        """수리완료 상태인 티켓만 표시"""
        return (
            super()
            .get_queryset(request)
            .filter(status=ASTicket.Status.REPAIRED)
        )

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context["show_save_and_add_another"] = False
        context["show_save_and_continue"] = False
        return super().render_change_form(request, context, add, change, form_url, obj)

    def response_change(self, request, obj):
        from django.contrib import messages
        messages.success(request, "출고 정보가 저장되었습니다. (%s)" % obj)
        return HttpResponseRedirect(
            reverse("admin:as_app_outboundticket_changelist")
        )

    @unfold_action(description="선택된 항목 출고 처리")
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(
            status=ASTicket.Status.SHIPPED,
            outbound_date=timezone.now().date(),
        )
        self.message_user(request, "%d건이 출고 처리되었습니다." % updated)


@admin.register(ASHistory)
class ASHistoryAdmin(NoRelatedButtonsMixin, ModelAdmin):
    """AS 통합 이력 조회 (Read-Only)"""

    list_display = [
        "inbound_date",
        "company",
        "tool",
        "serial_number",
        "status",
        "repair_cost",
        "outbound_date",
        "estimate_status",
        "tax_invoice",
    ]
    list_filter = [
        "status",
        "company",
        "tool__brand",
        "inbound_date",
        "estimate_status",
        "tax_invoice",
    ]
    search_fields = [
        "serial_number",
        "company__name",
        "tool__model_name",
        "tool__brand__name",
    ]
    date_hierarchy = "inbound_date"
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

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
