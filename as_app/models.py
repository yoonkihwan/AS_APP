from django.core.exceptions import ValidationError
from django.db import models

# ──────────────────────────────────────────────
# 공용 기준정보 (master_data 앱에서 re-export)
# 하위 호환성 유지: from as_app.models import Company 등이 기존대로 동작
# ──────────────────────────────────────────────
from master_data.models import (  # noqa: F401
    CompanyCategory,
    Company,
    Brand,
    Tool,
    OutsourceCompany,
)


# ──────────────────────────────────────────────
# AS 전용 마스터 데이터
# ──────────────────────────────────────────────


class Part(models.Model):
    """수리부품/공임 관리"""

    PART_TYPE_CHOICES = [
        ('part', '부품'),
        ('labor', '공임'),
    ]

    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        verbose_name="브랜드",
        related_name="parts",
    )
    part_type = models.CharField(
        "구분",
        max_length=10,
        choices=PART_TYPE_CHOICES,
        default='part',
    )
    tools = models.ManyToManyField(
        Tool,
        verbose_name="적용 장비/툴",
        related_name="parts",
        blank=True,
        help_text="이 부품이 사용되는 장비를 선택하세요. 공용 부품은 여러 장비를 선택할 수 있습니다.",
    )
    name = models.CharField("부품명", max_length=200)
    code = models.CharField("부품코드", max_length=100, blank=True)
    remarks = models.TextField("비고", blank=True)

    class Meta:
        verbose_name = "수리부품"
        verbose_name_plural = "수리부품 관리"
        ordering = ["name"]

    @property
    def default_price(self):
        """기본 단가 (다스 그룹 단가 기준)"""
        default_group = self.group_prices.filter(category__name="다스").first()
        return default_group.price if default_group else 0

    def __str__(self):
        return f"{self.name} ({self.default_price:,}원)"

    def tool_list(self):
        """적용 장비 목록 표시용"""
        tools = self.tools.all()
        if tools:
            return ", ".join(str(t) for t in tools)
        return "공용 (전체 적용)"

    def get_price_for_company(self, company):
        """업체의 단가 그룹에 맞는 부품 단가를 반환. 설정된 그룹 단가가 없으면 다스 기본 단가 반환"""
        if company and company.price_group:
            group_price = self.group_prices.filter(category=company.price_group).first()
            if group_price:
                return group_price.price
        return self.default_price

class PartPrice(models.Model):
    """수리부품의 단가 그룹별 차등 단가"""

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name="group_prices",
        verbose_name="부품",
    )
    category = models.ForeignKey(
        CompanyCategory,
        on_delete=models.CASCADE,
        verbose_name="단가 그룹",
    )
    price = models.PositiveIntegerField("그룹 단가", default=0)

    class Meta:
        verbose_name = "단가 그룹별 금액"
        verbose_name_plural = "단가 그룹별 금액"
        unique_together = ["part", "category"]

    def __str__(self):
        return f"[{self.category.name}] {self.price:,}원"




class RepairPreset(models.Model):
    """수리 세트 - 자주 사용하는 부품 조합을 프리셋으로 관리"""

    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        verbose_name="브랜드",
        related_name="repair_presets",
    )
    name = models.CharField("세트명", max_length=200)
    tools = models.ManyToManyField(
        Tool,
        verbose_name="적용 장비/툴",
        related_name="repair_presets",
        blank=True,
        help_text="이 세트가 적용되는 장비를 선택하세요. 비워두면 모든 장비에 표시됩니다.",
    )
    parts = models.ManyToManyField(
        Part,
        verbose_name="포함 부품/공임",
        related_name="presets",
        help_text="이 세트에 포함되는 부품과 공임을 선택하세요.",
    )

    class Meta:
        verbose_name = "수리 세트"
        verbose_name_plural = "수리 세트 관리"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.total_price:,}원)"

    @property
    def total_price(self):
        """세트에 포함된 부품/공임의 합계 금액"""
        return sum(p.default_price for p in self.parts.all())


# ──────────────────────────────────────────────
# AS 프로세스 데이터 (Transaction Data)
# ──────────────────────────────────────────────


class InboundBatch(models.Model):
    """입고 배치 - 동일 업체/날짜의 여러 품목을 한 번에 입고 등록"""

    inbound_date = models.DateField("입고 날짜")
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        verbose_name="매출처",
        related_name="inbound_batches",
    )
    manager = models.CharField("담당자/부서", max_length=100, blank=True)
    memo = models.TextField("메모", blank=True, help_text="이번 입고 건에 대한 참고 메모")
    created_at = models.DateTimeField("생성일", auto_now_add=True)

    class Meta:
        verbose_name = "입고 배치"
        verbose_name_plural = "입고 등록"
        ordering = ["-inbound_date", "-created_at"]

    def __str__(self):
        company_name = self.company.name if self.company_id else "미지정"
        count = self.tickets.count() if self.pk else 0
        return f"{self.inbound_date} | {company_name} ({count}건)"

    @property
    def ticket_count(self):
        if not self.pk:
            return 0
        return self.tickets.count()


class ASTicket(models.Model):
    """​AS 접수 및 이력 - 입고부터 출고까지 하나의 티켓"""

    class Status(models.TextChoices):
        INBOUND = "inbound", "입고"
        OUTSOURCED = "outsourced", "수리의뢰"
        REPAIRED = "repaired", "수리완료"
        SHIPPED = "shipped", "출고"
        DISPOSED = "disposed", "자체폐기"

    # ── 입고 정보 ──
    inbound_batch = models.ForeignKey(
        InboundBatch,
        on_delete=models.SET_NULL,
        verbose_name="입고 배치",
        related_name="tickets",
        null=True,
        blank=True,
    )
    inbound_date = models.DateField("입고 날짜")
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        verbose_name="매출처",
        related_name="tickets",
        )
    manager = models.CharField("담당자/부서", max_length=100, blank=True)
    tool = models.ForeignKey(
        Tool,
        on_delete=models.PROTECT,
        verbose_name="장비/툴",
        related_name="tickets",
        )
    serial_number = models.CharField("시리얼 번호", max_length=200)
    symptom = models.TextField("요청사항 및 증상", blank=True)

    # ── 수리 정보 ──
    repair_content = models.TextField("비고", blank=True, help_text="추가 메모 (선택사항)")
    used_parts = models.ManyToManyField(
        Part,
        verbose_name="사용 부품/공임",
        related_name="tickets",
        blank=True,
    )
    repair_cost = models.PositiveIntegerField("AS 비용", default=0, help_text="사용 부품/공임 단가 합산 (자동 계산)")
    status = models.CharField(
        "상태",
        max_length=15,
        choices=Status.choices,
        default=Status.INBOUND,
    )

    # ── 의뢰 정보 ──
    outsource_company = models.ForeignKey(
        OutsourceCompany,
        on_delete=models.SET_NULL,
        verbose_name="의뢰업체",
        related_name="tickets",
        null=True,
        blank=True,
    )
    outsource_date = models.DateField("의뢰 날짜", null=True, blank=True)

    # ── 출고 및 정산 ──
    outbound_date = models.DateField("출고 날짜", null=True, blank=True)
    estimate_status = models.BooleanField("견적서 추출", default=False)
    tax_invoice = models.BooleanField("세금계산서 발행", default=False)

    # ── 관리 필드 ──
    created_at = models.DateTimeField("생성일", auto_now_add=True)
    updated_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        verbose_name = "AS 티켓"
        verbose_name_plural = "AS 티켓"
        ordering = ["-inbound_date", "-created_at"]

    def clean(self):
        """동일 툴+시리얼 번호가 출고 전(활성) 상태로 이미 존재하면 중복 방지"""
        super().clean()
        if self.tool_id and self.serial_number:
            active_statuses = [
                self.Status.INBOUND,
                self.Status.OUTSOURCED,
                self.Status.REPAIRED,
            ]
            qs = ASTicket.objects.filter(
                tool=self.tool,
                serial_number=self.serial_number,
                status__in=active_statuses,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    {"serial_number": "이 장비(%(tool)s)의 시리얼 번호 '%(sn)s'은(는) "
                     "현재 입고/수리 중인 티켓이 있습니다. 출고 완료 후 재입고해 주세요."},
                    params={"tool": self.tool, "sn": self.serial_number},
                )

    def __str__(self):
        company_name = self.company.name if self.company_id else "미지정 업체"
        tool_name = str(self.tool) if self.tool_id else "미지정 장비"
        return f"[{self.get_status_display()}] {company_name} - {tool_name} (S/N: {self.serial_number})"


# ──────────────────────────────────────────────
# Proxy Models (Admin 뷰 분리용)
# ──────────────────────────────────────────────


class InboundTicket(ASTicket):
    """입고 등록 전용 프록시 모델"""

    class Meta:
        proxy = True
        verbose_name = "입고 등록"
        verbose_name_plural = "입고 등록"


class RepairTicket(ASTicket):
    """수리 기록 전용 프록시 모델"""

    class Meta:
        proxy = True
        verbose_name = "수리 기록 등록"
        verbose_name_plural = "수리 기록 등록"


class OutboundTicket(ASTicket):
    """출고 처리 전용 프록시 모델"""

    class Meta:
        proxy = True
        verbose_name = "출고 등록"
        verbose_name_plural = "출고 등록"


class ASHistory(ASTicket):
    """AS 통합 이력 조회 전용 프록시 모델"""

    class Meta:
        proxy = True
        verbose_name = "AS 이력"
        verbose_name_plural = "통합 이력"


class EstimateTicket(ASTicket):
    """견적서 발행 전용 프록시 모델 (데모)"""

    class Meta:
        proxy = True
        verbose_name = "견적서 발행 (데모)"
        verbose_name_plural = "견적서 발행 (데모)"


class TaxInvoiceTicket(ASTicket):
    """세금계산서 발행 처리 전용 프록시 모델"""

    class Meta:
        proxy = True
        verbose_name = "세금계산서 등록"
        verbose_name_plural = "세금계산서 등록"


class OutsourcedTicket(ASTicket):
    """수리의뢰 현황 전용 프록시 모델"""

    class Meta:
        proxy = True
        verbose_name = "수리의뢰 현황"
        verbose_name_plural = "수리의뢰 현황"


# ──────────────────────────────────────────────
# 개선사항 요청 게시판 (Improvement Request Board)
# ──────────────────────────────────────────────


class ImprovementRequest(models.Model):
    """포탈 개선사항 요청 게시판"""

    class Status(models.TextChoices):
        PENDING = "PENDING", "접수"
        IN_PROGRESS = "IN_PROGRESS", "검토 중"
        COMPLETED = "COMPLETED", "반영 완료"
        REJECTED = "REJECTED", "반려"

    title = models.CharField("제목", max_length=200)
    content = models.TextField("내용", help_text="개선을 원하는 내용을 자세히 작성해 주세요.")
    author = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        verbose_name="작성자",
        related_name="improvement_requests",
    )
    status = models.CharField(
        "처리 상태",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    admin_reply = models.TextField(
        "관리자 답변",
        blank=True,
        default="",
        help_text="관리자가 작성하는 답변/처리 결과",
    )
    created_at = models.DateTimeField("작성일", auto_now_add=True)
    updated_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        verbose_name = "개선사항 요청"
        verbose_name_plural = "개선사항 요청"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title}"

