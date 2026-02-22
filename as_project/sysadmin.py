from unfold.sites import UnfoldAdminSite
from django.shortcuts import redirect
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm as UnfoldUserChangeForm, UserCreationForm
from django import forms
from django.contrib import messages
from unfold.decorators import action

class CustomUserChangeForm(UnfoldUserChangeForm):
    grant_general_perms = forms.BooleanField(
        label="일반 업무 권한 일괄 추가",
        required=False,
        help_text="⭐ 체크하고 저장하면 이 사용자가 시스템 관리 권한(최상위 권한등) 없이도 'AS 관리'와 '장비 입출고'의 모든 기능을 사용할 수 있습니다."
    )

class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = CustomUserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    # list_display를 커스텀해서 가입 승인(staff status, active)등이 잘 보이도록.
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    actions_list = ["grant_as_inventory_perms"]

    def get_fieldsets(self, request, obj=None):
        base_fs = super().get_fieldsets(request, obj)
        if not obj:
            return base_fs
            
        new_fs = []
        for name, opts in base_fs:
            new_opts = opts.copy()
            fields = new_opts.get('fields', [])
            if 'is_active' in fields and 'grant_general_perms' not in fields:
                new_fields = list(fields)
                if 'is_superuser' in new_fields:
                    idx = new_fields.index('is_superuser') + 1
                    new_fields.insert(idx, 'grant_general_perms')
                else:
                    new_fields.append('grant_general_perms')
                new_opts['fields'] = tuple(new_fields)
            new_fs.append((name, new_opts))
        return tuple(new_fs)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if getattr(form, 'cleaned_data', None) and form.cleaned_data.get('grant_general_perms'):
            perms = Permission.objects.filter(content_type__app_label__in=['as_app', 'tool_inventory'])
            obj.user_permissions.add(*perms)
            messages.success(request, f"{obj.username} 님에게 AS 관리 및 인벤토리 앱의 전체 권한이 일괄 부여되었습니다.")

    @action(description="선택 항목 일괄: 일반업무 권한 허용 (시스템 제외)")
    def grant_as_inventory_perms(self, request, queryset):
        perms = Permission.objects.filter(content_type__app_label__in=['as_app', 'tool_inventory'])
        count = 0
        for user in queryset:
            user.is_active = True
            user.is_staff = True
            user.user_permissions.add(*perms)
            user.save()
            count += 1
        messages.success(request, f"{count}명의 사용자에게 시스템 관리를 제외한 일반 시스템 전체 사용 권한을 부여했습니다.")

class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass

class SysadminSite(UnfoldAdminSite):
    site_title = "시스템 사용자 관리"
    site_header = "계정 가입 및 권한 승인"
    site_url = None
    index_title = "계정/권한 설정"

    def index(self, request, extra_context=None):
        return redirect('sysadmin:auth_user_changelist')

sysadmin_site = SysadminSite(name='sysadmin')
sysadmin_site.register(User, UserAdmin)
sysadmin_site.register(Group, GroupAdmin)
