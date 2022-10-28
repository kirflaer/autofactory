from django.urls import path

from . import views

from .views import (
    MarkingOperationListView,
    MarkingOperationRemoveView,
    MarkRemoveView,
    MarkingOperationUpdateView, ShiftListView, ShiftCreateView
)

urlpatterns = [

    path('marking/', MarkingOperationListView.as_view(), name='marking'),
    path('marking/edit/<uuid:pk>', MarkingOperationUpdateView.as_view(), name='marking_operation_edit'),
    path('marking/detail/<uuid:pk>', views.marking_detail, name='marking_detail'),
    path('marking/pallets/detail/<uuid:operation>/<str:pallet>', views.marking_pallets_detail,
         name='marking_pallets_detail'),
    path('marking/pallets/<uuid:operation>', views.marking_pallets, name='marking_pallets'),
    path('marking/remove/<uuid:pk>', MarkingOperationRemoveView.as_view(), name='marking_remove'),
    path('marking/remove-mark/<int:pk>', MarkRemoveView.as_view(), name='mark-remove'),
    path('shifts/', ShiftListView.as_view(), name='shifts'),
    path('shifts/new/', ShiftCreateView.as_view(), name='shift_new'),
    path('shifts/close/', views.shift_close, name='shift_close'),

]
