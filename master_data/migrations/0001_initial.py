"""
master_data 0001_initial — State-only migration.

이 마이그레이션은 DB에는 아무 변경도 하지 않습니다.
기존 as_app 테이블(as_app_company 등)을 그대로 사용하면서,
Django ORM state에서만 모델 소유권을 master_data 앱으로 이전합니다.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        # SeparateDatabaseAndState: DB 작업 없이 state만 변경
        migrations.SeparateDatabaseAndState(
            database_operations=[],  # DB에는 아무것도 하지 않음
            state_operations=[
                migrations.CreateModel(
                    name="CompanyCategory",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("name", models.CharField(max_length=100, unique=True, verbose_name="단가 그룹명")),
                    ],
                    options={
                        "verbose_name": "단가 그룹",
                        "verbose_name_plural": "단가 그룹",
                        "db_table": "as_app_companycategory",
                        "ordering": ["name"],
                    },
                ),
                migrations.CreateModel(
                    name="Company",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("name", models.CharField(max_length=200, verbose_name="업체명")),
                        ("business_number", models.CharField(help_text="예: 123-45-67890", max_length=20, verbose_name="사업자등록번호")),
                        ("representative", models.CharField(max_length=100, verbose_name="대표자명")),
                        ("address", models.TextField(verbose_name="주소")),
                        ("price_group", models.ForeignKey(
                            blank=True,
                            help_text="견적서 금액이 다르게 적용되는 그룹",
                            null=True,
                            on_delete=django.db.models.deletion.SET_NULL,
                            related_name="companies",
                            to="master_data.companycategory",
                            verbose_name="단가 그룹",
                        )),
                    ],
                    options={
                        "verbose_name": "매출처",
                        "verbose_name_plural": "매출처 관리",
                        "db_table": "as_app_company",
                        "ordering": ["name"],
                    },
                ),
                migrations.CreateModel(
                    name="Brand",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("name", models.CharField(max_length=200, unique=True, verbose_name="브랜드명")),
                    ],
                    options={
                        "verbose_name": "브랜드",
                        "verbose_name_plural": "브랜드 관리",
                        "db_table": "as_app_brand",
                        "ordering": ["name"],
                    },
                ),
                migrations.CreateModel(
                    name="Tool",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("model_name", models.CharField(max_length=200, verbose_name="모델명")),
                        ("brand", models.ForeignKey(
                            on_delete=django.db.models.deletion.PROTECT,
                            related_name="tools",
                            to="master_data.brand",
                            verbose_name="브랜드",
                        )),
                    ],
                    options={
                        "verbose_name": "장비/툴",
                        "verbose_name_plural": "브랜드 & 툴 관리",
                        "db_table": "as_app_tool",
                        "ordering": ["brand__name", "model_name"],
                        "unique_together": {("brand", "model_name")},
                    },
                ),
                migrations.CreateModel(
                    name="OutsourceCompany",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("name", models.CharField(max_length=200, unique=True, verbose_name="의뢰업체명")),
                        ("contact", models.CharField(blank=True, max_length=100, verbose_name="연락처")),
                        ("memo", models.TextField(blank=True, verbose_name="메모")),
                    ],
                    options={
                        "verbose_name": "의뢰업체",
                        "verbose_name_plural": "의뢰업체 관리",
                        "db_table": "as_app_outsourcecompany",
                        "ordering": ["name"],
                    },
                ),
            ],
        ),
    ]
