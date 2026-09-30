from django.db import migrations, models


class Migration(migrations.Migration):
    """
    is_legacy 필드를 Inventory, InventoryBatch, OutboundBatch에 추가.
    - 기존 모든 레코드의 기본값은 False (신규 데이터로 간주)
    - 이후 별도 데이터 마이그레이션 스크립트로 기존 데이터를 True로 일괄 변경 예정
    - LegacyInventory Proxy 모델은 별도 DB 변경 없음 (proxy=True)
    """
    dependencies = [
        ('tool_inventory', '0016_alter_inventory_options_and_more'),
    ]

    operations = [
        # InventoryBatch에 is_legacy 추가
        migrations.AddField(
            model_name='inventorybatch',
            name='is_legacy',
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text='True이면 레거시(구) 데이터로 분류되어 별도 메뉴에서 조회됩니다.',
                verbose_name='구 데이터 여부',
            ),
        ),
        # OutboundBatch에 is_legacy 추가
        migrations.AddField(
            model_name='outboundbatch',
            name='is_legacy',
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text='True이면 레거시(구) 데이터로 분류됩니다.',
                verbose_name='구 데이터 여부',
            ),
        ),
        # Inventory에 is_legacy 추가
        migrations.AddField(
            model_name='inventory',
            name='is_legacy',
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text="True이면 레거시(구) 데이터로 분류되어 '툴 입출고 관리(구)' 메뉴에서 조회됩니다.",
                verbose_name='구 데이터 여부',
            ),
        ),
        # LegacyInventory Proxy 모델 등록 (DB 변경 없음)
        migrations.CreateModel(
            name='LegacyInventory',
            fields=[],
            options={
                'verbose_name': '통합 입출고 이력(구)',
                'verbose_name_plural': '통합 입출고 이력(구)',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('tool_inventory.inventory',),
        ),
    ]
