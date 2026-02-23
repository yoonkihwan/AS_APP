"""
URL configuration for as_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from as_app import views as as_views
from as_project import views as as_project_views
from tool_inventory.admin import tool_admin_site
from as_project.sysadmin import sysadmin_site
from tool_inventory import views as tool_views
from hr_app.admin import hr_admin_site

urlpatterns = [
    path("", as_project_views.portal_view, name="portal_view"),
    # /admin/as_app/ 클릭 시 대시보드(메인)로 바로 리다이렉트
    path("admin/as_app/", RedirectView.as_view(url="/admin/", permanent=False)),
    path("admin/", admin.site.urls),
    path("inventory/", tool_admin_site.urls),
    path("sysadmin/", sysadmin_site.urls),
    path("hr/hr_app/calendar/", RedirectView.as_view(url="/hr/api/calendar/", permanent=False)), # temporary redirect
    path("hr/api/", include("hr_app.urls")), # API and custom views for HR
    path("hr/", hr_admin_site.urls),
    path("signup/", as_project_views.signup_view, name="signup_view"),
    path("api/tools-by-brand/", as_views.get_tools_by_brand, name="api_tools_by_brand"),
    path("api/inventory-by-tool/", tool_views.get_inventory_by_tool, name="api_inventory_by_tool"),
]

admin.site.site_header = "AS 관리"
admin.site.site_title = "AS 관리"
admin.site.index_title = "AS 관리"

