from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import AttendanceRecord

@login_required
def hr_calendar_view(request):
    """
    Renders the HR calendar view. FullCalendar will fetch events via a separate API.
    """
    return render(request, "hr_app/calendar.html")

@login_required
def api_calendar_events(request):
    """
    Returns calendar events for the currently authenticated user in FullCalendar JSON format.
    """
    # [START, END] limits provided by FullCalendar (ISO8601 strings)
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    qs = AttendanceRecord.objects.all()
    # 일반 직원은 본인 것만 표출. 관리자(superuser)면 전체 표출 옵션을 줄 수도 있지만,
    # 일단 요구사항에 맞춰 "내 근무 달력"이므로 본인 것만 필터링합니다.
    if not request.user.is_superuser:
        qs = qs.filter(user=request.user)

    if start_str and end_str:
        qs = qs.filter(date__gte=start_str[:10], date__lte=end_str[:10])

    events = []
    
    # CSS 클래스 매핑 (템플릿에서 정의한 테마 연동)
    color_map = {
        'NORMAL': 'type-normal',
        'OVERTIME': 'type-overtime',
        'WEEKEND': 'type-weekend',
        'LEAVE_FULL': 'type-leave-full',
        'LEAVE_HALF_AM': 'type-leave-half',
        'LEAVE_HALF_PM': 'type-leave-half',
        'SICK_LEAVE': 'type-leave-full',
        'PUBLIC_LEAVE': 'type-leave-full',
    }

    for record in qs:
        # 이벤트 제목 구성 (장고 Admin과 동일하게)
        title_prefix = dict(AttendanceRecord.WorkType.choices).get(record.work_type, record.work_type)
        title = f"[{title_prefix}] {record.user.username}"
        
        if record.overtime_hours > 0:
            title += f" (+{record.overtime_hours}H)"

        events.append({
            'id': record.id,
            'title': title,
            'start': record.date.isoformat(),
            'allDay': True,
            'classNames': [color_map.get(record.work_type, 'type-normal')]
        })

    return JsonResponse(events, safe=False)

