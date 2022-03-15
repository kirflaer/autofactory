from django.urls import path

from . import views

from .views import (
    MarkingOperationListView,
    MarkingOperationRemoveView,
    MarkRemoveView,
    check_status_view,
    PalletListView,
    LogListView, TaskListView
)

urlpatterns = [
    path('', views.index, name='index'),

    path('marking/', MarkingOperationListView.as_view(), name='marking'),
    path('marking/detail/<uuid:pk>', views.marking_detail,
         name='marking_detail'),
    path('marking/remove/<uuid:pk>', MarkingOperationRemoveView.as_view(),
         name='marking_remove'),
    path('marking/remove-mark/<int:pk>', MarkRemoveView.as_view(),
         name='mark-remove'),

    path('check-status/', check_status_view),
    path('pallets/', PalletListView.as_view(),
         name='pallets'),
    path('pallets/detail/<uuid:pk>', views.pallet_detail,
         name='pallet_detail'),

    path('logs/', LogListView.as_view(), name='logs'),
    path('logs/summary/', views.logs_summary, name='logs_summary'),
    path('logs/detail/<int:pk>', views.logs_detail, name='logs_detail'),

    path('tasks/', TaskListView.as_view(), name='tasks'),
]
