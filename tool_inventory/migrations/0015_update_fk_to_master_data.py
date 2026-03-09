"""
tool_inventory 0015 — FK 참조를 as_app에서 master_data로 변경.

DB에는 아무 변경도 하지 않습니다.
Django ORM state에서 FK 대상을 master_data의 모델로 업데이트합니다.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tool_inventory", "0014_protect_inventory_batch_fk"),
        ("master_data", "0001_initial"),
        ("as_app", "0027_move_master_data"),
    ]

    operations = [
        # InventoryBatch.supplier: as_app.OutsourceCompany → master_data.OutsourceCompany
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="inventorybatch",
                    name="supplier",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="inbound_batches",
                        to="master_data.outsourcecompany",
                        verbose_name="입고업체",
                    ),
                ),
            ],
        ),
        # OutboundBatch.release_company: as_app.Company → master_data.Company
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="outboundbatch",
                    name="release_company",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="tool_outbound_batches",
                        to="master_data.company",
                        verbose_name="출고업체",
                    ),
                ),
            ],
        ),
        # OutboundTicket.tool: as_app.Tool → master_data.Tool
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="outboundticket",
                    name="tool",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="master_data.tool",
                        verbose_name="품목",
                    ),
                ),
            ],
        ),
        # Inventory.supplier: as_app.OutsourceCompany → master_data.OutsourceCompany
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="inventory",
                    name="supplier",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="master_data.outsourcecompany",
                        verbose_name="입고처",
                    ),
                ),
            ],
        ),
        # Inventory.tool: as_app.Tool → master_data.Tool
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="inventory",
                    name="tool",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="master_data.tool",
                        verbose_name="품목명",
                    ),
                ),
            ],
        ),
        # Inventory.release_company: as_app.Company → master_data.Company
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="inventory",
                    name="release_company",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="master_data.company",
                        verbose_name="출고처",
                    ),
                ),
            ],
        ),
        # ToolStockSummary: 프록시 모델의 부모를 master_data.Tool로 변경
        # DeleteModel + CreateModel로 재생성 (state only)
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name="ToolStockSummary"),
                migrations.CreateModel(
                    name="ToolStockSummary",
                    fields=[],
                    options={
                        "proxy": True,
                        "verbose_name": "재고 현황",
                        "verbose_name_plural": "재고 현황",
                    },
                    bases=("master_data.tool",),
                ),
            ],
        ),
    ]
