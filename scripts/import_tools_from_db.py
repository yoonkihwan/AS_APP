import os
import sys
import django

# Setup Django
sys.path.append(r"c:\Users\rlao1\AS_APP")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'as_project.settings')
django.setup()

from master_data.models import Brand, Tool

BRAND_MAPPING = {
    "CLECO (클레코)": [
        "48EAE41AM3", "18ESE17Q", "48ESE36D3", "48ESE90D4", "48EAE135MH4", "48EAE90AH4",
        "MPRO400GCD-P", "MPRO300GCD", "30ESN12EAQ", "50ESN43GD3", "50EAN39GA3", "30EAN12EA3",
        "50EAN80JA4", "DC CABLE (신형 일자)", "DC CABLE (신형 앵글)", "DC CABLE (중신형)"
    ],
    "ESTIC (에스틱)": [
        "MDT4006-A", "MDT4024-Q 3/8", "MDT4027-Q 3/8", "MDT4045Q 1/2", "MDTC-90",
        "MDTH4011", "MDTH4036", "CB-MDT05-5M", "MDT-25P-3M-OPEN"
    ],
    "YOKOTA (요코타)": [
        "YLA-80A", "YETC-230ER-HL", "YET-2001C-E", "YTT-750"
    ],
    "TOKU (토쿠)": [
        "TKA-60", "TKA-90", "TKA-111"
    ],
    "DELVO (델보)": [
        "DLV45A06L-AF"
    ],
    "GESIPA (게시파)": [
        "TAURUS2"
    ],
    "STANLEY (스탠리)": [
        "SC7E (L)"
    ],
    "URYU (유류)": [
        "M2-6CAW-N"
    ],
    "기타 / 공용": [
        "해체툴", "락볼트", "락볼트 컨트롤러", "리벳 컨트롤러", "포지션 컨트롤러",
        "SYSTEM CABLE (10M)", "SYSTEM CABLE (15M)", "961560-060 (네오텍 일자 케이블)"
    ]
}

def run_import():
    total_brands = 0
    total_tools = 0
    for brand_name, tools in BRAND_MAPPING.items():
        brand, b_created = Brand.objects.get_or_create(name=brand_name)
        if b_created:
            total_brands += 1
        for model in tools:
            _, t_created = Tool.objects.get_or_create(brand=brand, model_name=model)
            if t_created:
                total_tools += 1
    print(f"동기화 완료: 브랜드 {Brand.objects.count()}개, 툴 {Tool.objects.count()}개 등록됨 (신규: 브랜드 {total_brands}개, 툴 {total_tools}개)")

if __name__ == "__main__":
    run_import()
