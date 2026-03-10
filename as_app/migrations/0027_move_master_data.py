"""
as_app 0027 — State-only: as_app에서 master_data로 이전된 모델 제거.

DB에는 아무 변경도 하지 않습니다. Django ORM state에서만
CompanyCategory, Company, Brand, Tool, OutsourceCompany를 as_app에서 제거합니다.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("as_app", "0026_remove_part_price"),
        ("master_data", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],  # DB에는 아무것도 하지 않음
            state_operations=[
                migrations.AlterField(
                    model_name="asticket",
                    name="company",
                    field=models.ForeignKey(
                        on_delete=models.deletion.PROTECT,
                        related_name="tickets",
                        to="master_data.company",
                        verbose_name="매출처",
                    ),
                ),
                migrations.AlterField(
                    model_name="asticket",
                    name="outsource_company",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="tickets",
                        to="master_data.outsourcecompany",
                        verbose_name="의뢰업체",
                    ),
                ),
                migrations.AlterField(
                    model_name="asticket",
                    name="tool",
                    field=models.ForeignKey(
                        on_delete=models.deletion.PROTECT,
                        related_name="tickets",
                        to="master_data.tool",
                        verbose_name="장비/툴",
                    ),
                ),
                migrations.AlterField(
                    model_name="inboundbatch",
                    name="company",
                    field=models.ForeignKey(
                        on_delete=models.deletion.PROTECT,
                        related_name="inbound_batches",
                        to="master_data.company",
                        verbose_name="매출처",
                    ),
                ),
                migrations.AlterField(
                    model_name="part",
                    name="brand",
                    field=models.ForeignKey(
                        on_delete=models.deletion.PROTECT,
                        related_name="parts",
                        to="master_data.brand",
                        verbose_name="브랜드",
                    ),
                ),
                migrations.AlterField(
                    model_name="part",
                    name="tools",
                    field=models.ManyToManyField(
                        blank=True,
                        help_text="이 부품이 사용되는 장비를 선택하세요. 공용 부품은 여러 장비를 선택할 수 있습니다.",
                        related_name="parts",
                        to="master_data.tool",
                        verbose_name="적용 장비/툴",
                    ),
                ),
                migrations.AlterField(
                    model_name="partprice",
                    name="category",
                    field=models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        to="master_data.companycategory",
                        verbose_name="단가 그룹",
                    ),
                ),
                migrations.AlterField(
                    model_name="repairpreset",
                    name="brand",
                    field=models.ForeignKey(
                        on_delete=models.deletion.PROTECT,
                        related_name="repair_presets",
                        to="master_data.brand",
                        verbose_name="브랜드",
                    ),
                ),
                migrations.AlterField(
                    model_name="repairpreset",
                    name="tools",
                    field=models.ManyToManyField(
                        blank=True,
                        help_text="이 세트가 적용되는 장비를 선택하세요. 비워두면 모든 장비에 표시됩니다.",
                        related_name="repair_presets",
                        to="master_data.tool",
                        verbose_name="적용 장비/툴",
                    ),
                ),
                migrations.DeleteModel(name="CompanyCategory"),
                migrations.DeleteModel(name="Company"),
                migrations.DeleteModel(name="Brand"),
                migrations.DeleteModel(name="Tool"),
                migrations.DeleteModel(name="OutsourceCompany"),
            ],
        ),
    ]
