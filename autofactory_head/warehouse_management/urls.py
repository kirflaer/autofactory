from django.urls import path

from .views import (
    PalletListView
)

urlpatterns = [

    path('pallets/', PalletListView.as_view(),
         name='pallets'),
]
# path('pallets/detail/<uuid:pk>', views.pallet_detail,
#      name='pallet_detail'),
#
# path('tasks/', TaskListView.as_view(), name='tasks'),
