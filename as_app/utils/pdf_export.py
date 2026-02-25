import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

def _register_fonts():
    # Register Malgun Gothic (맑은 고딕)
    font_path = "C:\\Windows\\Fonts\\malgun.ttf"
    font_bold_path = "C:\\Windows\\Fonts\\malgunbd.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('Malgun', font_path))
    if os.path.exists(font_bold_path):
        pdfmetrics.registerFont(TTFont('Malgun-Bold', font_bold_path))
        
def generate_pdf_estimate(tickets):
    _register_fonts()
    buffer = io.BytesIO()
    
    # 여백 설정 (상하좌우 20mm 정도)
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=30, 
        leftMargin=30, 
        topMargin=40, 
        bottomMargin=30
    )
    
    elements = []
    
    styles = getSampleStyleSheet()
    font_name = 'Malgun' if 'Malgun' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
    font_bold = 'Malgun-Bold' if 'Malgun-Bold' in pdfmetrics.getRegisteredFontNames() else font_name
    
    title_style = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    
    normal_style = ParagraphStyle(
        name='NormalStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=14,
    )
    
    for idx, ticket in enumerate(tickets):
        if idx > 0:
            from reportlab.platypus import PageBreak
            elements.append(PageBreak())
            
        company_name = ticket.company.name if ticket.company else "업체미정"
        model_name = ticket.tool.model_name if ticket.tool else "품목미정"
        total_price = sum(p.price for p in ticket.used_parts.all())
        today = datetime.now()
        
        # 1. 윗부분 (제목 및 발신/수신)
        elements.append(Paragraph("제    목 : DC TOOL(Conveyor Line) 견적", normal_style))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("<u>見    積    書</u>", title_style))
        
        # 발신, 수신 레이아웃을 표(Table)로 구성
        # 좌측: 수신자 정보 등
        # 우측: 발신자 정보
        left_info = [
            f"{company_name} 귀중",
            "참    조 : ",
            f"금    액 : \\ {total_price:,}  (VAT 별도)",
            "납품기일 : 발주후 30일",
            "지불조건 : 당사조건",
            "유효기간 : 30일",
            f"견적일자 : {today.year} 년 {today.month:02d} 월 {today.day:02d} 일",
            f"제    목 : {model_name} 수리비 견적"
        ]
        
        right_info = [
            "주소 : 울산광역시 북구 호수2로 7-1(호계동)",
            "Tel. (052) 988-0776   Fax. 988-0775",
            "M. 010-2577-0776",
            "Mail. tooleng@naver.com",
            "", "", "", "" # 빈 줄
        ]
        
        header_data = []
        for l, r in zip(left_info, right_info):
            header_data.append([l, r])
            
        header_table = Table(header_data, colWidths=[280, 250])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), font_name),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('ALIGN', (0,2), (0,2), 'LEFT'),  # 금액 부분을 좀 띄울지 여부 (기본은 왼쪽)
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 20))
        
        # 2. 견적서 품목 테이블
        # Description, Model, Qty, Unit price, Amount, Remark
        # 너비 대략: 160, 100, 40, 70, 80, 80
        col_widths = [160, 100, 40, 70, 80, 80]
        table_data = [
            ["Description", "Model", "Qty", "Unit price", "Amount", "Remark"]
        ]
        
        # 첫 번째 대표 품목줄
        sn = ticket.serial_number if ticket.serial_number else "없음"
        table_data.append([f"{model_name} 본체 수리비(Ser.No {sn})", "", "", "", "", ""])
        
        # 품목들
        for part in ticket.used_parts.all():
            table_data.append([
                part.name,
                part.code or "",
                "1",
                f"{part.price:,}",
                f"{part.price:,}",
                ""
            ])
            
        # 총합계 및 네고가
        table_data.append(["", "", "", "", "TOTAL", f"{total_price:,}"])
        table_data.append(["", "", "", "", "최종네고가", f"{total_price:,}"])
        table_data.append(["", "", "", "", "- VAT 별도 -", ""])
        
        # 테이블 스타일
        t_style = TableStyle([
            ('FONTNAME', (0,0), (-1,-1), font_name),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ALIGN', (0,0), (-1,0), 'CENTER'), # 헤더 중앙 정렬
            ('ALIGN', (2,1), (-1,-4), 'CENTER'), # 수량부터 금액까지 다 맞추기 기본
            ('ALIGN', (3,1), (4,-4), 'RIGHT'), # 단가, 금액 우측 정렬
            ('ALIGN', (4,-3), (4,-1), 'CENTER'), # TOTAL 등 우측정렬? 아니면 왼쪽?
            ('ALIGN', (5,-3), (5,-1), 'RIGHT'), # 금액 우측정렬
            
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('INNERGRID', (0,0), (-1,-4), 0.5, colors.black),
            ('BOX', (0,0), (-1,-4), 1, colors.black),
            
            # 셀 병합 (첫 줄 모델명)
            ('SPAN', (0,1), (-1,1)), 
            ('ALIGN', (0,1), (0,1), 'LEFT'),
            
            # 아래쪽 TOTAL, 네고가 테두리
            ('SPAN', (0,-3), (3,-3)), # TOTAL 왼쪽 빈공간
            ('SPAN', (0,-2), (3,-2)), # 최종네고가 왼쪽 빈공간
            ('SPAN', (0,-1), (3,-1)), # VAT 왼쪽 빈공간
        ])
        
        items_table = Table(table_data, colWidths=col_widths)
        items_table.setStyle(t_style)
        elements.append(items_table)
        
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("특기사항 : ", normal_style))
        
    doc.build(elements)
    buffer.seek(0)
    return buffer
