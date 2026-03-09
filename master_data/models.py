from django.db import models


# ──────────────────────────────────────────────
# 공용 기준정보 (Master Data)
# 여러 앱(AS관리, 툴입출고, 납품 등)에서 공유하는 기준 모델
# ──────────────────────────────────────────────


class CompanyCategory(models.Model):
    """단가 그룹 - 견적서 금액 구분용 (예: A등급, B등급, 특별단가 등)"""

    name = models.CharField("단가 그룹명", max_length=100, unique=True)

    class Meta:
        db_table = "as_app_companycategory"
        verbose_name = "단가 그룹"
        verbose_name_plural = "단가 그룹"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Company(models.Model):
    """매출처 관리 - AS 매출 거래처"""

    name = models.CharField("업체명", max_length=200)
    business_number = models.CharField(
        "사업자등록번호",
        max_length=20,
        help_text="예: 123-45-67890",
    )
    representative = models.CharField(
        "대표자명",
        max_length=100,
    )
    address = models.TextField("주소")
    price_group = models.ForeignKey(
        CompanyCategory,
        on_delete=models.SET_NULL,
        verbose_name="단가 그룹",
        related_name="companies",
        null=True,
        blank=True,
        help_text="견적서 금액이 다르게 적용되는 그룹",
    )

    class Meta:
        db_table = "as_app_company"
        verbose_name = "매출처"
        verbose_name_plural = "매출처 관리"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Brand(models.Model):
    """브랜드 관리"""

    name = models.CharField("브랜드명", max_length=200, unique=True)

    class Meta:
        db_table = "as_app_brand"
        verbose_name = "브랜드"
        verbose_name_plural = "브랜드 관리"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tool(models.Model):
    """장비/툴 관리"""

    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        verbose_name="브랜드",
        related_name="tools",
    )
    model_name = models.CharField("모델명", max_length=200)

    class Meta:
        db_table = "as_app_tool"
        verbose_name = "장비/툴"
        verbose_name_plural = "브랜드 & 툴 관리"
        ordering = ["brand__name", "model_name"]
        unique_together = ["brand", "model_name"]

    def __str__(self):
        return f"{self.brand.name} > {self.model_name}"


class OutsourceCompany(models.Model):
    """의뢰업체 - AS 수리를 외주 의뢰하는 업체"""

    name = models.CharField("의뢰업체명", max_length=200, unique=True)
    contact = models.CharField("연락처", max_length=100, blank=True)
    memo = models.TextField("메모", blank=True)

    class Meta:
        db_table = "as_app_outsourcecompany"
        verbose_name = "의뢰업체"
        verbose_name_plural = "의뢰업체 관리"
        ordering = ["name"]

    def __str__(self):
        return self.name
