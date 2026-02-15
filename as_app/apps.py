from django.apps import AppConfig


class AsAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "as_app"
    verbose_name = "AS 관리 시스템"
