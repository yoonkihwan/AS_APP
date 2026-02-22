from django.contrib import admin
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseRedirect
from unfold.admin import ModelAdmin, TabularInline
from unfold.sites import UnfoldAdminSite
from unfold.decorators import action as unfold_action, display
from django.utils import timezone
from django.utils.html import format_html
from .models import Inventory, InventoryBatch, InboundInventory, OutboundInventory
from .forms import InventoryForm
from as_app.models import OutsourceCompany, Company, Tool, Brand

class ToolInventoryAdminSite(UnfoldAdminSite):
    site_title = "장비/툴 관리 시스템"
    site_header = "장비/툴 관리 대시보드"
    site_url = None
    index_title = "대시보드"
    index_template = "tool_inventory/index.html"

    def app_index(self, request, app_label, extra_context=None):
        return HttpResponseRedirect(reverse('tool_admin:index'))

tool_admin_site = ToolInventoryAdminSite(name='tool_admin')

# ── Register AS_APP models for autocomplete functionality in Tool Inventory ──
@admin.register(OutsourceCompany, site=tool_admin_site)
class ToolOutsourceCompanyAdmin(ModelAdmin):
    search_fields = ["name"]
    def has_module_permission(self, request): return False

@admin.register(Company, site=tool_admin_site)
class ToolCompanyAdmin(ModelAdmin):
    search_fields = ["name"]
    def has_module_permission(self, request): return False

@admin.register(Brand, site=tool_admin_site)
class ToolBrandAdmin(ModelAdmin):
    search_fields = ["name"]
    def has_module_permission(self, request): return False

@admin.register(Tool, site=tool_admin_site)
class ToolToolAdmin(ModelAdmin):
    search_fields = ["model_name", "brand__name"]
    autocomplete_fields = ["brand"]
    def has_module_permission(self, request): return False

@admin.register(Inventory, site=tool_admin_site)
class InventoryAdmin(ModelAdmin):
    list_display = (
        'display_status', 'date', 'supplier', 'tool', 'serial', 
        'release_company', 'release_date', 'display_edit_button'
    )
    list_display_links = None
    list_filter = ('status', 'supplier', 'release_company')
    search_fields = ('tool__model_name', 'tool__brand__name', 'serial', 'supplier__name', 'release_company__name')
    list_per_page = 50
    autocomplete_fields = ('tool', 'supplier', 'release_company')

    class Media:
        css = {"all": ("as_app/css/row_colors.css",)}

    def has_add_permission(self, request):
        return False

    @display(description="상태")
    def display_status(self, obj):
        css_status = "inbound" if obj.status == "재고" else "shipped"
        return format_html(
            '<span class="status-marker" data-status="{}">{}</span>',
            css_status,
            obj.get_status_display(),
        )

    @display(description="수정")
    def display_edit_button(self, obj):
        url = reverse("tool_admin:tool_inventory_inventory_change", args=[obj.pk])
        return format_html(
            '<a href="{}" style="'
            'display:inline-flex; align-items:center; gap:4px; '
            'padding:6px 12px; border-radius:6px; font-size:0.8rem; '
            'font-weight:600; text-decoration:none; '
            'background:#8b5cf6; color:#fff; '
            'transition:all .15s ease;'
            '" '
            'onmouseover="this.style.background=\'#7c3aed\'" '
            'onmouseout="this.style.background=\'#8b5cf6\'">'
            '📝 수정</a>',
            url
        )

class InventoryInline(TabularInline):
    model = Inventory
    fk_name = "batch"
    form = InventoryForm
    fields = ["brand", "tool", "serial"]
    verbose_name = "입고등록 티켓"
    verbose_name_plural = "입고등록 티켓"
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
                if hasattr(field.widget, 'attrs'):
                    field.widget.attrs['autocomplete'] = 'off'
        if 'serial' in formset.form.base_fields:
            formset.form.base_fields['serial'].label = "시리얼 번호 (쉼표로 구분 시 다건 등록)"
        return formset

@admin.register(InventoryBatch, site=tool_admin_site)
class InventoryBatchAdmin(ModelAdmin):
    list_display = ["inbound_date", "supplier", "created_at"]
    list_filter = ["inbound_date", "supplier"]
    search_fields = ["supplier__name"]
    autocomplete_fields = ["supplier"]
    date_hierarchy = "inbound_date"
    list_per_page = 20
    inlines = [InventoryInline]

    class Media:
        css = {"all": ("as_app/css/inline_fix.css", "as_app/css/hide_fab.css")}
        js = ("as_app/js/inbound_form.js",)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'supplier' in form.base_fields:
            widget = form.base_fields['supplier'].widget
            widget.can_add_related = False
            widget.can_change_related = False
            widget.can_delete_related = False
            widget.can_view_related = False
        return form

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context["show_save_and_add_another"] = False
        context["show_save_and_continue"] = False
        return super().render_change_form(request, context, add, change, form_url, obj)

    def response_add(self, request, obj, post_url_continue=None):
        if getattr(request, "_formset_validation_failed", False):
            if obj.pk and obj.inventories.count() == 0:
                obj.delete()
            return HttpResponseRedirect(request.path)
        from django.contrib import messages
        messages.success(request, f"입고 등록이 완료되었습니다. ({obj})")
        return HttpResponseRedirect(request.path)

    def response_change(self, request, obj):
        if getattr(request, "_formset_validation_failed", False):
            return HttpResponseRedirect(request.path)
        from django.contrib import messages
        messages.success(request, f"입고 정보가 수정되었습니다. ({obj})")
        return HttpResponseRedirect(request.path)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        batch = form.instance
        
        expanded = []
        for instance in instances:
            if instance.tool_id and instance.serial:
                serials = [s.strip() for s in instance.serial.split(",") if s.strip()]
                if len(serials) > 1:
                    instance.serial = serials[0]
                    expanded.append(instance)
                    for sn in serials[1:]:
                        new_inv = Inventory(
                            batch=batch,
                            tool=instance.tool,
                            serial=sn,
                            # status is '재고' by default
                        )
                        expanded.append(new_inv)
                else:
                    expanded.append(instance)
            elif instance.tool_id:
                expanded.append(instance)

        saved_count = 0
        for instance in expanded:
            instance.date = batch.inbound_date
            instance.supplier = batch.supplier
            instance.save()
            saved_count += 1
        formset.save_m2m()
        
        original_count = len(instances)
        if saved_count > original_count:
            from django.contrib import messages
            messages.info(request, f"시리얼번호 분리로 총 {saved_count}건의 툴장비가 등록되었습니다.")

from .models import Inventory, InventoryBatch, InboundInventory, OutboundInventory, OutboundBatch, OutboundTicket
from .forms import InventoryForm, OutboundTicketForm

class OutboundTicketInline(TabularInline):
    model = OutboundTicket
    fk_name = "batch"
    form = OutboundTicketForm
    fields = ["brand", "tool", "current_stock", "quantity", "inventories"]
    verbose_name = "출고등록 티켓"
    verbose_name_plural = "출고등록 티켓"
    extra = 0
    min_num = 1

@admin.register(OutboundBatch, site=tool_admin_site)
class OutboundBatchAdmin(ModelAdmin):
    list_display = ["release_date", "release_company", "created_at"]
    list_filter = ["release_date", "release_company"]
    search_fields = ["release_company__name"]
    autocomplete_fields = ["release_company"]
    list_per_page = 20
    inlines = [OutboundTicketInline]

    class Media:
        css = {"all": ("as_app/css/inline_fix.css", "as_app/css/hide_fab.css", "as_app/css/outbound_form.css")}
        js = ("as_app/js/outbound_form.js",)

    def get_model_perms(self, request):
        return {}

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if formset.model == OutboundTicket:
            for instance in formset.instances:
                if instance in formset.deleted_objects:
                    continue
                
                selected_inventories = list(instance.inventories.all())
                
                # 시리얼 번호가 골라지지 않았을 때는 선입선출 자동 배정
                if not selected_inventories:
                    qty = instance.quantity or 1
                    auto_inventories = Inventory.objects.filter(
                        tool=instance.tool, 
                        status='재고'
                    ).order_by('date')[:qty]
                    
                    for inv in auto_inventories:
                        inv.release_date = instance.batch.release_date
                        inv.release_company = instance.batch.release_company
                        inv.status = '출고'
                        inv.save()
                        instance.inventories.add(inv)
                else:
                    # 유저가 직접 다중 선택한 경우
                    for inv in selected_inventories:
                        inv.release_date = instance.batch.release_date
                        inv.release_company = instance.batch.release_company
                        inv.status = '출고'
                        inv.save()
                        
                instance.quantity = instance.inventories.count()
                instance.save()

@admin.register(OutboundInventory, site=tool_admin_site)
class OutboundInventoryAdmin(ModelAdmin):
    list_display = (
        'display_status', 'date', 'supplier', 'tool', 'serial'
    )
    list_display_links = None
    list_filter = ["supplier", "tool__brand", "tool"]
    search_fields = ["serial", "supplier__name", "tool__model_name", "tool__brand__name"]
    list_per_page = 30
    
    def changelist_view(self, request, extra_context=None):
        return HttpResponseRedirect(reverse("tool_admin:tool_inventory_outboundbatch_add"))
    list_display = (
        'display_status', 'date', 'supplier', 'tool', 'serial'
    )
    list_display_links = None
    list_filter = ["supplier", "tool__brand", "tool"]
    search_fields = ["serial", "supplier__name", "tool__model_name", "tool__brand__name"]
    list_per_page = 30

    class Media:
        css = {"all": ("as_app/css/row_colors.css",)}

    @display(description="상태")
    def display_status(self, obj):
        css_status = "inbound" if obj.status == "재고" else "shipped"
        return format_html(
            '<span class="status-marker" data-status="{}">{}</span>',
            css_status,
            obj.get_status_display(),
        )

    def get_queryset(self, request):
        # '재고' 상태인 데이터만 표시
        return super().get_queryset(request).filter(status='재고')

    def add_view(self, request, form_url='', extra_context=None):
        # "추가" 버튼 클릭 시 OutboundBatch 생성 화면으로 리다이렉트
        return HttpResponseRedirect(reverse("tool_admin:tool_inventory_outboundbatch_add"))
