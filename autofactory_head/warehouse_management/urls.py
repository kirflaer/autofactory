from django.urls import path

from .views import (
    PalletListView
)

urlpatterns = [

    path('pallets/', PalletListView.as_view(),
         name='pallets'),
]
