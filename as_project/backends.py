from django.contrib.auth.backends import ModelBackend


class StaffFullAccessBackend(ModelBackend):
    """
    작업자(is_staff) 이상의 사용자에게 모든 업무 권한을 자동 부여합니다.
    시스템 계정 관리(/sysadmin/) 접근은 SysadminSite.has_permission()에서
    별도로 is_superuser 체크하므로, 여기서는 단순히 is_staff만 확인합니다.

    이 백엔드를 통해 개별 Permission/Group 관리가 불필요해집니다.
    """

    def has_perm(self, user_obj, perm, obj=None):
        if not user_obj.is_active:
            return False
        # staff(작업자) 이상이면 모든 퍼미션 허용
        if user_obj.is_staff:
            return True
        return super().has_perm(user_obj, perm, obj)

    def has_module_perms(self, user_obj, app_label):
        if not user_obj.is_active:
            return False
        if user_obj.is_staff:
            return True
        return super().has_module_perms(user_obj, app_label)
