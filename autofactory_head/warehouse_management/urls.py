from django.urls import path

from .views import (
    ShipmentListView, OrderListView,
    OrderDetailListView, SourceRemoveView, SourceListView, PalletProductUpdateView, PalletListView, PalletDetailView
)

urlpatterns = [

    path('shipment/', ShipmentListView.as_view(),
         name='shipment'),
    path('shipment/pallets/<uuid:parent_task>', PalletListView.as_view(),
         name='shipment_pallets'),
    path('shipment/pallets/detail/<uuid:pallet>', PalletDetailView.as_view(),
         name='shipment_pallets_detail'),
    path('shipment/orders/<uuid:parent_task>/', OrderListView.as_view(),
         name='orders'),
    path('orders/products/<uuid:order>/', OrderDetailListView.as_view(),
         name='orders_detail'),
    path('orders/products/edit/<int:pk>/', PalletProductUpdateView.as_view(),
         name='orders_products_update'),
    path('sources/<uuid:key>/', SourceListView.as_view(),
         name='sources'),
    path('sources/remove/<int:pk>/', SourceRemoveView.as_view(),
         name='sources_remove'),
]
