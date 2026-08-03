import os
from django.conf import settings
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def register_korean_fonts():
    """
    프로젝트 내부의 나눔고딕 폰트를 등록하고 (기본폰트명, 볼드폰트명) 튜플을 반환합니다.
    """
    font_name = 'NanumGothic'
    font_name_bold = 'NanumGothic-Bold'
    
    font_path = os.path.join(settings.BASE_DIR, 'as_app', 'static', 'fonts', 'NanumGothic-Regular.ttf')
    font_bold_path = os.path.join(settings.BASE_DIR, 'as_app', 'static', 'fonts', 'NanumGothic-Bold.ttf')
    
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
        except Exception:
            font_name = 'Helvetica'
    else:
        font_name = 'Helvetica'
        
    if os.path.exists(font_bold_path):
        try:
            pdfmetrics.registerFont(TTFont(font_name_bold, font_bold_path))
        except Exception:
            font_name_bold = font_name
    else:
        font_name_bold = font_name

    return font_name, font_name_bold
