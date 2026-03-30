"""자동 수리완료 트리거 제거 스크립트"""
import re

filepath = r"c:\Users\rlao1\AS_APP\as_app\admin.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 자동 트리거 블록을 찾아서 교체
old_block = """        # 부품이 선택되어 있으면 자동으로 수리완료 상태로 변경
        if obj.ticket_used_parts.exists() and obj.status != ASTicket.Status.REPAIRED:
            if obj.status == ASTicket.Status.OUTSOURCED and obj.outsource_date and obj.outsource_company and obj.repair_content:
                import re
                today_str = timezone.localdate().strftime('%Y-%m-%d')
                pattern = rf\"{re.escape(obj.outsource_company.name)} 수리의뢰 \\({re.escape(obj.outsource_date.strftime('%Y-%m-%d'))}~\\)\"
                replacement = f\"{obj.outsource_company.name} 수리의뢰 ({obj.outsource_date.strftime('%Y-%m-%d')}~{today_str})\"
                obj.repair_content = re.sub(pattern, replacement, obj.repair_content)
                if \"repair_content\" not in update_fields:
                    update_fields.append(\"repair_content\")
                    
            obj.status = ASTicket.Status.REPAIRED
            update_fields.append(\"status\")
        if update_fields:
            obj.save(update_fields=update_fields)"""

new_block = """        # [V5 개편] 자동 수리완료 트리거 제거됨
        # 부품을 등록해도 상태는 변하지 않습니다.
        # 상태 변경은 '견적등록' 드롭다운 또는 '상태 등록' 일괄 액션으로만 가능합니다.
        if update_fields:
            obj.save(update_fields=update_fields)"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: 자동 트리거 제거 완료")
else:
    print("ERROR: 대상 블록을 찾지 못함")
    # 디버그: 핵심 문자열 존재 여부 확인
    print("  '자동으로 수리완료' in content:", "자동으로 수리완료" in content)
    print("  'ASTicket.Status.REPAIRED' in content:", "ASTicket.Status.REPAIRED" in content)
