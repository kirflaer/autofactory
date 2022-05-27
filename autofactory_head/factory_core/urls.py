from django.urls import path

from . import views

from .views import (
    check_status_view,
    LogListView
)

urlpatterns = [
    path('', views.index, name='index'),
    path('check-status/', check_status_view),
    path('logs/', LogListView.as_view(), name='logs'),
    path('logs/summary/', views.logs_summary, name='logs_summary'),
    path('logs/detail/<int:pk>', views.logs_detail, name='logs_detail'),
]
