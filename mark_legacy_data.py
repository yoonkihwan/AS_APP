"""
기존 입출고 데이터를 is_legacy=True로 일괄 설정하는 스크립트.

실행 방법:
  python mark_legacy_data.py

주의:
  - migrate(0017_add_is_legacy_flag) 완료 후 실행해야 합니다.
  - 이 스크립트 실행 이후 추가되는 데이터는 is_legacy=False(기본값)로 저장됩니다.
  - 실행 전 DB 백업을 권장합니다.
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'as_project.settings')
django.setup()

from tool_inventory.models import Inventory, InventoryBatch, OutboundBatch

def run():
    print("=" * 60)
    print("기존 데이터 is_legacy=True 일괄 설정 시작")
    print("=" * 60)

    # --- Inventory 전체를 is_legacy=True로 설정 ---
    total_inv = Inventory.all_objects.filter(is_legacy=False).count()
    print(f"\n[1] Inventory 레코드: {total_inv}건을 is_legacy=True로 변경합니다...")
    updated_inv = Inventory.all_objects.filter(is_legacy=False).update(is_legacy=True)
    print(f"    ✅ {updated_inv}건 완료")

    # --- InventoryBatch 전체를 is_legacy=True로 설정 ---
    total_batch = InventoryBatch.objects.filter(is_legacy=False).count()
    print(f"\n[2] InventoryBatch 레코드: {total_batch}건을 is_legacy=True로 변경합니다...")
    updated_batch = InventoryBatch.objects.filter(is_legacy=False).update(is_legacy=True)
    print(f"    ✅ {updated_batch}건 완료")

    # --- OutboundBatch 전체를 is_legacy=True로 설정 ---
    total_obatch = OutboundBatch.objects.filter(is_legacy=False).count()
    print(f"\n[3] OutboundBatch 레코드: {total_obatch}건을 is_legacy=True로 변경합니다...")
    updated_obatch = OutboundBatch.objects.filter(is_legacy=False).update(is_legacy=True)
    print(f"    ✅ {updated_obatch}건 완료")

    # --- 결과 확인 ---
    print("\n" + "=" * 60)
    print("완료 후 상태 확인")
    print("=" * 60)
    legacy_count = Inventory.all_objects.filter(is_legacy=True).count()
    new_count = Inventory.all_objects.filter(is_legacy=False).count()
    print(f"  레거시(구) 데이터 (is_legacy=True): {legacy_count}건")
    print(f"  신규 데이터    (is_legacy=False): {new_count}건")
    print("\n이제 서버를 재시작하면 사이드바에 '툴 입출고 관리(구)' 메뉴가 나타납니다.")
    print("이후 추가되는 입고/출고 데이터는 자동으로 신규 데이터로 분류됩니다.")
    print("=" * 60)

if __name__ == '__main__':
    run()
