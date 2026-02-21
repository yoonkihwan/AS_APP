import re

with open('as_app/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

mixin_code = '''
class StatusColorMixin:
    """행 전체에 상태별 배경색을 적용하기 위해 HTML 마커를 삽입하는 믹스인"""
    @display(description="상태")
    def display_status(self, obj):
        return format_html(
            '<span class="status-marker" data-status="{}">{}</span>',
            obj.status,
            obj.get_status_display(),
        )
'''

# 1. Insert mixin after CustomTitleMixin
content = content.replace('class CustomTitleMixin:', mixin_code + '\nclass CustomTitleMixin:')

# 2. Inherit StatusColorMixin in the relevant admins
admins = ['InboundTicketAdmin', 'RepairTicketAdmin', 'OutboundTicketAdmin', 'ASHistoryAdmin', 'EstimateTicketAdmin']

for admin_cls in admins:
    if f"class {admin_cls}(ModelAdmin):" in content:
        content = content.replace(f"class {admin_cls}(ModelAdmin):", f"class {admin_cls}(StatusColorMixin, ModelAdmin):")
    elif f"class {admin_cls}(CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):" in content:
        content = content.replace(f"class {admin_cls}(CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):", f"class {admin_cls}(StatusColorMixin, CustomTitleMixin, NoRelatedButtonsMixin, ModelAdmin):")

# 3. Add "display_status" to list_display of RepairTicketAdmin and OutboundTicketAdmin, and Estimate if not there (Estimate has it)
def add_to_list_display(cls_name, new_val, txt):
    # Find the list_display array inside the class
    class_idx = txt.find(f"class {cls_name}")
    if class_idx == -1: return txt
    ld_start = txt.find("list_display = [", class_idx)
    if ld_start == -1: return txt
    ld_end = txt.find("]", ld_start)
    ld_content = txt[ld_start:ld_end]
    if new_val not in ld_content:
        # Insert at the beginning of list
        txt = txt[:ld_start+16] + f'\n        "{new_val}",' + txt[ld_start+16:]
    return txt

content = add_to_list_display('RepairTicketAdmin', 'display_status', content)
content = add_to_list_display('OutboundTicketAdmin', 'display_status', content)


# 4. Remove existing display_status defined inside these classes
# Regex to remove display_status definition (which may have @display decorator)
# Pattern: \s+@display\([^)]*\)\s+def display_status\(self, obj\):[\s\S]*?(?=\s+def |\s+@|\s+class |\Z)
pattern = r'\s+@display\([^)]*\)\s+def display_status\(self, obj\):(?:(?!\n\s+(?:def |@|class ))[\s\S])*'
content = re.sub(pattern, '', content)


# 5. Make sure row_colors.css is in the Media class
media_css_patterns = [
    # Match css = {"all": (...)} blocks
    (r'(class\s+(?:' + '|'.join(admins) + r')\b[\s\S]*?class Media:[\s\S]*?css\s*=\s*\{"all":\s*\()((?:[^)]*))(\)\})', r'\1\2, "as_app/css/row_colors.css"\3')
]

for admin_cls in admins:
    admin_block_re = re.compile(rf'(class {admin_cls}\b.*?(?=\nclass [A-Z]|\Z))', re.DOTALL)
    match = admin_block_re.search(content)
    if match:
        block = match.group(1)
        if 'class Media:' not in block:
            # Add Media class
            new_block = block.rstrip() + '''
    class Media:
        css = {"all": ("as_app/css/row_colors.css",)}
'''
        else:
            if '"as_app/css/row_colors.css"' not in block and "'as_app/css/row_colors.css'" not in block:
                # Append to existing 'all' tuple
                new_block = re.sub(r'(css\s*=\s*\{\s*"all"\s*:\s*\()([^)]*)(\)\s*\})', r'\1\2, "as_app/css/row_colors.css"\3', block)
            else:
                new_block = block
        content = content.replace(block, new_block)

# Clean up possible duplicated commas in Media tuple
content = content.replace(', "as_app/css/row_colors.css", "as_app/css/row_colors.css"', ', "as_app/css/row_colors.css"')
content = content.replace('", ,', '",')

with open('as_app/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("StatusColorMixin applied successfully!")
