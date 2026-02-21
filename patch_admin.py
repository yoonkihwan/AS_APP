import re

with open('as_app/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

mixin_code = '''
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
        extra_context['title'] = f"{self.get_custom_title()} 추가/등록"
        return super().add_view(request, form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = f"{self.get_custom_title()} 상세/수정"
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

'''

# Inject mixin before the imports on line 25
if 'class CustomTitleMixin:' not in content:
    content = content.replace('from .models import (', mixin_code + 'from .models import (')

# Now we need to add the mixin to specific admins and set their custom_title
replacements = [
    (
        r'class CompanyAdmin\(NoRelatedButtonsMixin, ModelAdmin\):',
        r'class CompanyAdmin(CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):\n    custom_title = "업체관리"'
    ),
    (
        r'class ToolAdmin\(NoRelatedButtonsMixin, ModelAdmin\):',
        r'class ToolAdmin(CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):\n    custom_title = "브랜드 & 툴 관리"'
    ),
    (
        r'class PartAdmin\(NoRelatedButtonsMixin, ModelAdmin\):',
        r'class PartAdmin(CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):\n    custom_title = "수리부품 관리"'
    ),
    (
        r'class InboundBatchAdmin\(NoRelatedButtonsMixin, ModelAdmin\):',
        r'class InboundBatchAdmin(CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):\n    custom_title = "입고 등록"'
    ),
    (
        r'class RepairTicketAdmin\(NoRelatedButtonsMixin, ModelAdmin\):',
        r'class RepairTicketAdmin(CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):\n    custom_title = "수리 기록 등록"'
    ),
    (
        r'class OutboundTicketAdmin\(NoRelatedButtonsMixin, ModelAdmin\):',
        r'class OutboundTicketAdmin(CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):\n    custom_title = "출고 등록"'
    ),
    (
        r'class ASHistoryAdmin\(NoRelatedButtonsMixin, ModelAdmin\):',
        r'class ASHistoryAdmin(CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):\n    custom_title = "통합 이력"'
    ),
    (
        r'class EstimateTicketAdmin\(NoRelatedButtonsMixin, ModelAdmin\):',
        r'class EstimateTicketAdmin(CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):\n    custom_title = "견적서 발행"'
    ),
]

for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

with open('as_app/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Injected CustomTitleMixin and configured titles.")
