from django.urls import path

from .views import (
    index,
    logs_summary,
    logs_detail,
    check_status_view,
    LogListView,
    ShiftUpdateView,
)

urlpatterns = [
    path('', index, name='index'),
    path('check-status/', check_status_view),
    path('logs/', LogListView.as_view(), name='logs'),
    path('logs/summary/', logs_summary, name='logs_summary'),
    path('logs/detail/<int:pk>', logs_detail, name='logs_detail'),
    path('shifts/edit/<uuid:pk>', ShiftUpdateView.as_view(), name='shifts_edit'),
]
