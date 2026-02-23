from django.urls import path
from .views import hr_calendar_view, api_calendar_events

urlpatterns = [
    path('calendar/', hr_calendar_view, name='hr_calendar_view'),
    path('calendar-events/', api_calendar_events, name='api_calendar_events'),
]
