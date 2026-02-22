import uuid
from django.db import models

class Supplier(models.Model):
    """입고처 (매입처) 마스터 데이터"""
    name = models.CharField("입고처명", max_length=100, unique=True, primary_key=True)

    class Meta:
        verbose_name = "입고처"
        verbose_name_plural = "입고처 목록"
        ordering = ['name']

    def __str__(self):
        return self.name

class ReleaseSupplier(models.Model):
    """출고처 (현장) 마스터 데이터"""
    name = models.CharField("출고처명", max_length=100, unique=True, primary_key=True)

    class Meta:
        verbose_name = "출고처"
        verbose_name_plural = "출고처 목록"
        ordering = ['name']

    def __str__(self):
        return self.name

class ItemName(models.Model):
    """품목 이름 마스터 데이터"""
    name = models.CharField("품목명", max_length=200, unique=True, primary_key=True)

    class Meta:
        verbose_name = "품목명"
        verbose_name_plural = "품목 관리"
        ordering = ['name']

    def __str__(self):
        return self.name

class InventoryBatch(models.Model):
    """입고 배치 - 한 번에 여러 툴/장비를 입고 등록"""
    inbound_date = models.DateField("입고 날짜")
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        verbose_name="입고업체",
        related_name="inbound_batches",
        null=True,
    )
    as_supplier = models.ForeignKey(
        'as_app.OutsourceCompany',
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name="입고처(AS앱)",
    )
    manager = models.CharField("담당자/부서", max_length=100, blank=True)
    memo = models.TextField("메모", blank=True)
    created_at = models.DateTimeField("생성일", auto_now_add=True)

    class Meta:
        verbose_name = "입고 배치"
        verbose_name_plural = "입고 등록"
        ordering = ["-inbound_date", "-created_at"]

    def __str__(self):
        return f"{self.inbound_date} | {self.supplier.name} ({self.inventories.count()}건)"

class Inventory(models.Model):
    """메인 방비/툴 재고 리스트"""
    STATUS_CHOICES = [
        ('재고', '재고 (입고됨)'),
        ('출고', '출고 완료'),
    ]

    # 배치 정보 연동
    batch = models.ForeignKey(
        InventoryBatch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="입고 배치",
        related_name="inventories"
    )

    # 기본키는 기존 DB 데이터(UUID 형태의 문자열)를 그대로 담기 위해 맞춰줍니다.
    id = models.CharField(
        "관리 고유번호", 
        max_length=50, 
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.RESTRICT, 
        verbose_name="입고처",
        null=True,
    )
    as_supplier = models.ForeignKey(
        'as_app.OutsourceCompany',
        on_delete=models.PROTECT,
        null=True, blank=True,
    )
    date = models.DateField("입고일 자")
    name = models.ForeignKey(
        ItemName, 
        on_delete=models.RESTRICT, 
        verbose_name="품목명",
        null=True,
    )
    as_tool = models.ForeignKey(
        'as_app.Tool',
        on_delete=models.PROTECT,
        null=True, blank=True,
    )
    serial = models.CharField("시리얼 번호", max_length=100, blank=True, null=True)
    
    release_date = models.DateField("출고일자", blank=True, null=True)
    release_supplier = models.ForeignKey(
        ReleaseSupplier, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="출고처"
    )
    as_release_company = models.ForeignKey(
        'as_app.Company',
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    
    status = models.CharField("상태", max_length=10, choices=STATUS_CHOICES, default='재고')

    class Meta:
        verbose_name = "툴/장비 인벤토리"
        verbose_name_plural = "툴/장비 인벤토리 관리"
        ordering = ['-date']

    def __str__(self):
        base_str = f"[{self.status}] {self.name.name}"
        if self.serial:
            base_str += f" (S/N: {self.serial})"
        return base_str

# ── Proxy Models for Admin Views ──

class InboundInventory(Inventory):
    """입고 등록 전용 프록시 모델 (숨김 처리 또는 단일 조회용)"""
    class Meta:
        proxy = True
        verbose_name = "개별 입고 내역"
        verbose_name_plural = "개별 입고 내역"

class OutboundInventory(Inventory):
    """출고 등록 전용 프록시 모델"""
    class Meta:
        proxy = True
        verbose_name = "출고 등록"
        verbose_name_plural = "출고 등록"
