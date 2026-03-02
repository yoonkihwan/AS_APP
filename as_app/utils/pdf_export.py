import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# ── 이미지 경로 ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMG_DIR = os.path.join(BASE_DIR, "견적서", "이미지")
LOGO_AUTOPOP = os.path.join(IMG_DIR, "AUTOPOP 로고.png")
LOGO_YOKOTA_APEX = os.path.join(IMG_DIR, "YOKOTA,APEX 로고.png")
STAMP_IMG = os.path.join(IMG_DIR, "회사직인.png")


def _register_fonts():
    font_path = "C:\\Windows\\Fonts\\malgun.ttf"
    font_bold_path = "C:\\Windows\\Fonts\\malgunbd.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('Malgun', font_path))
    if os.path.exists(font_bold_path):
        pdfmetrics.registerFont(TTFont('Malgun-Bold', font_bold_path))


def _safe_image(path, width=None, height=None):
    """이미지 파일이 존재하면 Image 객체 반환, 없으면 빈 문자열"""
    if os.path.exists(path):
        kwargs = {}
        if width:
            kwargs['width'] = width
        if height:
            kwargs['height'] = height
        return Image(path, **kwargs)
    return ""


def generate_pdf_estimate(tickets):
    """기존 다스 공구실 견적서 엑셀 양식과 동일한 레이아웃의 PDF 생성"""
    _register_fonts()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=30,
        bottomMargin=25,
    )

    elements = []
    font_name = 'Malgun' if 'Malgun' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
    font_bold = 'Malgun-Bold' if 'Malgun-Bold' in pdfmetrics.getRegisteredFontNames() else font_name

    # ── 스타일 정의 ──
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Normal'],
        fontName=font_bold, fontSize=26, leading=32,
        alignment=TA_CENTER, spaceAfter=8,
    )
    company_large_style = ParagraphStyle(
        'CompanyLarge', parent=styles['Normal'],
        fontName=font_bold, fontSize=20, leading=26,
        alignment=TA_RIGHT,
    )
    info_style = ParagraphStyle(
        'InfoStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=10, leading=14,
    )
    info_right_style = ParagraphStyle(
        'InfoRight', parent=styles['Normal'],
        fontName=font_name, fontSize=10, leading=14,
        alignment=TA_LEFT,
    )
    note_style = ParagraphStyle(
        'NoteStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=9, leading=13,
    )
    cell_style = ParagraphStyle(
        'CellStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=9, leading=12,
    )
    cell_center = ParagraphStyle(
        'CellCenter', parent=styles['Normal'],
        fontName=font_name, fontSize=9, leading=12,
        alignment=TA_CENTER,
    )
    cell_right = ParagraphStyle(
        'CellRight', parent=styles['Normal'],
        fontName=font_name, fontSize=9, leading=12,
        alignment=TA_RIGHT,
    )
    cell_bold = ParagraphStyle(
        'CellBold', parent=styles['Normal'],
        fontName=font_bold, fontSize=9, leading=12,
        alignment=TA_CENTER,
    )
    header_style = ParagraphStyle(
        'HeaderStyle', parent=styles['Normal'],
        fontName=font_bold, fontSize=10, leading=13,
        alignment=TA_CENTER,
    )

    page_width = A4[0] - 50  # 좌우 여백 25씩

    for idx, ticket in enumerate(tickets):
        if idx > 0:
            from reportlab.platypus import PageBreak
            elements.append(PageBreak())

        company_name = ticket.company.name if ticket.company else "업체미정"
        model_name = ticket.tool.model_name if ticket.tool else "품목미정"
        brand_name = ticket.tool.brand.name if ticket.tool and ticket.tool.brand else ""
        sn = ticket.serial_number if ticket.serial_number else ""
        parts = list(ticket.used_parts.all())
        total_price = sum(p.price for p in parts)
        nego_price = int(total_price * 0.9)
        today = datetime.now()

        # ═══════════════════════════════════════════
        # 1. 見 積 書 제목
        # ═══════════════════════════════════════════
        elements.append(Paragraph("<u>見    積    書</u>", title_style))
        elements.append(Spacer(1, 6))

        # ═══════════════════════════════════════════
        # 2. 업체명 귀중 + 청호이엔지 (+ 직인)
        # ═══════════════════════════════════════════
        stamp = _safe_image(STAMP_IMG, width=55, height=55)

        company_row = Table(
            [[
                Paragraph(f"<b>{company_name}</b>    귀중", info_style),
                Paragraph("<b>청 호 이 엔 지</b>", company_large_style),
                stamp if stamp else "",
            ]],
            colWidths=[page_width * 0.40, page_width * 0.42, page_width * 0.18],
        )
        company_row.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ]))
        elements.append(company_row)
        elements.append(Spacer(1, 4))

        # ═══════════════════════════════════════════
        # 3. 좌측: 발신 정보 / 우측: 수신 정보
        # ═══════════════════════════════════════════
        left_lines = [
            f"금    액 : ",
            f"납품기일 :   발주후      90 일",
            f"지불조건 : ",
            f"유효기간 :               30 일",
            f"견적일자 : {today.year} 년   {today.month:02d} 월   {today.day:02d} 일",
            f"제    목 : {model_name} 수리비 견적",
        ]
        right_lines = [
            "주소 : 울산광역시 북구 호수2로 7-1(호계동)",
            "Tel. (052) 988-0776    fax. 988-0775",
            "M. 010-2577-0776",
            "Mail. tooleng@naver.com",
            "",
            "",
        ]

        info_data = []
        for l_text, r_text in zip(left_lines, right_lines):
            info_data.append([
                Paragraph(l_text, info_style),
                Paragraph(r_text, info_right_style),
            ])

        info_table = Table(info_data, colWidths=[page_width * 0.50, page_width * 0.50])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 6))

        # ═══════════════════════════════════════════
        # 4. 브랜드 로고 영역
        # ═══════════════════════════════════════════
        logo_items = []
        autopop = _safe_image(LOGO_AUTOPOP, width=80, height=30)
        yokota_apex = _safe_image(LOGO_YOKOTA_APEX, width=160, height=30)

        if autopop or yokota_apex:
            logo_row = Table(
                [["", autopop if autopop else "", yokota_apex if yokota_apex else ""]],
                colWidths=[page_width * 0.40, 90, 170],
            )
            logo_row.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
            ]))
            elements.append(logo_row)
            elements.append(Spacer(1, 6))

        # ═══════════════════════════════════════════
        # 5. 품목 테이블
        # ═══════════════════════════════════════════
        col_widths = [155, 95, 35, 75, 85, 85]
        # 5-1) 헤더
        table_data = [[
            Paragraph("Description", header_style),
            Paragraph("Model", header_style),
            Paragraph("Qty", header_style),
            Paragraph("Unit price", header_style),
            Paragraph("Amount", header_style),
            Paragraph("Remark", header_style),
        ]]

        # 5-2) 대표 품목줄 (전체 span)
        sn_label = f"(Ser.No.{sn})" if sn else ""
        title_row_text = f"{model_name} 수리비{sn_label}"
        table_data.append([
            Paragraph(f"<b>{title_row_text}</b>", cell_style),
            "", "", "", "", "",
        ])

        # 5-3) 부품/공임 목록
        for part in parts:
            table_data.append([
                Paragraph(part.name, cell_style),
                Paragraph(part.code or "", cell_center),
                Paragraph("1 EA", cell_center),
                Paragraph(f"{part.price:,}", cell_right),
                Paragraph(f"{part.price:,}", cell_right),
                Paragraph("", cell_style),
            ])

        # 빈 행 채우기 (최소 10행 유지하여 표가 채워지도록)
        min_rows = 8
        data_rows = len(parts)
        for _ in range(max(0, min_rows - data_rows)):
            table_data.append(["", "", "", "", "", ""])

        num_data_rows = len(table_data)

        # 5-4) TOTAL / 최종네고가 / VAT 별도
        table_data.append([
            "", "", "", "",
            Paragraph("<b>TOTAL</b>", cell_right),
            Paragraph(f"<b>{total_price:,}</b>", cell_right),
        ])
        table_data.append([
            "", "", "", "",
            Paragraph("<b>최종네고가</b>", cell_right),
            Paragraph(f"<b>{nego_price:,}</b>", cell_right),
        ])
        table_data.append([
            "", "", "", "",
            Paragraph("- VAT 별도 -", cell_center),
            "",
        ])

        items_table = Table(table_data, colWidths=col_widths)

        t_style_cmds = [
            # 폰트
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),

            # 정렬
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            # 헤더 배경
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.92, 0.92, 0.92)),

            # 데이터 영역 테두리 (TOTAL부터 아래 제외)
            ('INNERGRID', (0, 0), (-1, num_data_rows - 1), 0.5, colors.black),
            ('BOX', (0, 0), (-1, num_data_rows - 1), 1, colors.black),

            # 대표 품목줄 span
            ('SPAN', (0, 1), (-1, 1)),
            ('ALIGN', (0, 1), (0, 1), 'LEFT'),
            ('BACKGROUND', (0, 1), (-1, 1), colors.Color(0.96, 0.96, 0.96)),

            # TOTAL 행
            ('SPAN', (0, num_data_rows), (3, num_data_rows)),
            ('LINEABOVE', (4, num_data_rows), (5, num_data_rows), 1, colors.black),
            ('LINEBELOW', (4, num_data_rows), (5, num_data_rows), 0.5, colors.black),

            # 네고가 행
            ('SPAN', (0, num_data_rows + 1), (3, num_data_rows + 1)),
            ('LINEBELOW', (4, num_data_rows + 1), (5, num_data_rows + 1), 1, colors.black),

            # VAT 행
            ('SPAN', (0, num_data_rows + 2), (3, num_data_rows + 2)),
            ('SPAN', (4, num_data_rows + 2), (5, num_data_rows + 2)),

            # 패딩
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]

        items_table.setStyle(TableStyle(t_style_cmds))
        elements.append(items_table)

        # ═══════════════════════════════════════════
        # 6. 특기사항
        # ═══════════════════════════════════════════
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(
            "특기사항 :  1. 최종 네고단가는 금회 구매에 한하며, 타사업체에 단가 공개를 금해 줄 것을 요청함.",
            note_style,
        ))
        elements.append(Spacer(1, 3))
        elements.append(Paragraph(
            "         2. Overhaul Charge 및 오일교환비 :  - 기본 수리 및 오일교환 : 140,000원",
            note_style,
        ))
        elements.append(Paragraph(
            "                                              - 완전 분해 및 오일교환 : 280,000원",
            note_style,
        ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
