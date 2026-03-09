"""
as_app 0027 — State-only: as_app에서 master_data로 이전된 모델 제거.

DB에는 아무 변경도 하지 않습니다. Django ORM state에서만
CompanyCategory, Company, Brand, Tool, OutsourceCompany를 as_app에서 제거합니다.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("as_app", "0026_remove_part_price"),
        ("master_data", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],  # DB에는 아무것도 하지 않음
            state_operations=[
                migrations.DeleteModel(name="CompanyCategory"),
                migrations.DeleteModel(name="Company"),
                migrations.DeleteModel(name="Brand"),
                migrations.DeleteModel(name="Tool"),
                migrations.DeleteModel(name="OutsourceCompany"),
            ],
        ),
    ]
