from django.core.exceptions import ValidationError
from django.db import models


# ──────────────────────────────────────────────
# 마스터 데이터 (Master Data)
# ──────────────────────────────────────────────


class CompanyCategory(models.Model):
    """단가 그룹 - 견적서 금액 구분용 (예: A등급, B등급, 특별단가 등)"""

    name = models.CharField("단가 그룹명", max_length=100, unique=True)

    class Meta:
        verbose_name = "단가 그룹"
        verbose_name_plural = "단가 그룹"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Company(models.Model):
    """업체 관리 - 매출처 및 AS 의뢰 업체"""

    class CompanyType(models.TextChoices):
        SALES = "sales", "매출처"
        CLIENT = "client", "의뢰처"
        BOTH = "both", "매출처/의뢰처"

    name = models.CharField("업체명", max_length=200)
    company_type = models.CharField(
        "업체 구분",
        max_length=10,
        choices=CompanyType.choices,
        default=CompanyType.CLIENT,
    )
    price_group = models.ForeignKey(
        CompanyCategory,
        on_delete=models.SET_NULL,
        verbose_name="단가 그룹",
        related_name="companies",
        null=True,
        blank=True,
        help_text="견적서 금액이 다르게 적용되는 그룹",
    )
    region = models.CharField(
        "지역/국가",
        max_length=100,
        blank=True,
        help_text="예: 한국, 일본, 중국, 미국 등",
    )
    address = models.TextField("주소", blank=True)

    class Meta:
        verbose_name = "업체"
        verbose_name_plural = "업체 관리"
        ordering = ["name"]

    def __str__(self):
        if self.region:
            return f"{self.name} [{self.region}]"
        return self.name


class Brand(models.Model):
    """브랜드 관리"""

    name = models.CharField("브랜드명", max_length=200, unique=True)

    class Meta:
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
        verbose_name = "장비/툴"
        verbose_name_plural = "툴 관리"
        ordering = ["brand__name", "model_name"]
        unique_together = ["brand", "model_name"]

    def __str__(self):
        return f"{self.brand.name} > {self.model_name}"


class Part(models.Model):
    """부품/수리 품목 관리"""

    class PartType(models.TextChoices):
        DEDICATED = "dedicated", "전용"
        COMMON = "common", "공용"

    tools = models.ManyToManyField(
        Tool,
        verbose_name="적용 장비/툴",
        related_name="parts",
        blank=True,
        help_text="이 부품이 사용되는 장비를 선택하세요. 공용 부품은 여러 장비를 선택할 수 있습니다.",
    )
    name = models.CharField("부품명", max_length=200)
    code = models.CharField("부품코드", max_length=100, blank=True)
    price = models.PositiveIntegerField("단가", default=0)
    part_type = models.CharField(
        "구분",
        max_length=10,
        choices=PartType.choices,
        default=PartType.DEDICATED,
    )

    class Meta:
        verbose_name = "부품"
        verbose_name_plural = "부품 관리"
        ordering = ["name"]

    def __str__(self):
        type_label = self.get_part_type_display()
        return f"[{type_label}] {self.name}"

    def tool_list(self):
        """적용 장비 목록 표시용"""
        tools = self.tools.all()
        if tools:
            return ", ".join(str(t) for t in tools)
        return "공용 (전체 적용)"


# ──────────────────────────────────────────────
# AS 프로세스 데이터 (Transaction Data)
# ──────────────────────────────────────────────


class InboundBatch(models.Model):
    """입고 배치 - 동일 업체/날짜의 여러 품목을 한 번에 입고 등록"""

    inbound_date = models.DateField("입고 날짜")
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        verbose_name="업체",
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
        return f"{self.inbound_date} | {self.company.name} ({self.ticket_count}건)"

    @property
    def ticket_count(self):
        return self.tickets.count()


class ASTicket(models.Model):
    """​AS 접수 및 이력 - 입고부터 출고까지 하나의 티켓"""

    class Status(models.TextChoices):
        INBOUND = "inbound", "입고"
        WAITING = "waiting", "수리대기"
        REPAIRED = "repaired", "수리완료"
        SHIPPED = "shipped", "출고"

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
        verbose_name="업체",
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
    repair_content = models.TextField("AS 내용 (수리 내역)", blank=True)
    used_parts = models.ManyToManyField(
        Part,
        verbose_name="사용 부품",
        related_name="tickets",
        blank=True,
    )
    repair_cost = models.PositiveIntegerField("AS 비용", default=0)
    status = models.CharField(
        "상태",
        max_length=10,
        choices=Status.choices,
        default=Status.INBOUND,
    )

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
                self.Status.WAITING,
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
        return f"[{self.get_status_display()}] {self.company.name} - {self.tool} (S/N: {self.serial_number})"


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
        verbose_name = "수리 기록"
        verbose_name_plural = "수리 기록"


class OutboundTicket(ASTicket):
    """출고 처리 전용 프록시 모델"""

    class Meta:
        proxy = True
        verbose_name = "출고 처리"
        verbose_name_plural = "출고 처리"


class ASHistory(ASTicket):
    """AS 통합 이력 조회 전용 프록시 모델"""

    class Meta:
        proxy = True
        verbose_name = "AS 이력"
        verbose_name_plural = "통합 이력"
