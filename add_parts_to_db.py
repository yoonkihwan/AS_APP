import os
import django
import sys

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'as_project.settings')
django.setup()

from as_app.models import Part

parts_to_add = [
    ("Vacuum Ejection", "07640-00240", 508000),
    ("One Touch Coupler(M)", "TBC384M(S)", 50400),
    ("Adaptor", "07265-03802", 50000),
    ("Anvil", "07200-03501(A)", 432000),
    ("Jaw Housing", "07200-02201(A)", 133200),
    ("Jaws", "07220-02302", 57000),
    ("Spring Guide(F)", "07220-02104", 36000),
    ("Spring Guide(R)", "07220-02104(A)", 36000),
    ('"O"ring', "07267-01015", 3900)
]

added_count = 0
for name, code, price in parts_to_add:
    # First, check if the part exists by code, if code exists
    # Or fallback to name if code is empty but here they all have codes.
    part, created = Part.objects.get_or_create(
        code=code,
        defaults={'name': name, 'price': price, 'part_type': Part.PartType.COMMON}
    )
    if created:
        added_count += 1
        print(f"✅ 추가 완료: {name} (코드: {code}, 단가: {price:,}원)")
    else:
        # If part exists but price is different, update it? 
        # For now, just print it exists.
        print(f"⚠️ 이미 존재함: {name} (코드: {code})")

print(f"\n총 {added_count}개의 부품이 수리부품 관리(DB)에 성공적으로 추가되었습니다.")
