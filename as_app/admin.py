from django.contrib import admin
from django.utils import timezone
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action as unfold_action


class NoRelatedButtonsMixin:
    """모든 FK/M2M 드롭다운 옆의 추가/수정/삭제/보기 버튼을 제거"""

    def _remove_related_buttons(self, field):
        if field and hasattr(field, 'widget'):
            field.widget.can_add_related = False
            field.widget.can_change_related = False
            field.widget.can_delete_related = False
            field.widget.can_view_related = False
        return field

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        return self._remove_related_buttons(field)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        field = super().formfield_for_manytomany(db_field, request, **kwargs)
        return self._remove_related_buttons(field)

from .models import (
    ASHistory,
    ASTicket,
    Brand,
    Company,
    CompanyCategory,
    InboundBatch,
    InboundTicket,
    OutboundTicket,
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
# AS 프로세스 Admin
# ──────────────────────────────────────────────


# ── 일괄 입고 등록 ──

class ASTicketInline(NoRelatedButtonsMixin, TabularInline):
    """입고 배치 안에서 개별 품목을 행으로 추가"""
    model = ASTicket
    fk_name = "inbound_batch"
    fields = ["tool", "serial_number"]
    autocomplete_fields = ["tool"]
    extra = 3
    min_num = 1

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        for field in formset.form.base_fields.values():
            if hasattr(field, 'widget'):
                field.widget.can_add_related = False
                field.widget.can_change_related = False
                field.widget.can_delete_related = False
                field.widget.can_view_related = False
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

    def save_formset(self, request, form, formset, change):
        """인라인 저장 시 배치의 공통 정보를 각 티켓에 자동 복사 + 중복 검증"""
        instances = formset.save(commit=False)

        for obj in formset.deleted_objects:
            obj.delete()

        batch = form.instance

        # ── 중복 검증 ──
        # 1) 같은 배치 내 중복 체크 (tool + serial_number)
        seen = set()
        duplicates_in_batch = []
        for instance in instances:
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
            ASTicket.Status.REPAIRING,
            ASTicket.Status.REPAIRED,
        ]
        conflicts = []
        for instance in instances:
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
        for instance in instances:
            instance.inbound_date = batch.inbound_date
            instance.company = batch.company
            instance.manager = batch.manager
            instance.status = ASTicket.Status.INBOUND
            instance.save()

        formset.save_m2m()


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
    """수리 기록 전용 Admin"""

    list_display = [
        "inbound_date",
        "company",
        "tool",
        "serial_number",
        "status",
        "repair_cost",
    ]
    list_filter = ["status"]
    search_fields = ["serial_number", "company__name", "tool__model_name"]
    list_per_page = 20

    fieldsets = (
        (
            "입고 정보 (읽기 전용)",
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
    )

    readonly_fields = [
        "inbound_date",
        "company",
        "manager",
        "tool",
        "serial_number",
        "symptom",
    ]
    filter_horizontal = ["used_parts"]

    def get_queryset(self, request):
        """입고 또는 수리중 상태인 티켓만 표시"""
        return (
            super()
            .get_queryset(request)
            .filter(
                status__in=[
                    ASTicket.Status.INBOUND,
                    ASTicket.Status.REPAIRING,
                ]
            )
        )


@admin.register(OutboundTicket)
class OutboundTicketAdmin(NoRelatedButtonsMixin, ModelAdmin):
    """출고 처리 전용 Admin"""

    list_display = [
        "inbound_date",
        "company",
        "tool",
        "serial_number",
        "status",
        "outbound_date",
        "estimate_status",
        "tax_invoice",
    ]
    list_filter = ["status", "estimate_status", "tax_invoice"]
    search_fields = ["serial_number", "company__name", "tool__model_name"]
    list_per_page = 20
    actions = ["mark_as_shipped"]

    fieldsets = (
        (
            "입고 정보 (읽기 전용)",
            {
                "fields": (
                    "inbound_date",
                    "company",
                    "manager",
                    "tool",
                    "serial_number",
                ),
            },
        ),
        (
            "수리 정보 (읽기 전용)",
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

    readonly_fields = [
        "inbound_date",
        "company",
        "manager",
        "tool",
        "serial_number",
        "repair_content",
        "used_parts",
        "repair_cost",
    ]

    def get_queryset(self, request):
        """수리완료 상태인 티켓만 표시"""
        return (
            super()
            .get_queryset(request)
            .filter(status=ASTicket.Status.REPAIRED)
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
