from unfold.sites import UnfoldAdminSite
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm as UnfoldUserChangeForm, UserCreationForm
from django.contrib import admin, messages
from unfold.decorators import action, display
from django.utils.html import format_html
from django.urls import reverse


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
        return super().get_queryset(request).select_related("content_type")

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
    form = UnfoldUserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = (
        "username",
        "display_name",
        "display_role",
        "is_active",
        "display_last_login",
    )
    list_filter = ("is_superuser", "is_active")
    search_fields = ("username", "first_name", "last_name", "email")
    actions_list = ["approve_as_worker", "promote_to_admin"]
    inlines = [LogEntryInline]

    # ── 역할 표시 컬럼 ──
    @display(description="역할")
    def display_role(self, obj):
        if obj.is_superuser:
            return format_html(
                '<span style="color:#f59e0b;font-weight:600;">🛡️ 관리자</span>'
            )
        elif obj.is_staff and obj.is_active:
            return format_html(
                '<span style="color:#3b82f6;font-weight:600;">🔧 작업자</span>'
            )
        elif not obj.is_active:
            return format_html(
                '<span style="color:#94a3b8;font-weight:600;">⏳ 미승인</span>'
            )
        return format_html(
            '<span style="color:#94a3b8;">—</span>'
        )

    @display(description="이름")
    def display_name(self, obj):
        name = obj.get_full_name()
        return name if name.strip() else "-"

    @display(description="최근 로그인")
    def display_last_login(self, obj):
        if obj.last_login:
            return obj.last_login.strftime("%Y-%m-%d %H:%M")
        return format_html('<span style="color:#94a3b8;">-</span>')

    # ── fieldsets 단순화: groups/user_permissions 숨김 ──
    def get_fieldsets(self, request, obj=None):
        if not obj:
            # 신규 사용자 생성 폼
            return (
                (None, {"fields": ("username", "password1", "password2")}),
            )

        return (
            (None, {"fields": ("username", "password")}),
            ("개인정보", {"fields": ("first_name", "last_name", "email")}),
            (
                "권한 설정",
                {
                    "fields": ("is_active", "is_staff", "is_superuser"),
                    "description": "관리자: is_superuser ✅ / 작업자: is_staff ✅ + is_active ✅",
                },
            ),
            ("중요 일자", {"fields": ("last_login", "date_joined")}),
        )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("last_login", "date_joined")
        return ()

    # ── 작업자 승인 (일괄 액션) ──
    @action(description="선택 사용자: 작업자로 승인")
    def approve_as_worker(self, request, queryset):
        """미승인 사용자를 작업자로 승인합니다. is_active=True, is_staff=True 설정."""
        count = 0
        for user in queryset:
            user.is_active = True
            user.is_staff = True
            user.save()
            count += 1
        messages.success(
            request,
            f"{count}명의 사용자를 작업자로 승인했습니다.",
        )

    # ── 관리자로 승격 (일괄 액션) ──
    @action(description="선택 사용자: 관리자로 승격")
    def promote_to_admin(self, request, queryset):
        """선택한 사용자를 관리자(superuser)로 승격합니다."""
        count = 0
        for user in queryset:
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            user.save()
            count += 1
        messages.success(
            request,
            f"{count}명의 사용자를 관리자로 승격했습니다.",
        )




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


# ── Sysadmin 사이트 (관리자 전용) ──
class SysadminSite(UnfoldAdminSite):
    site_title = "시스템 사용자 관리"
    site_header = "계정 가입 및 권한 승인"
    site_url = None
    index_title = "계정/권한 설정"

    def has_permission(self, request):
        """관리자(superuser)만 시스템 관리 사이트에 접근 가능"""
        return request.user.is_active and request.user.is_superuser

    def index(self, request, extra_context=None):
        return redirect("sysadmin:auth_user_changelist")


sysadmin_site = SysadminSite(name="sysadmin")
sysadmin_site.register(User, UserAdmin)
sysadmin_site.register(LogEntry, LogEntryAdmin)
