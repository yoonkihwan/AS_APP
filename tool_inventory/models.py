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

class Inventory(models.Model):
    """메인 방비/툴 재고 리스트"""
    STATUS_CHOICES = [
        ('재고', '재고 (입고됨)'),
        ('출고', '출고 완료'),
    ]

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
        verbose_name="입고처"
    )
    date = models.DateField("입고일 자")
    name = models.ForeignKey(
        ItemName, 
        on_delete=models.RESTRICT, 
        verbose_name="품목명"
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
