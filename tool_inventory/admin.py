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
    actions = ['cancel_outbound']
    list_filter = ('status', 'supplier', 'release_company')
    search_fields = ('tool__model_name', 'tool__brand__name', 'serial', 'supplier__name', 'release_company__name')
    list_per_page = 50
    autocomplete_fields = ('tool', 'supplier', 'release_company')

    class Media:
        css = {"all": ("as_app/css/row_colors.css",)}
        js = ("as_app/js/inventory_change.js",)

    @unfold_action(description="↩️ 선택한 장비 출고 취소 (재고로 원복)")
    def cancel_outbound(self, request, queryset):
        qs = queryset.filter(status='출고')
        count = qs.count()
        if count == 0:
            from django.contrib import messages
            messages.warning(request, "선택한 항목 중 '출고' 상태인 장비가 없습니다.")
            return

        for obj in qs:
            obj.status = '재고'
            obj.release_date = None
            obj.release_company = None
            obj.save(update_fields=['status', 'release_date', 'release_company'])
            
        from django.contrib import messages
        messages.success(request, f"총 {count}개의 장비가 성공적으로 재고로 원복되었습니다.")

    def has_add_permission(self, request):
        return False

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context["show_save_and_continue"] = False
        return super().render_change_form(request, context, add, change, form_url, obj)

    def get_fields(self, request, obj=None):
        if obj:
            return ('id', 'date', 'supplier_text', 'tool_text', 'serial', 'release_date', 'release_company', 'status')
        return ('date', 'supplier', 'tool', 'serial', 'status')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            # 수정 모드: 'serial', 'release_company', 'release_date' 수정 가능
            # 입고배치(batch)는 fields에서 제외하여 보이지 않게 함
            # 품목(tool) 및 입고처(supplier)는 단순 텍스트로 표시되어 링크 이동 방지
            return ['id', 'date', 'supplier_text', 'tool_text', 'status']
        return super().get_readonly_fields(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'release_company' in form.base_fields:
            widget = form.base_fields['release_company'].widget
            widget.can_add_related = False
            widget.can_change_related = False
            widget.can_delete_related = False
            widget.can_view_related = False
        return form

    @display(description="입고처")
    def supplier_text(self, obj):
        return str(obj.supplier) if obj.supplier else "-"

    @display(description="품목명")
    def tool_text(self, obj):
        return str(obj.tool) if obj.tool else "-"

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
    fields = ["brand", "tool", "no_serial", "quantity", "serial"]
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
        for inline_form in formset.forms:
            if inline_form.instance in formset.deleted_objects or getattr(inline_form, 'cleaned_data', None) is None:
                continue
            if not inline_form.has_changed() and not inline_form.instance.pk:
                continue
                
            instance = inline_form.instance
            no_serial = inline_form.cleaned_data.get('no_serial', False)
            quantity = inline_form.cleaned_data.get('quantity', 1) or 1
            
            if no_serial:
                for _ in range(quantity):
                    if _ == 0:
                        instance.serial = None
                        expanded.append(instance)
                    else:
                        new_inv = Inventory(
                            batch=batch,
                            tool=instance.tool,
                            serial=None,
                        )
                        expanded.append(new_inv)
            elif instance.tool_id and instance.serial:
                serials = [s.strip() for s in instance.serial.split(",") if s.strip()]
                if len(serials) > 1:
                    instance.serial = serials[0]
                    expanded.append(instance)
                    for sn in serials[1:]:
                        new_inv = Inventory(
                            batch=batch,
                            tool=instance.tool,
                            serial=sn,
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
            for inline_form in formset.forms:
                instance = inline_form.instance
                
                # 삭제 대상이거나 빈 폼(cleaned_data가 없는 경우)은 건너뜀
                if instance in formset.deleted_objects or not getattr(inline_form, 'cleaned_data', None):
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

from .models import ToolStockSummary

@admin.register(ToolStockSummary, site=tool_admin_site)
class ToolStockSummaryAdmin(ModelAdmin):
    list_display = ('brand', 'model_name', 'stock_count', 'serial_list')
    search_fields = ('brand__name', 'model_name')
    list_filter = ('brand',)
    list_per_page = 50
    actions = None
    list_disable_select_all = True
    actions_list = ["export_stock_pdf"]

    def has_add_permission(self, request):
        return False
        
    def has_change_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        # Tools that only have inventory records maybe? 
        # For now, let's just return all tools.
        return super().get_queryset(request)

    @display(description="현재 재고 수량")
    def stock_count(self, obj):
        count = Inventory.objects.filter(tool=obj, status='재고').count()
        return format_html(
            '<span style="font-weight: bold; color: {};">{}개</span>',
            '#10b981' if count > 0 else '#ef4444', 
            count
        )

    @display(description="보유 시리얼 목록")
    def serial_list(self, obj):
        from django.db.models import Q
        invs = Inventory.objects.filter(tool=obj, status='재고').order_by('date')
        serials = [inv.serial for inv in invs if inv.serial]
        no_serial_count = invs.filter(Q(serial__isnull=True) | Q(serial__exact='')).count()
        
        parts = []
        if serials:
            parts.append(", ".join(serials))
        if no_serial_count > 0:
            parts.append(f"(S/N 없음: {no_serial_count}개)")
            
        return " / ".join(parts) if parts else "-"

    @unfold_action(description="재고 내역 출력", url_path="export-stock-pdf", attrs={"style": "background-color: #9333ea; color: white; border: none;"})
    def export_stock_pdf(self, request):
        queryset = self.get_queryset(request)
        import io
        from django.http import FileResponse
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os
        from django.db.models import Q
        from django.utils import timezone
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        font_name = 'Helvetica'
        try:
            font_path = "c:\\Windows\\Fonts\\malgun.ttf"
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Malgun', font_path))
                font_name = 'Malgun'
        except Exception:
            pass
            
        queryset = queryset.select_related('brand').order_by('brand__name', 'model_name')
        c.setFont(font_name, 16)
        c.drawString(50, 800, "현재 재고 내역")
        
        c.setFont(font_name, 10)
        c.drawRightString(550, 800, f"출력일: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
        
        y = 750
        current_brand = None
        
        import textwrap
        
        for tool in queryset:
            if y < 100:
                c.showPage()
                y = 800
                current_brand = None

            if tool.brand != current_brand:
                current_brand = tool.brand
                c.setFont(font_name, 12)
                brand_name = current_brand.name if current_brand else "미지정"
                c.setStrokeColorRGB(0.7, 0.7, 0.7)
                c.line(50, y+15, 550, y+15)
                c.setStrokeColorRGB(0, 0, 0)
                c.drawString(50, y, f"■ 브랜드: {brand_name}")
                y -= 25
            
            invs = Inventory.objects.filter(tool=tool, status='재고').order_by('date')
            count = invs.count()
            
            serials = [inv.serial for inv in invs if inv.serial]
            no_serial_count = invs.filter(Q(serial__isnull=True) | Q(serial__exact='')).count()
            
            parts = []
            if serials:
                parts.append(", ".join(serials))
            if no_serial_count > 0:
                parts.append(f"S/N 없음: {no_serial_count}개")
            
            serial_text = " / ".join(parts) if parts else "재고 없음"
            
            name_lines = textwrap.wrap(tool.model_name, width=42)
            # "내역: " prefix takes some space, adjust if first line
            serial_lines = textwrap.wrap(serial_text, width=46)
            if not serial_lines:
                serial_lines = [""]
            if not name_lines:
                name_lines = [""]
                
            max_lines = max(len(name_lines), len(serial_lines))
            
            c.setFont(font_name, 10)
            
            for i in range(max_lines):
                if y < 70:
                    c.showPage()
                    y = 800
                    c.setFont(font_name, 10)
                    
                if i == 0:
                    c.drawString(60, y, "•")
                    c.drawRightString(320, y, f"수량: {count}개")
                    c.drawString(340, y, "내역:")
                    s_x = 365
                else:
                    s_x = 340
                    
                if i < len(name_lines):
                    c.drawString(70, y, name_lines[i])
                    
                if i < len(serial_lines):
                    c.drawString(s_x, y, serial_lines[i])
                
                y -= 16
                
            y -= 4 # Extra spacing after each tool
            
        c.save()
        buffer.seek(0)
        
        filename = f"tool_stock_{timezone.now().strftime('%Y%m%d_%H%M')}.pdf"
        response = FileResponse(buffer, as_attachment=True, filename=filename)
        return response
