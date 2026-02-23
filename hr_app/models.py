from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class AttendanceRecord(models.Model):
    class WorkType(models.TextChoices):
        NORMAL = 'NORMAL', '정상근무'
        OVERTIME = 'OVERTIME', '연장근무'
        WEEKEND = 'WEEKEND', '주말특근'
        LEAVE_FULL = 'LEAVE_FULL', '연차 (종일)'
        LEAVE_HALF_AM = 'LEAVE_HALF_AM', '오전반차'
        LEAVE_HALF_PM = 'LEAVE_HALF_PM', '오후반차'
        SICK_LEAVE = 'SICK_LEAVE', '병가'
        PUBLIC_LEAVE = 'PUBLIC_LEAVE', '공가'

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="직원")
    date = models.DateField(default=timezone.now, verbose_name="근무 일자")
    work_type = models.CharField(
        max_length=20,
        choices=WorkType.choices,
        default=WorkType.NORMAL,
        verbose_name="근무 형태"
    )
    
    start_time = models.TimeField(null=True, blank=True, verbose_name="시작 시간", help_text="예: 09:00:00")
    end_time = models.TimeField(null=True, blank=True, verbose_name="종료 시간", help_text="예: 18:00:00")
    
    overtime_hours = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="연장/특근 시간(H)", help_text="추가 근무한 시간 (단위: 시간)")
    memo = models.TextField(blank=True, verbose_name="근무/휴가 메모", help_text="예: 주말 장비 셋업, 병원 진료 등")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "근태 기록"
        verbose_name_plural = "근태 기록 목록"
        unique_together = ('user', 'date')
        ordering = ['-date', 'user']

    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.get_work_type_display()})"
