from django.contrib import admin
from django.urls import path
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.sites import UnfoldAdminSite
from .models import Supplier, ReleaseSupplier, ItemName, Inventory

class ToolInventoryAdminSite(UnfoldAdminSite):
    site_title = "장비/툴 관리 시스템"
    site_header = "장비/툴 관리 대시보드"
    site_url = None
    index_title = "현황판"
    index_template = "tool_inventory/index.html"

tool_admin_site = ToolInventoryAdminSite(name='tool_admin')

@admin.register(Supplier, site=tool_admin_site)
class SupplierAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(ReleaseSupplier, site=tool_admin_site)
class ReleaseSupplierAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(ItemName, site=tool_admin_site)
class ItemNameAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Inventory, site=tool_admin_site)
class InventoryAdmin(ModelAdmin):
    list_display = ('name', 'serial', 'supplier', 'date', 'release_supplier', 'release_date', 'status')
    list_filter = ('status', 'supplier', 'release_supplier')
    search_fields = ('name__name', 'serial', 'supplier__name', 'release_supplier__name')
    date_hierarchy = 'date'
    list_per_page = 50
    autocomplete_fields = ('name', 'supplier', 'release_supplier')
