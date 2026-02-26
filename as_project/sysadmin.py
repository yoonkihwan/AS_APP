from unfold.sites import UnfoldAdminSite
from django.shortcuts import redirect
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm as UnfoldUserChangeForm, UserCreationForm
from django import forms
from django.contrib import admin, messages
from unfold.decorators import action, display
from django.utils.html import format_html
from django.urls import reverse


# ── 사용자 변경 폼 (일반 업무 권한 일괄 추가) ──
class CustomUserChangeForm(UnfoldUserChangeForm):
    grant_general_perms = forms.BooleanField(
        label="일반 업무 권한 일괄 추가",
        required=False,
        help_text="⭐ 체크하고 저장하면 'AS 관리', '장비 입출고', '근무/근태 관리'의 모든 기능을 사용할 수 있습니다.",
    )


# ── 활동 기록 인라인 (사용자 상세 페이지에서 표시) ──
class LogEntryInline(TabularInline):
    model = LogEntry
    fk_name = "user"
    extra = 0
    max_num = 0
    can_delete = False
    fields = ["action_time", "display_action", "display_target", "display_detail"]
    readonly_fields = ["action_time", "display_action", "display_target", "display_detail"]
    verbose_name = "활동 기록"
    verbose_name_plural = "최근 활동 기록 (최근 20건)"
    ordering = ["-action_time"]

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("content_type")[:20]

    @display(description="작업")
    def display_action(self, obj):
        action_map = {
            ADDITION: ("➕ 추가", "#10b981"),
            CHANGE: ("✏️ 수정", "#3b82f6"),
            DELETION: ("🗑️ 삭제", "#ef4444"),
        }
        text, color = action_map.get(obj.action_flag, ("❓ 기타", "#94a3b8"))
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, text,
        )

    @display(description="대상")
    def display_target(self, obj):
        ct = obj.content_type
        model_name = ct.name if ct else "알 수 없음"
        return format_html(
            '<span style="color:#94a3b8;">[{}]</span> <strong>{}</strong>',
            model_name,
            obj.object_repr or "-",
        )

    @display(description="변경 내용")
    def display_detail(self, obj):
        msg = obj.get_change_message() or "-"
        if len(msg) > 80:
            msg = msg[:80] + "…"
        return msg


# ── 사용자 관리 Admin ──
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = CustomUserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = (
        "username",
        "display_name",
        "is_staff",
        "is_active",
        "is_superuser",
        "display_last_login",
    )
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("username", "first_name", "last_name", "email")
    actions_list = ["grant_as_inventory_perms"]
    inlines = [LogEntryInline]

    @display(description="이름")
    def display_name(self, obj):
        name = obj.get_full_name()
        return name if name.strip() else "-"

    @display(description="최근 로그인")
    def display_last_login(self, obj):
        if obj.last_login:
            return obj.last_login.strftime("%Y-%m-%d %H:%M")
        return format_html('<span style="color:#94a3b8;">-</span>')

    def get_fieldsets(self, request, obj=None):
        base_fs = super().get_fieldsets(request, obj)
        if not obj:
            return base_fs

        new_fs = []
        for name, opts in base_fs:
            new_opts = opts.copy()
            fields = new_opts.get("fields", [])
            if "is_active" in fields and "grant_general_perms" not in fields:
                new_fields = list(fields)
                if "is_superuser" in new_fields:
                    idx = new_fields.index("is_superuser") + 1
                    new_fields.insert(idx, "grant_general_perms")
                else:
                    new_fields.append("grant_general_perms")
                new_opts["fields"] = tuple(new_fields)
            new_fs.append((name, new_opts))
        return tuple(new_fs)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if getattr(form, "cleaned_data", None) and form.cleaned_data.get(
            "grant_general_perms"
        ):
            perms = Permission.objects.filter(
                content_type__app_label__in=["as_app", "tool_inventory", "hr_app"]
            )
            obj.user_permissions.add(*perms)
            messages.success(
                request,
                f"{obj.username} 님에게 AS 관리, 장비 입출고, 근무/근태 관리의 전체 권한이 일괄 부여되었습니다.",
            )

    @action(description="선택 항목 일괄: 일반업무 권한 허용 (시스템 제외)")
    def grant_as_inventory_perms(self, request, queryset):
        perms = Permission.objects.filter(
            content_type__app_label__in=["as_app", "tool_inventory", "hr_app"]
        )
        count = 0
        for user in queryset:
            user.is_active = True
            user.is_staff = True
            user.user_permissions.add(*perms)
            user.save()
            count += 1
        messages.success(
            request,
            f"{count}명의 사용자에게 시스템 관리를 제외한 전체 업무 권한을 부여했습니다.",
        )


# ── 권한 그룹 Admin ──
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


# ── 활동 기록 전체 조회 Admin (읽기 전용) ──
class LogEntryAdmin(ModelAdmin):
    list_display = (
        "action_time",
        "display_user",
        "display_action",
        "display_target",
        "display_detail",
    )
    list_filter = ("action_flag", "content_type", "user")
    search_fields = ("object_repr", "change_message", "user__username")
    list_per_page = 30
    date_hierarchy = "action_time"

    class Media:
        css = {"all": ("as_app/css/row_colors.css",)}

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @display(description="사용자")
    def display_user(self, obj):
        user = obj.user
        name = user.get_full_name() or user.username
        return format_html("<strong>{}</strong>", name)

    @display(description="작업 유형")
    def display_action(self, obj):
        action_map = {
            ADDITION: ("➕ 추가", "#10b981"),
            CHANGE: ("✏️ 수정", "#3b82f6"),
            DELETION: ("🗑️ 삭제", "#ef4444"),
        }
        text, color = action_map.get(obj.action_flag, ("❓ 기타", "#94a3b8"))
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, text,
        )

    @display(description="대상")
    def display_target(self, obj):
        ct = obj.content_type
        model_name = ct.name if ct else "알 수 없음"
        return format_html(
            '<span style="color:#94a3b8;">[{}]</span> <strong>{}</strong>',
            model_name,
            obj.object_repr or "-",
        )

    @display(description="변경 내용")
    def display_detail(self, obj):
        msg = obj.get_change_message() or "-"
        if len(msg) > 100:
            msg = msg[:100] + "…"
        return msg


# ── Sysadmin 사이트 ──
class SysadminSite(UnfoldAdminSite):
    site_title = "시스템 사용자 관리"
    site_header = "계정 가입 및 권한 승인"
    site_url = None
    index_title = "계정/권한 설정"

    def index(self, request, extra_context=None):
        return redirect("sysadmin:auth_user_changelist")


sysadmin_site = SysadminSite(name="sysadmin")
sysadmin_site.register(User, UserAdmin)
sysadmin_site.register(Group, GroupAdmin)
sysadmin_site.register(LogEntry, LogEntryAdmin)
