"""V5 기획안 대규모 admin.py 패치 스크립트
- HoldTicketAdmin 자동보류 트리거 제거
- 기존 메뉴 숨김 (RepairTicket, HoldTicket, OutsourcedTicket, OutboundTicket)
- 견적서/통합이력/대시보드 쿼리셋에 신규 상태 반영
- 신규 Admin(EstimateRegistration, StatusRegistration) 추가
"""

filepath = r"c:\Users\rlao1\AS_APP\as_app\admin.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ────────────────────────────────────────────
# 1. HoldTicketAdmin의 자동 보류 트리거 제거
# ────────────────────────────────────────────
old_hold_trigger = """        # 부품이 선택되어 있으면 수리보류(HOLD) 상태로 변경
        if obj.ticket_used_parts.exists() and obj.status != ASTicket.Status.HOLD:
            obj.status = ASTicket.Status.HOLD
            obj.hold_date = timezone.localdate()
            update_fields.append("status")
            update_fields.append("hold_date")
        if update_fields:
            obj.save(update_fields=update_fields)"""

new_hold_trigger = """        # [V5 개편] 자동 보류 트리거 제거됨
        # 상태 변경은 수동으로만 가능합니다.
        if update_fields:
            obj.save(update_fields=update_fields)"""

if old_hold_trigger in content:
    content = content.replace(old_hold_trigger, new_hold_trigger)
    changes += 1
    print("✅ 1. HoldTicketAdmin 자동 보류 트리거 제거")
else:
    print("⚠️ 1. HoldTicketAdmin 트리거를 찾지 못함")

# ────────────────────────────────────────────
# 2. 기존 메뉴 숨김 처리
# RepairTicketAdmin, HoldTicketAdmin, OutsourcedTicketAdmin, OutboundTicketAdmin
# ────────────────────────────────────────────

# RepairTicketAdmin - has_module_permission 추가 (이미 has_add_permission 있음)
if "class RepairTicketAdmin" in content and "# [V5] 사이드바 숨김" not in content:
    # RepairTicketAdmin의 response_change 다음에 has_module_permission 추가
    old_repair_response = '''    def response_change(self, request, obj):
        from django.contrib import messages
        messages.success(request, "수리 정보가 저장되었습니다. (%s)" % obj)
        return HttpResponseRedirect(
            reverse("admin:as_app_repairticket_changelist")
        )'''
    new_repair_response = '''    def response_change(self, request, obj):
        from django.contrib import messages
        messages.success(request, "수리 정보가 저장되었습니다. (%s)" % obj)
        return HttpResponseRedirect(
            reverse("admin:as_app_repairticket_changelist")
        )

    # [V5] 사이드바 숨김 — 견적등록으로 대체됨
    def has_module_permission(self, request):
        return False'''
    if old_repair_response in content:
        content = content.replace(old_repair_response, new_repair_response)
        changes += 1
        print("✅ 2a. RepairTicketAdmin 사이드바 숨김")

# HoldTicketAdmin 사이드바 숨김
old_hold_response = '''    def response_change(self, request, obj):
        from django.contrib import messages
        messages.success(request, "⏸️ 수리보류 등록이 완료되었습니다. (%s)" % obj)
        return HttpResponseRedirect(
            reverse("admin:as_app_holdticket_changelist")
        )'''
new_hold_response = '''    def response_change(self, request, obj):
        from django.contrib import messages
        messages.success(request, "⏸️ 수리보류 등록이 완료되었습니다. (%s)" % obj)
        return HttpResponseRedirect(
            reverse("admin:as_app_holdticket_changelist")
        )

    # [V5] 사이드바 숨김 — 상태등록으로 대체됨
    def has_module_permission(self, request):
        return False'''
if old_hold_response in content:
    content = content.replace(old_hold_response, new_hold_response)
    changes += 1
    print("✅ 2b. HoldTicketAdmin 사이드바 숨김")

# OutsourcedTicketAdmin 사이드바 숨김 - 이미 has_delete가 마지막이니 그 뒤에 추가
old_outsource_del = '''class OutsourcedTicketAdmin(CompositeDisplayMixin, StatusColorMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):'''
new_outsource_del = '''class OutsourcedTicketAdmin(CompositeDisplayMixin, StatusBadgeMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):'''
if old_outsource_del in content:
    content = content.replace(old_outsource_del, new_outsource_del)
    changes += 1
    print("✅ 2c-1. OutsourcedTicketAdmin Mixin 교체")

# OutboundTicketAdmin Mixin 교체
old_outbound_class = '''class OutboundTicketAdmin(CompositeDisplayMixin, StatusColorMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):'''
new_outbound_class = '''class OutboundTicketAdmin(CompositeDisplayMixin, StatusBadgeMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):'''
if old_outbound_class in content:
    content = content.replace(old_outbound_class, new_outbound_class)
    changes += 1
    print("✅ 2c-2. OutboundTicketAdmin Mixin 교체")

# RepairTicketAdmin Mixin 교체
old_repair_class = '''class RepairTicketAdmin(CompositeDisplayMixin, StatusColorMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):'''
new_repair_class = '''class RepairTicketAdmin(CompositeDisplayMixin, StatusBadgeMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):'''
if old_repair_class in content:
    content = content.replace(old_repair_class, new_repair_class)
    changes += 1
    print("✅ 2c-3. RepairTicketAdmin Mixin 교체")

# HoldTicketAdmin Mixin 교체
old_hold_class = '''class HoldTicketAdmin(CompositeDisplayMixin, StatusColorMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):'''
new_hold_class = '''class HoldTicketAdmin(CompositeDisplayMixin, StatusBadgeMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):'''
if old_hold_class in content:
    content = content.replace(old_hold_class, new_hold_class)
    changes += 1
    print("✅ 2c-4. HoldTicketAdmin Mixin 교체")

# ASHistoryAdmin Mixin 교체
old_history_class = '''class ASHistoryAdmin(StatusColorMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):'''
new_history_class = '''class ASHistoryAdmin(StatusBadgeMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):'''
if old_history_class in content:
    content = content.replace(old_history_class, new_history_class)
    changes += 1
    print("✅ 2c-5. ASHistoryAdmin Mixin 교체")

# EstimateTicketAdmin Mixin 교체
old_est_class = '''class EstimateTicketAdmin(CompositeDisplayMixin, StatusColorMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):'''
new_est_class = '''class EstimateTicketAdmin(CompositeDisplayMixin, StatusBadgeMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):'''
if old_est_class in content:
    content = content.replace(old_est_class, new_est_class)
    changes += 1
    print("✅ 2c-6. EstimateTicketAdmin Mixin 교체")

# TaxInvoiceTicketAdmin Mixin 교체
old_tax_class = '''class TaxInvoiceTicketAdmin(CompositeDisplayMixin, StatusColorMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):'''
new_tax_class = '''class TaxInvoiceTicketAdmin(CompositeDisplayMixin, StatusBadgeMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):'''
if old_tax_class in content:
    content = content.replace(old_tax_class, new_tax_class)
    changes += 1
    print("✅ 2c-7. TaxInvoiceTicketAdmin Mixin 교체")

# InboundTicketAdmin Mixin 교체
old_inbound_class = '''class InboundTicketAdmin(StatusColorMixin, ModelAdmin):'''
new_inbound_class = '''class InboundTicketAdmin(StatusBadgeMixin, ModelAdmin):'''
if old_inbound_class in content:
    content = content.replace(old_inbound_class, new_inbound_class)
    changes += 1
    print("✅ 2c-8. InboundTicketAdmin Mixin 교체")

# ────────────────────────────────────────────
# 3. 견적서 발행 쿼리셋에 신규 상태 추가
# ────────────────────────────────────────────
old_est_qs = '''.filter(status__in=[ASTicket.Status.REPAIRED, ASTicket.Status.SHIPPED, ASTicket.Status.HOLD])'''
new_est_qs = '''.filter(status__in=[ASTicket.Status.REPAIRED, ASTicket.Status.SHIPPED, ASTicket.Status.SHIPPED_UNREPAIRED, ASTicket.Status.HOLD, ASTicket.Status.ESTIMATE_DONE])'''
if old_est_qs in content:
    content = content.replace(old_est_qs, new_est_qs)
    changes += 1
    print("✅ 3. 견적서 발행 쿼리셋에 견적완료/출고(미수리) 추가")

# ────────────────────────────────────────────
# 4. 세금계산서 쿼리셋 - 출고(수리완료)만 표시하도록 유지 (이미 SHIPPED만. 변경 불필요)
# ────────────────────────────────────────────
print("✅ 4. 세금계산서 쿼리셋은 출고(수리완료)만 — 기존 유지")

# ────────────────────────────────────────────
# 5. 통합이력 액션 업데이트 — 출고(미수리) 취소 액션 추가
# 기존 revert_shipped_to_repaired 다음 블록에 신규 액션 추가
# ────────────────────────────────────────────
old_history_actions = '''    actions = [
        "revert_shipped_to_repaired",
        "revert_repaired_to_inbound",
        "revert_outsourced_to_inbound",
        "revert_disposed_to_inbound",
        "mark_as_hold",
        "revert_hold_to_previous",
        "reset_estimate_status",
        "reset_tax_invoice",
        "mark_as_disposed",
    ]'''
new_history_actions = '''    actions = [
        "revert_shipped_to_repaired",
        "revert_shipped_unrepaired_to_inbound",
        "revert_repaired_to_inbound",
        "revert_outsourced_to_inbound",
        "revert_disposed_to_inbound",
        "mark_as_hold",
        "revert_hold_to_previous",
        "revert_estimate_done_to_inbound",
        "reset_estimate_status",
        "reset_tax_invoice",
        "mark_as_disposed",
    ]'''
if old_history_actions in content:
    content = content.replace(old_history_actions, new_history_actions)
    changes += 1
    print("✅ 5. 통합이력 actions 목록에 신규 롤백 액션 추가")

# ────────────────────────────────────────────
# 6. 파일 끝에 신규 Admin 클래스 추가 (EstimateRegistrationAdmin, StatusRegistrationAdmin)
# ────────────────────────────────────────────
new_admins = '''

# ──────────────────────────────────────────────
# [V5 개편] 견적등록 Admin (기존 수리기록등록 + 수리보류등록 대체)
# ──────────────────────────────────────────────

@admin.register(EstimateRegistration)
class EstimateRegistrationAdmin(CompositeDisplayMixin, StatusBadgeMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):
    custom_title = "견적등록"
    """견적등록 - 부품/공임을 입력하고 상태를 수동으로 변경하는 집중 작업 공간"""

    # ── 목록 화면 설정 ──
    list_display = [
        "display_status",
        "inbound_date",
        "display_company_info",
        "display_tool_info",
        "display_estimate_button",
    ]
    list_display_links = None  # 행 클릭 비활성화 (버튼으로만 이동)
    search_fields = ["serial_number", "company__name", "tool__model_name"]
    list_per_page = 30
    actions = None

    class Media:
        css = {"all": ("as_app/css/inline_fix.css", "as_app/css/hide_fab.css", "as_app/css/status_badge.css", "as_app/css/parts_table.css", "as_app/css/multiline_cell.css")}
        js = ("as_app/js/parts_table.js",)

    # ── 견적등록 폼 설정 ──
    fieldsets = (
        (
            "상태 변경",
            {
                "fields": ("status",),
                "description": "⚠️ 상태를 변경하려면 아래 드롭다운에서 선택 후 저장하세요. 출고/수리의뢰는 이곳에서 변경할 수 없으며, 반드시 '상태 등록' 메뉴를 이용하세요.",
            },
        ),
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
            "견적/수리 부품 선택",
            {
                "fields": (
                    "selected_parts",
                    "repair_content",
                ),
                "description": "해당 장비에 적용 가능한 부품/공임이 표시됩니다. 체크하고 저장하면 AS 비용이 자동 계산됩니다. (상태는 자동으로 변하지 않습니다)",
            },
        ),
    )

    readonly_fields = [
        "inbound_date",
        "company",
        "tool",
        "serial_number",
    ]

    @admin.display(description="견적 등록")
    def display_estimate_button(self, obj):
        """목록에서 견적 등록 버튼을 표시"""
        url = reverse("admin:as_app_estimateregistration_change", args=[obj.pk])
        return format_html(
            \'<a href="{}" style="\\'
            \'display:inline-flex; align-items:center; gap:6px; \\'
            \'padding:6px 14px; border-radius:6px; font-size:0.8rem; \\'
            \'font-weight:600; text-decoration:none; \\'
            \'background:#6366f1; color:#fff; \\'
            \'transition:all .15s ease;\\'
            \'" \\'
            \'onmouseover="this.style.background=\\\\'#4f46e5\\\\'" \\'
            \'onmouseout="this.style.background=\\\\'#6366f1\\\\'">\\x3c/a>\',
            url
        )

    def get_form(self, request, obj=None, **kwargs):
        """견적등록 편집 폼: 해당 장비 부품만 필터링 + 테이블 위젯"""
        kwargs["form"] = RepairTicketForm
        from .widgets import PartsTableWidget
        form = super().get_form(request, obj, **kwargs)

        # [V5 안전장치] 상태 드롭다운에서 출고/의뢰 등 예민한 상태 숨김
        if "status" in form.base_fields:
            # 견적등록에서 선택 가능한 상태만 허용
            allowed_statuses = [
                ASTicket.Status.INBOUND,
                ASTicket.Status.ESTIMATE_DONE,
                ASTicket.Status.REPAIRED,
                ASTicket.Status.HOLD,
                ASTicket.Status.DISPOSED,
            ]
            form.base_fields["status"].choices = [
                (value, label)
                for value, label in ASTicket.Status.choices
                if value in [s.value for s in allowed_statuses]
            ]

        if obj and obj.tool_id:
            from django.db.models import Q
            parts_qs = Part.objects.filter(
                Q(tools=obj.tool) | Q(tools__isnull=True)
            ).distinct().order_by("part_type", "name")
            form.base_fields["selected_parts"].queryset = parts_qs

            has_category = obj.company and obj.company.price_group

            if not has_category:
                msg = format_html(
                    \'⚠️ <strong>[{}]</strong>에 단가 그룹이 설정되어 있지 않습니다.<br>\'
                    \'견적 기록을 저장할 수 없으므로, <a href="{}" style="color:#b91c1c; text-decoration:underline;">[업체관리]</a>에서 단가 그룹을 먼저 지정해주세요.\',
                    obj.company.name if obj.company else "업체",
                    reverse("admin:master_data_company_change", args=[obj.company.id]) if obj.company else "#"
                )
                form.base_fields["selected_parts"].widget = PartsTableWidget(disabled_message=msg)
            else:
                parts_data = {}
                for p in parts_qs:
                    parts_data[p.id] = {
                        "name": p.name,
                        "code": p.code,
                        "price": p.get_price_for_company(obj.company),
                        "part_type": p.part_type,
                    }
                form.base_fields["selected_parts"].widget = PartsTableWidget(
                    parts_data=parts_data,
                )
        if "repair_content" in form.base_fields:
            form.base_fields["repair_content"].widget = forms.TextInput(
                attrs={"placeholder": "추가 메모가 있으면 입력하세요 (선택사항)", "style": "width:100%"}
            )
        return form

    def get_queryset(self, request):
        """입고/수리의뢰/견적완료/수리보류 상태인 티켓만 표시 (견적 작성 대상)"""
        return (
            super()
            .get_queryset(request)
            .filter(
                status__in=[
                    ASTicket.Status.INBOUND,
                    ASTicket.Status.ESTIMATE_DONE,
                    ASTicket.Status.OUTSOURCED,
                    ASTicket.Status.HOLD,
                ]
            )
            .select_related("company", "tool", "tool__brand")
            .prefetch_related("used_parts")
        )

    # ── 권한 제어 ──
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # ── 저장 로직 (부품 스냅샷 + 비용 계산, 상태 자동변경 없음) ──
    def save_related(self, request, form, formsets, change):
        """M2M 저장 후 사용 부품/공임 단가 스냅샷 보존 및 비용 계산"""
        super().save_related(request, form, formsets, change)
        obj = form.instance

        if "selected_parts" in form.cleaned_data:
            selected_parts = form.cleaned_data["selected_parts"]
            current_parts = set(obj.used_parts.all())
            new_parts = set(selected_parts)

            # ── 미설정 단가 부품 차단 ──
            missing_price_parts = [
                p for p in new_parts
                if p.get_price_for_company(obj.company) is None
            ]
            if missing_price_parts:
                group_name = obj.company.price_group.name if (obj.company and obj.company.price_group) else "미지정"
                part_names = ", ".join(p.name for p in missing_price_parts)
                from django.contrib import messages
                messages.error(
                    request,
                    f"⚠️ 다음 부품의 [{group_name}] 단가가 설정되지 않았습니다: {part_names}. "
                    f"부품 관리에서 해당 단가 그룹의 가격을 먼저 입력해주세요."
                )
                obj.ticket_used_parts.filter(part__in=missing_price_parts).delete()
                new_parts -= set(missing_price_parts)

            to_remove = current_parts - new_parts
            if to_remove:
                obj.ticket_used_parts.filter(part__in=to_remove).delete()

            to_add = new_parts - current_parts
            for part in to_add:
                price = part.get_price_for_company(obj.company)
                obj.ticket_used_parts.create(part=part, applied_price=price)

        # 비용 계산 (자동 상태변경 없음)
        total_parts = sum(tup.applied_price for tup in obj.ticket_used_parts.all())
        nego_price = int(total_parts * 0.9)
        total_with_vat = int(nego_price * 1.1)
        update_fields = []
        if obj.repair_cost != total_with_vat:
            obj.repair_cost = total_with_vat
            update_fields.append("repair_cost")
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
                parts = preset.parts.all()
                part_ids = [p.id for p in parts if p.part_type == \'part\']
                labor_ids = [p.id for p in parts if p.part_type == \'labor\']
                company_total = sum((p.get_price_for_company(obj.company) or 0) for p in parts)
                preset_data.append({
                    "id": preset.id,
                    "name": preset.name,
                    "part_ids": part_ids,
                    "labor_ids": labor_ids,
                    "total_price": company_total,
                })
            context["repair_presets"] = preset_data
            from django.db.models import Q as Q2
            all_parts = Part.objects.filter(
                Q2(tools=obj.tool) | Q2(tools__isnull=True)
            ).distinct().prefetch_related(\'group_prices\')
            parts_meta = []
            for p in all_parts:
                p_price = p.get_price_for_company(obj.company)
                parts_meta.append({"id": p.id, "part_type": p.part_type, "price": p_price})
            context["parts_meta"] = parts_meta
        else:
            context["repair_presets"] = []
            context["parts_meta"] = []
        return super().render_change_form(request, context, add, change, form_url, obj)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_history"] = False
        return super().change_view(request, object_id, form_url, extra_context)

    def response_change(self, request, obj):
        from django.contrib import messages
        messages.success(request, "견적 정보가 저장되었습니다. (%s)" % obj)
        return HttpResponseRedirect(
            reverse("admin:as_app_estimateregistration_changelist")
        )


# ──────────────────────────────────────────────
# [V5 개편] 상태 등록 Admin (기존 출고등록 + 수리의뢰등록 + 수리보류등록 통합)
# ──────────────────────────────────────────────

@admin.register(StatusRegistration)
class StatusRegistrationAdmin(CompositeDisplayMixin, StatusBadgeMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):
    custom_title = "상태 등록"
    """상태 등록 - 체크박스 선택 후 일괄 액션으로 출고/의뢰/보류를 처리하는 스피드 화면"""

    list_display = [
        "display_status",
        "inbound_date",
        "display_company_info",
        "display_tool_info",
        "display_repair_summary",
        "formatted_repair_cost",
    ]
    list_display_links = None
    list_filter = [
        "status",
        "company",
        "tool__brand",
        ("inbound_date", RangeDateFilter),
    ]
    search_fields = ["serial_number", "company__name", "tool__model_name", "tool__brand__name"]
    list_per_page = 30
    actions = [
        "action_ship_today",
        "action_ship_with_date",
        "action_ship_unrepaired_today",
        "action_ship_unrepaired_with_date",
        "action_outsource",
        "action_mark_hold",
        "action_mark_repaired",
        "action_mark_estimate_done",
    ]
    ordering = ["-inbound_date", "-created_at"]

    class Media:
        css = {"all": ("as_app/css/hide_fab.css", "as_app/css/status_badge.css", "as_app/css/multiline_cell.css")}

    @admin.display(description="수리 내역")
    def display_repair_summary(self, obj):
        parts_list = list(obj.ticket_used_parts.all())
        if not parts_list:
            return "-"
        parts_list.sort(
            key=lambda tup: (0 if tup.part.part_type == \'labor\' else 1, -tup.applied_price)
        )
        count = len(parts_list)
        first = parts_list[0].part
        first_code = f" ({first.code})" if first.code else ""
        first_label = "공임" if first.part_type == "labor" else "부품"
        summary_text = f"[{first_label}] {first.name}{first_code}"
        if count == 1:
            return format_html(\'<span>{}</span>\', summary_text)
        return format_html(\'<span><strong>{}</strong> 외 {}건</span>\', summary_text, count - 1)

    @admin.display(description="수리 비용")
    def formatted_repair_cost(self, obj):
        return f"{obj.repair_cost:,}원" if obj.repair_cost else "0원"

    def get_queryset(self, request):
        """출고/폐기 상태가 아닌 모든 활성 티켓을 표시"""
        return (
            super()
            .get_queryset(request)
            .exclude(status__in=[
                ASTicket.Status.SHIPPED,
                ASTicket.Status.SHIPPED_UNREPAIRED,
                ASTicket.Status.DISPOSED,
            ])
            .select_related("company", "tool", "tool__brand")
            .prefetch_related("ticket_used_parts", "ticket_used_parts__part")
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # ── 출고 (수리완료) 액션 ──
    @unfold_action(description="📤 선택 항목 출고(수리완료) — 오늘 날짜")
    def action_ship_today(self, request, queryset):
        invalid = queryset.exclude(status=ASTicket.Status.REPAIRED)
        if invalid.exists():
            from django.contrib import messages
            messages.error(request, "수리완료 상태가 아닌 항목이 포함되어 있습니다. 수리완료 상태인 항목만 선택해 주세요.")
            return
        today = timezone.localdate()
        updated = queryset.update(status=ASTicket.Status.SHIPPED, outbound_date=today)
        from django.contrib import messages
        messages.success(request, f"{updated}건이 출고(수리완료) 처리되었습니다. (출고일: {today})")

    @unfold_action(description="📅 선택 항목 출고(수리완료) — 날짜 선택")
    def action_ship_with_date(self, request, queryset):
        from django.template.response import TemplateResponse
        import datetime
        invalid = queryset.exclude(status=ASTicket.Status.REPAIRED)
        if invalid.exists():
            from django.contrib import messages
            messages.error(request, "수리완료 상태가 아닌 항목이 포함되어 있습니다. 수리완료 상태인 항목만 선택해 주세요.")
            return
        if request.POST.get("confirm") == "yes":
            date_str = request.POST.get("outbound_date", "")
            try:
                outbound_date = datetime.date.fromisoformat(date_str) if date_str else timezone.localdate()
            except (ValueError, TypeError):
                from django.contrib import messages
                messages.error(request, "올바른 날짜 형식이 아닙니다.")
                return None
            updated = queryset.update(status=ASTicket.Status.SHIPPED, outbound_date=outbound_date)
            from django.contrib import messages
            messages.success(request, f"{updated}건이 출고(수리완료) 처리되었습니다. (출고일: {outbound_date})")
            return None
        context = {
            **self.admin_site.each_context(request),
            "title": "출고(수리완료) 날짜 선택",
            "ticket_count": queryset.count(),
            "selected_pks": list(queryset.values_list("pk", flat=True)),
            "today": timezone.localdate().isoformat(),
            "opts": self.model._meta,
        }
        return TemplateResponse(request, "admin/as_app/outbound_date_select.html", context)

    # ── 출고 (미수리) 액션 ──
    @unfold_action(description="🔙 선택 항목 출고(미수리) — 오늘 날짜")
    def action_ship_unrepaired_today(self, request, queryset):
        valid_statuses = [ASTicket.Status.INBOUND, ASTicket.Status.ESTIMATE_DONE, ASTicket.Status.HOLD, ASTicket.Status.OUTSOURCED]
        invalid = queryset.exclude(status__in=valid_statuses)
        if invalid.exists():
            from django.contrib import messages
            messages.error(request, "이미 출고되었거나 수리완료된 항목이 포함되어 있습니다.")
            return
        today = timezone.localdate()
        updated = queryset.update(status=ASTicket.Status.SHIPPED_UNREPAIRED, outbound_date=today)
        from django.contrib import messages
        messages.success(request, f"{updated}건이 출고(미수리) 처리되었습니다. (출고일: {today})")

    @unfold_action(description="📅 선택 항목 출고(미수리) — 날짜 선택")
    def action_ship_unrepaired_with_date(self, request, queryset):
        from django.template.response import TemplateResponse
        import datetime
        valid_statuses = [ASTicket.Status.INBOUND, ASTicket.Status.ESTIMATE_DONE, ASTicket.Status.HOLD, ASTicket.Status.OUTSOURCED]
        invalid = queryset.exclude(status__in=valid_statuses)
        if invalid.exists():
            from django.contrib import messages
            messages.error(request, "이미 출고되었거나 수리완료된 항목이 포함되어 있습니다.")
            return
        if request.POST.get("confirm") == "yes":
            date_str = request.POST.get("outbound_date", "")
            try:
                outbound_date = datetime.date.fromisoformat(date_str) if date_str else timezone.localdate()
            except (ValueError, TypeError):
                from django.contrib import messages
                messages.error(request, "올바른 날짜 형식이 아닙니다.")
                return None
            updated = queryset.update(status=ASTicket.Status.SHIPPED_UNREPAIRED, outbound_date=outbound_date)
            from django.contrib import messages
            messages.success(request, f"{updated}건이 출고(미수리) 처리되었습니다. (출고일: {outbound_date})")
            return None
        context = {
            **self.admin_site.each_context(request),
            "title": "출고(미수리) 날짜 선택",
            "ticket_count": queryset.count(),
            "selected_pks": list(queryset.values_list("pk", flat=True)),
            "today": timezone.localdate().isoformat(),
            "opts": self.model._meta,
        }
        return TemplateResponse(request, "admin/as_app/outbound_date_select.html", context)

    # ── 수리의뢰 액션 ──
    @unfold_action(description="📦 선택 항목 수리의뢰 처리")
    def action_outsource(self, request, queryset):
        from django.template.response import TemplateResponse
        import datetime
        invalid = queryset.exclude(status=ASTicket.Status.INBOUND)
        if invalid.exists():
            from django.contrib import messages
            messages.error(request, "입고 상태가 아닌 항목이 포함되어 있습니다. 입고 상태인 항목만 선택해 주세요.")
            return
        if request.POST.get("confirm") == "yes":
            company_id = request.POST.get("outsource_company")
            date_str = request.POST.get("outsource_date", "")
            if not company_id:
                from django.contrib import messages
                messages.error(request, "의뢰업체를 선택해야 합니다.")
                return None
            try:
                outsource_date = datetime.date.fromisoformat(date_str) if date_str else timezone.localdate()
            except (ValueError, TypeError):
                from django.contrib import messages
                messages.error(request, "올바른 날짜 형식이 아닙니다.")
                return None
            try:
                company = OutsourceCompany.objects.get(pk=company_id)
            except OutsourceCompany.DoesNotExist:
                from django.contrib import messages
                messages.error(request, "존재하지 않는 의뢰업체입니다.")
                return None
            tickets_to_update = []
            for ticket in queryset:
                ticket.status = ASTicket.Status.OUTSOURCED
                ticket.outsource_company = company
                ticket.outsource_date = outsource_date
                remarks_text = f"{company.name} 수리의뢰 ({outsource_date.strftime(\'%Y-%m-%d\')}~)"
                if ticket.repair_content:
                    ticket.repair_content = f"{ticket.repair_content}\\n{remarks_text}"
                else:
                    ticket.repair_content = remarks_text
                tickets_to_update.append(ticket)
            ASTicket.objects.bulk_update(
                tickets_to_update,
                fields=["status", "outsource_company", "outsource_date", "repair_content"]
            )
            from django.contrib import messages
            messages.success(request, f"{len(tickets_to_update)}건이 수리의뢰 처리되었습니다. (의뢰업체: {company.name})")
            return None
        companies = OutsourceCompany.objects.all().order_by("name")
        context = dict(
            self.admin_site.each_context(request),
            title="수리의뢰 처리 (의뢰업체 선택)",
            queryset=queryset,
            companies=companies,
            default_date=timezone.localdate().strftime("%Y-%m-%d"),
            action_checkbox_name=admin.helpers.ACTION_CHECKBOX_NAME,
        )
        return TemplateResponse(request, "admin/as_app/action_outsource.html", context)

    # ── 보류 처리 액션 ──
    @unfold_action(description="⏸️ 선택 항목 → 수리보류 처리")
    def action_mark_hold(self, request, queryset):
        valid_statuses = [ASTicket.Status.INBOUND, ASTicket.Status.ESTIMATE_DONE, ASTicket.Status.OUTSOURCED, ASTicket.Status.REPAIRED]
        invalid = queryset.exclude(status__in=valid_statuses)
        if invalid.exists():
            from django.contrib import messages
            messages.error(request, "수리보류 불가한 상태의 항목이 포함되어 있습니다.")
            return
        updated = queryset.update(status=ASTicket.Status.HOLD, hold_date=timezone.localdate())
        from django.contrib import messages
        messages.success(request, f"{updated}건이 수리보류 처리되었습니다.")

    # ── 수리완료 처리 액션 ──
    @unfold_action(description="✅ 선택 항목 → 수리완료 처리")
    def action_mark_repaired(self, request, queryset):
        valid_statuses = [ASTicket.Status.INBOUND, ASTicket.Status.ESTIMATE_DONE, ASTicket.Status.OUTSOURCED, ASTicket.Status.HOLD]
        invalid = queryset.exclude(status__in=valid_statuses)
        if invalid.exists():
            from django.contrib import messages
            messages.error(request, "수리완료로 변경할 수 없는 상태의 항목이 포함되어 있습니다.")
            return
        updated = queryset.update(status=ASTicket.Status.REPAIRED)
        from django.contrib import messages
        messages.success(request, f"{updated}건이 수리완료 처리되었습니다.")

    # ── 견적완료 처리 액션 ──
    @unfold_action(description="📋 선택 항목 → 견적완료 처리")
    def action_mark_estimate_done(self, request, queryset):
        valid_statuses = [ASTicket.Status.INBOUND, ASTicket.Status.HOLD]
        invalid = queryset.exclude(status__in=valid_statuses)
        if invalid.exists():
            from django.contrib import messages
            messages.error(request, "입고 또는 수리보류 상태인 항목만 견적완료로 변경할 수 있습니다.")
            return
        updated = queryset.update(status=ASTicket.Status.ESTIMATE_DONE)
        from django.contrib import messages
        messages.success(request, f"{updated}건이 견적완료 처리되었습니다.")
'''

# 파일 끝(마지막 줄) 앞에 추가
if "EstimateRegistrationAdmin" not in content:
    content = content.rstrip() + "\n" + new_admins
    changes += 1
    print("✅ 6. EstimateRegistrationAdmin + StatusRegistrationAdmin 추가")
else:
    print("⚠️ 6. 신규 Admin이 이미 존재합니다 (스킵)")

# ────────────────────────────────────────────
# 7. 통합이력에 신규 롤백 액션 메서드 추가
# mark_as_disposed 다음에 추가
# ────────────────────────────────────────────
old_disposed_action = '''    @unfold_action(description="🗑️ 입고 → 자체폐기 처리")
    def mark_as_disposed(self, request, queryset):
        if not self._validate_status(request, queryset, ASTicket.Status.INBOUND, "입고"):
            return
        updated = queryset.update(status=ASTicket.Status.DISPOSED)
        from django.contrib import messages
        messages.success(request, f"{updated}건이 자체폐기 처리되었습니다.")'''

new_disposed_action = '''    @unfold_action(description="🗑️ 입고 → 자체폐기 처리")
    def mark_as_disposed(self, request, queryset):
        if not self._validate_status(request, queryset, ASTicket.Status.INBOUND, "입고"):
            return
        updated = queryset.update(status=ASTicket.Status.DISPOSED)
        from django.contrib import messages
        messages.success(request, f"{updated}건이 자체폐기 처리되었습니다.")

    @unfold_action(description="⏪ 출고(미수리) 취소 → 입고로 되돌리기")
    def revert_shipped_unrepaired_to_inbound(self, request, queryset):
        if not self._validate_status(request, queryset, ASTicket.Status.SHIPPED_UNREPAIRED, "출고(미수리)"):
            return
        updated = queryset.update(status=ASTicket.Status.INBOUND, outbound_date=None)
        from django.contrib import messages
        messages.success(request, f"{updated}건이 입고 상태로 되돌려졌습니다. (출고일 초기화)")

    @unfold_action(description="⏪ 견적완료 취소 → 입고로 되돌리기")
    def revert_estimate_done_to_inbound(self, request, queryset):
        if not self._validate_status(request, queryset, ASTicket.Status.ESTIMATE_DONE, "견적완료"):
            return
        updated = queryset.update(status=ASTicket.Status.INBOUND)
        from django.contrib import messages
        messages.success(request, f"{updated}건이 입고 상태로 되돌려졌습니다.")'''

if old_disposed_action in content:
    content = content.replace(old_disposed_action, new_disposed_action)
    changes += 1
    print("✅ 7. 통합이력에 출고(미수리)/견적완료 롤백 액션 추가")

# ────────────────────────────────────────────
# 저장
# ────────────────────────────────────────────
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n총 {changes}개 변경사항이 admin.py에 적용되었습니다.")
