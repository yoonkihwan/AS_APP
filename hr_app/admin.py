from django.contrib import admin
from unfold.sites import UnfoldAdminSite

class HRAdminSite(UnfoldAdminSite):
    site_title = "근무/근태 관리"
    site_header = "근무 관리 포털"
    index_title = "근무/근태 관리 대시보드"
    index_template = "hr_app/calendar.html"

hr_admin_site = HRAdminSite(name="hr_admin")

from .models import AttendanceRecord
from unfold.admin import ModelAdmin

@admin.register(AttendanceRecord, site=hr_admin_site)
class AttendanceRecordAdmin(ModelAdmin):
    list_display = ["date", "user", "work_type", "overtime_hours", "memo"]
    list_filter = ["work_type", "user", "date"]
    search_fields = ["user__username", "memo"]
    date_hierarchy = "date"

