from django.urls import path, include

from api.v3.views import (ShiftListViewSet, ShiftUpdateView, MarkingOnLineViewSet, MarkingOffLineViewSet,
                          MarkingViewSet, TasksViewSet, StorageAreaListCreateViewSet, PalletViewSet,
                          PalletShipmentUpdate, PalletRepackingUpdate, CellRetrieveView)

urlpatterns = [
    path('tasks/<str:type_task>/<uuid:guid>/take/', TasksViewSet.as_view({'patch': 'take'})),
    path('tasks/<str:type_task>/<uuid:guid>/', TasksViewSet.as_view({'patch': 'change_task'})),
    path('tasks/<str:type_task>/', TasksViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('marking/', MarkingOnLineViewSet.as_view()),
    path('marking/<uuid:pk>/', MarkingViewSet.as_view({'put': 'close'})),
    path('marking/offline/', MarkingOffLineViewSet.as_view()),
    path('shifts/', ShiftListViewSet.as_view()),
    path('shifts/<uuid:pk>/', ShiftUpdateView.as_view()),
    path('area/', StorageAreaListCreateViewSet.as_view()),
    path('pallets/<str:pallet_id>/cell/change/', PalletViewSet.as_view({'patch': 'change_cell'})),
    path('pallets/<uuid:guid>/repacking/', PalletRepackingUpdate.as_view()),
    path('pallets/<uuid:guid>/shipment/', PalletShipmentUpdate.as_view()),
    path('cells/<str:external_key>/', CellRetrieveView.as_view()),
    path('', include('api.v2.urls')),
]
