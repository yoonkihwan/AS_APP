from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from unfold.admin import ModelAdmin
from unfold.sites import UnfoldAdminSite

from .models import Company, CompanyCategory, OutsourceCompany, Brand, Tool


# ──────────────────────────────────────────────
# Mixins (as_app/admin.py 와 동일)
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
# AdminSite
# ──────────────────────────────────────────────

class MasterDataAdminSite(UnfoldAdminSite):
    site_title = "기준정보 관리"
    site_header = "기준정보 관리"
    site_url = None
    index_title = "기준정보 관리"

    def index(self, request, extra_context=None):
        """대시보드 대신 매출처 목록으로 바로 리다이렉트"""
        return HttpResponseRedirect(
            reverse("master_data_admin:master_data_company_changelist")
        )

master_data_site = MasterDataAdminSite(name='master_data_admin')


# ──────────────────────────────────────────────
# 업체 관리 (매출처 / 의뢰업체 / 단가그룹)
# ──────────────────────────────────────────────

class MasterCompanyCategoryAdmin(CustomTitleMixin, ModelAdmin):
    custom_title = "단가그룹 관리"
    list_display = ["name"]
    search_fields = ["name"]
    change_list_template = "admin/master_data/companycategory/change_list.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["active_tab"] = "category"
        return super().changelist_view(request, extra_context)


class MasterCompanyAdmin(CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):
    custom_title = "업체관리"
    list_display = ["name", "business_number", "representative", "address", "price_group"]
    list_filter = ["price_group"]
    search_fields = ["name", "business_number", "representative"]
    list_per_page = 20
    change_list_template = "admin/master_data/company/change_list.html"

    fieldsets = (
        (
            "매출처 기본 정보",
            {
                "fields": (
                    "name",
                    "business_number",
                    "representative",
                ),
            },
        ),
        (
            "주소 및 기타",
            {
                "fields": (
                    "address",
                    "price_group",
                ),
            },
        ),
    )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["active_tab"] = "company"
        return super().changelist_view(request, extra_context)


class MasterOutsourceCompanyAdmin(ModelAdmin):
    """의뢰업체 관리"""
    list_display = ["name", "contact", "memo"]
    search_fields = ["name"]
    list_per_page = 20
    change_list_template = "admin/master_data/outsourcecompany/change_list.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["active_tab"] = "outsource"
        return super().changelist_view(request, extra_context)


# ──────────────────────────────────────────────
# 브랜드 + 툴 관리
# ──────────────────────────────────────────────

class MasterBrandAdmin(CustomTitleMixin, ModelAdmin):
    custom_title = "브랜드 관리"
    list_display = ["name"]
    search_fields = ["name"]
    change_list_template = "admin/master_data/brand/change_list.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["active_tab"] = "brand"
        return super().changelist_view(request, extra_context)

    def has_module_permission(self, request):
        """사이드바에 표시하지 않음 (Tool Admin에서 통합 관리)"""
        return False


class MasterToolAdmin(CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):
    custom_title = "장비/툴 관리"
    list_display = ["brand", "model_name"]
    list_filter = ["brand"]
    search_fields = ["model_name", "brand__name"]
    autocomplete_fields = ["brand"]
    list_per_page = 20
    change_list_template = "admin/master_data/tool/change_list.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["active_tab"] = "tool"
        return super().changelist_view(request, extra_context)


# ──────────────────────────────────────────────
# 모델 등록
# ──────────────────────────────────────────────

master_data_site.register(CompanyCategory, MasterCompanyCategoryAdmin)
master_data_site.register(Company, MasterCompanyAdmin)
master_data_site.register(OutsourceCompany, MasterOutsourceCompanyAdmin)
master_data_site.register(Brand, MasterBrandAdmin)
master_data_site.register(Tool, MasterToolAdmin)
