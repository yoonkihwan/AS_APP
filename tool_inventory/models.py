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

    # ── 시리얼 정규화 (모든 저장 경로 공통) ──
    @staticmethod
    def normalize_serial(raw: str | None) -> str | None:
        """앞뒤 공백·쉼표 제거 + 대문자화. 빈 값이면 None."""
        if raw is None:
            return None
        cleaned = raw.strip().strip(",").strip().upper()
        return cleaned or None

    @classmethod
    def split_serials(cls, raw: str | None) -> list[str]:
        """'A, B, , C,' -> ['A', 'B', 'C'] (입력 순서 유지, 중복 제거)"""
        if not raw:
            return []
        result: list[str] = []
        for token in raw.split(","):
            sn = cls.normalize_serial(token)
            if sn and sn not in result:
                result.append(sn)
        return [s for s in result if not cls.is_master_barcode_text(s)]

    @staticmethod
    def is_master_barcode_text(raw: str | None) -> bool:
        """툴 마스터 바코드(TOOL-1-20 등) 또는 잔여 문자열인지 판별"""
        if not raw:
            return False
        import re
        s = raw.strip().upper()
        return bool(re.match(r"^(?:T?O?O?L)?[;:\-_]\d+(?:[;:\-_]\d+)?$", s) or re.match(r"^(?:TOOL|OOL)[;:\-_]?\d+", s))

    @classmethod
    def find_tool_by_model_barcode(cls, raw: str | None):
        """박스에 인쇄된 품목명(모델명) 바코드가 찍혔을 때 등록된 Tool 객체 반환"""
        sn = cls.normalize_serial(raw)
        if not sn:
            return None
        import re
        from master_data.models import Tool
        sn_clean = re.sub(r"^(?:P/?N|MODEL|ITEM)[;:\-\s]+", "", sn, flags=re.IGNORECASE).strip()
        sn_alnum = re.sub(r"[\s\-_]", "", sn_clean)
        if len(sn_alnum) < 3:
            return None
        for t in Tool.objects.select_related("brand").all():
            m_full = t.model_name.strip().upper()
            m_no_paren = m_full.split("(")[0].strip()
            m_first_tok = m_full.split(" ")[0].strip()
            candidates = {m_full, re.sub(r"[\s\-_]", "", m_full)}
            if len(m_no_paren) >= 3:
                candidates.add(m_no_paren)
                candidates.add(re.sub(r"[\s\-_]", "", m_no_paren))
            if len(m_first_tok) >= 4:
                candidates.add(m_first_tok)
                candidates.add(re.sub(r"[\s\-_]", "", m_first_tok))
            if sn_clean in candidates or sn_alnum in candidates:
                return t
        return None

    @classmethod
    def find_in_stock(cls, serial: str | None):
        """해당 시리얼이 현재 '재고' 상태인 신규 데이터 레코드 반환 (툴 무관, 1시리얼=1장비)"""
        sn = cls.normalize_serial(serial)
        if not sn:
            return None
        return (
            cls.all_objects.filter(serial__iexact=sn, status='재고', is_legacy=False)
            .select_related('tool', 'tool__brand')
            .first()
        )

    def save(self, *args, **kwargs):
        self.serial = self.normalize_serial(self.serial)
        super().save(*args, **kwargs)

    def clean(self):
        """중복 시리얼 검증 — 툴 종류와 무관하게 '재고' 상태 동일 시리얼 중복 방지"""
        sn = self.normalize_serial(self.serial)
        if sn and "," not in sn and not self.is_legacy:
            dup = Inventory.find_in_stock(sn)
            if dup and dup.pk != self.pk:
                raise ValidationError(
                    {"serial": f"이미 '재고' 상태인 시리얼입니다 — 출고 등록 대상: {sn}({dup.tool.model_name})"}
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
