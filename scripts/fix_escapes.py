"""이스케이핑 문제 수정 및 기타 문법 오류 정리"""
filepath = r"c:\Users\rlao1\AS_APP\as_app\admin.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# 1. format_html 내에서 escaped quote(\') -> 올바른 이스케이프
# Python 스크립트에서 삽입 시 \' 이중 이스케이프 문제 수정

# 2. 기타 PatternFix: \\n -> actual newline in f-strings for outsource action
old_escaped_newline = '''ticket.repair_content = f"{ticket.repair_content}\\\\n{remarks_text}"'''
new_escaped_newline = '''ticket.repair_content = f"{ticket.repair_content}\\n{remarks_text}"'''
while old_escaped_newline in content:
    content = content.replace(old_escaped_newline, new_escaped_newline)
    changes += 1

# 3. Fix strftime escape issue
old_strftime = """remarks_text = f"{company.name} 수리의뢰 ({outsource_date.strftime(\\'%Y-%m-%d\\')}~)\""""
new_strftime = """remarks_text = f"{company.name} 수리의뢰 ({outsource_date.strftime('%Y-%m-%d')}~)\""""
if old_strftime in content:
    content = content.replace(old_strftime, new_strftime)
    changes += 1

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Fixed {changes} escape issues")
