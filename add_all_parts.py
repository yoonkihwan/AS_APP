import os
import django
import sys

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'as_project.settings')
django.setup()

from as_app.models import Part

md_file = r'c:\Users\rlao1\AS_APP\수리견적서 부품정리.md'

added_count = 0
skipped_count = 0

try:
    with open(md_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        if line.startswith('|') and not line.startswith('| 부품명') and not line.startswith('| ---'):
            cols = [col.strip() for col in line.split('|')]
            if len(cols) >= 4:
                name = cols[1]
                code = cols[2].replace('`', '')
                price_str = cols[3].replace(',', '')
                
                try:
                    price = int(price_str)
                except ValueError:
                    price = 0
                    
                # Skip invalid lines
                if not name or price == 0:
                    continue
                
                part, created = Part.objects.get_or_create(
                    code=code,
                    defaults={'name': name, 'price': price, 'part_type': Part.PartType.COMMON}
                )
                
                if created:
                    added_count += 1
                    print(f"✅ 추가 완료: {name} (코드: {code}, 단가: {price:,}원)")
                else:
                    skipped_count += 1
                    print(f"⏩ 이미 존재함 (건너뜀): {name} (코드: {code})")

    print(f"\n✨ 완료! 총 {added_count}개의 새로운 부품이 추가되었고, {skipped_count}개의 중복 부품은 건너뛰었습니다.")

except Exception as e:
    print("Error:", e)
