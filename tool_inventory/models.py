import uuid
from django.db import models
from django.core.exceptions import ValidationError
# Removing legacy Supplier, ReleaseSupplier, ItemName classes since we map to as_app models now.


# ── Custom Managers ──────────────────────────────────────────

class ActiveInventoryManager(models.Manager):
    """is_legacy=False인 신규 데이터만 반환하는 기본 매니저"""
    def get_queryset(self):
        return super().get_queryset().filter(is_legacy=False)


class LegacyInventoryManager(models.Manager):
    """is_legacy=True인 구 데이터만 반환하는 매니저"""
    def get_queryset(self):
        return super().get_queryset().filter(is_legacy=True)


class AllInventoryManager(models.Manager):
    """레거시 여부에 상관없이 전체를 반환하는 매니저 (관리용)"""
    def get_queryset(self):
        return super().get_queryset()


class InventoryBatch(models.Model):
    """입고 배치 - 한 번에 여러 툴/장비를 입고 등록"""
    inbound_date = models.DateField("입고 날짜")
    supplier = models.ForeignKey(
        'master_data.OutsourceCompany',
        on_delete=models.PROTECT,
        verbose_name="입고업체",
        related_name="inbound_batches",
    )
    created_at = models.DateTimeField("생성일", auto_now_add=True)
    is_legacy = models.BooleanField(
        "구 데이터 여부",
        default=False,
        help_text="True이면 레거시(구) 데이터로 분류되어 별도 메뉴에서 조회됩니다.",
        db_index=True,
    )

    class Meta:
        verbose_name = "입고 등록"
        verbose_name_plural = "입고 등록"
        ordering = ["-inbound_date", "-created_at"]

    def __str__(self):
        return f"{self.inbound_date} | {self.supplier.name} ({self.inventories.count()}건)"

class OutboundBatch(models.Model):
    """출고 배치 - 한 번에 여러 툴/장비를 출고 등록"""
    release_date = models.DateField("출고 날짜")
    release_company = models.ForeignKey(
        'master_data.Company',
        on_delete=models.PROTECT,
        verbose_name="출고업체",
        related_name="tool_outbound_batches",
    )
    created_at = models.DateTimeField("생성일", auto_now_add=True)
    is_legacy = models.BooleanField(
        "구 데이터 여부",
        default=False,
        help_text="True이면 레거시(구) 데이터로 분류됩니다.",
        db_index=True,
    )

    class Meta:
        verbose_name = "출고 등록"
        verbose_name_plural = "출고 등록"
        ordering = ["-release_date", "-created_at"]

    def __str__(self):
        return f"{self.release_date} | {self.release_company.name} ({self.tickets.count()}건)"

class OutboundTicket(models.Model):
    batch = models.ForeignKey(
        OutboundBatch,
        on_delete=models.CASCADE,
        verbose_name="출고 배치",
        related_name="tickets"
    )
    tool = models.ForeignKey(
        'master_data.Tool',
        on_delete=models.PROTECT,
        verbose_name="품목"
    )
    quantity = models.PositiveIntegerField(
        "출고 수량",
        default=1,
        help_text="시리얼 미선택 시, 이 수량만큼 선입선출 출고"
    )
    inventories = models.ManyToManyField(
        'Inventory',
        blank=True,
        verbose_name="출고 대상 (시리얼 다중선택)",
        limit_choices_to={'status': '재고'}
    )
    usage_process = models.CharField(
        "적용공정/용도",
        max_length=50,
        blank=True,
        null=True,
        help_text="[선택] 출고 시 현장 적용 공정이나 용도를 기입"
    )

    class Meta:
        verbose_name = "출고등록 티켓"
        verbose_name_plural = "출고등록 티켓"
        
    def __str__(self):
        return f"{self.tool.model_name} ({self.quantity}개)"

class Inventory(models.Model):
    """메인 장비/툴 재고 리스트"""
    STATUS_CHOICES = [
        ('재고', '재고'),
        ('출고', '출고'),
    ]

    # 배치 정보 연동
    batch = models.ForeignKey(
        InventoryBatch,
        on_delete=models.PROTECT,
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
        'master_data.OutsourceCompany',
        on_delete=models.PROTECT,
        verbose_name="입고처",
    )
    date = models.DateField("입고일자")
    tool = models.ForeignKey(
        'master_data.Tool',
        on_delete=models.PROTECT,
        verbose_name="품목명",
    )
    serial = models.CharField("시리얼 번호", max_length=100, blank=True, null=True)

    release_date = models.DateField("출고일자", blank=True, null=True)
    release_company = models.ForeignKey(
        'master_data.Company',
        on_delete=models.SET_NULL,
        verbose_name="출고처",
        null=True, blank=True,
    )

    status = models.CharField("상태", max_length=10, choices=STATUS_CHOICES, default='재고')
    usage_process = models.CharField("적용공정/용도", max_length=50, blank=True, null=True)

    is_legacy = models.BooleanField(
        "구 데이터 여부",
        default=False,
        help_text="True이면 레거시(구) 데이터로 분류되어 '툴 입출고 관리(구)' 메뉴에서 조회됩니다.",
        db_index=True,
    )

    # ── Managers ──
    # 기본 매니저(objects): 신규 데이터만 (is_legacy=False)
    objects = ActiveInventoryManager()
    # 레거시 데이터 전용 매니저
    legacy_objects = LegacyInventoryManager()
    # 전체 데이터 매니저 (마이그레이션/관리용)
    all_objects = AllInventoryManager()

    class Meta:
        verbose_name = "통합 입출고 이력"
        verbose_name_plural = "통합 입출고 이력"
        ordering = ['-date', 'tool__model_name']
        # 같은 tool + serial 조합은 신규 데이터(is_legacy=False) 내에서만 재고 상태일 때 중복 불가
        # (DB 레벨 unique 제약은 걸지 않고, clean()에서 소프트 검증)

    def clean(self):
        """중복 시리얼 검증 — 신규 데이터에서 재고 상태 동일 시리얼 중복 방지"""
        if self.serial and self.tool_id and not self.is_legacy:
            dup_qs = Inventory.all_objects.filter(
                tool=self.tool,
                serial=self.serial,
                status='재고',
                is_legacy=False,
            ).exclude(pk=self.pk)
            if dup_qs.exists():
                raise ValidationError(
                    {"serial": f"해당 시리얼 번호({self.serial})는 이미 '재고' 상태로 등록되어 있습니다. "
                                "중복 입고를 확인해 주세요."}
                )

    def __str__(self):
        base_str = f"[{self.status}] {self.tool.model_name}"
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

class LegacyInventory(Inventory):
    """레거시(구) 데이터 전용 프록시 모델 — 읽기 전용 조회용"""
    legacy_objects = LegacyInventoryManager()

    class Meta:
        proxy = True
        verbose_name = "통합 입출고 이력(구)"
        verbose_name_plural = "통합 입출고 이력(구)"

from master_data.models import Tool

class ToolStockSummary(Tool):
    """툴별 현재 재고 수량 및 시리얼 조회를 위한 프록시 모델"""
    class Meta:
        proxy = True
        verbose_name = "재고 현황"
        verbose_name_plural = "재고"


class TodoItem(models.Model):
    """대시보드 투두리스트 항목"""

    title = models.CharField("할 일", max_length=300)
    is_done = models.BooleanField("완료 여부", default=False)
    created_at = models.DateTimeField("생성일", auto_now_add=True)
    updated_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        verbose_name = "할 일"
        verbose_name_plural = "할 일 목록"
        ordering = ["is_done", "-created_at"]

    def __str__(self):
        return self.title
