import os
import django
import random
from datetime import timedelta, date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'as_project.settings')
django.setup()

from as_app.models import ASTicket, Company, Tool, Part, OutsourceCompany

def main():
    companies = list(Company.objects.all())
    tools = list(Tool.objects.all())
    parts = list(Part.objects.all())
    outsource_companies = list(OutsourceCompany.objects.all())

    if not companies or not tools:
        print("Error: 기준정보(Company, Tool)가 부족합니다. 먼저 기준정보를 등록해주세요.")
        return

    statuses = [ASTicket.Status.INBOUND, ASTicket.Status.REPAIRED, ASTicket.Status.SHIPPED, ASTicket.Status.DISPOSED]

    symptoms = [
        "전원 안켜짐", "소음 발생", "정상 작동 안함", "정기 점검", "모터 고장", 
        "발열 심함", "센서 오작동", "케이블 단선", "외관 파손", "통신 불량",
        "액정 파손", "버튼 눌림 불량", "배터리 방전 진단", "접촉 불량", "오류 코드 발생"
    ]

    repair_contents = [
        "보드 교체", "모터 수리", "케이블 재연결", "내부 청소 및 윤활제 도포", "센서 교체",
        "외장 케이스 교체", "펌웨어 업데이트", "부품 교체 후 정상 작동 확인", "점검 결과 이상 없음",
        "소모품 교환", "단자부 재납땜", "기판 세척"
    ]

    managers = ["김철수", "이영희", "박지성", "최동원", "홍길동", "손흥민", "김민재", ""]

    def generate_random_sn():
        return f"SN-{random.randint(10000, 99999)}-{random.randint(100, 999)}"

    created_count = 0
    for i in range(50):
        company = random.choice(companies)
        tool = random.choice(tools)
        
        days_ago = random.randint(0, 180)
        inbound_date = date.today() - timedelta(days=days_ago)
        
        status = random.choice(statuses)
        
        # 중복 SN 방지 (clean() 메서드 검증 회피)
        while True:
            sn = generate_random_sn()
            if not ASTicket.objects.filter(tool=tool, serial_number=sn, status__in=[ASTicket.Status.INBOUND, ASTicket.Status.REPAIRED]).exists():
                break

        ticket = ASTicket(
            inbound_date=inbound_date,
            company=company,
            manager=random.choice(managers),
            tool=tool,
            serial_number=sn,
            symptom=random.choice(symptoms),
            status=status,
        )
        
        if status in [ASTicket.Status.REPAIRED, ASTicket.Status.SHIPPED]:
            ticket.repair_content = random.choice(repair_contents)
            if status == ASTicket.Status.SHIPPED:
                outbound_days = random.randint(0, 30)
                ticket.outbound_date = inbound_date + timedelta(days=outbound_days)
                if ticket.outbound_date > date.today():
                    ticket.outbound_date = date.today()
        
        ticket.save()
        
        # 랜덤 부품 추가 (0~3개)
        num_parts = random.randint(0, 3)
        if num_parts > 0 and parts:
            selected_parts = random.sample(parts, min(num_parts, len(parts)))
            ticket.used_parts.set(selected_parts)
            ticket.repair_cost = sum(p.price for p in selected_parts)
            ticket.save()
            
        created_count += 1
        print(f"[{created_count}/50] Created ticket for {company.name} - {tool.model_name}")

    print(f"성공적으로 {created_count}개의 AS 이력 더미데이터를 생성했습니다.")

if __name__ == '__main__':
    main()
