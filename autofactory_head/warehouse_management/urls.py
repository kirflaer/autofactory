from django.urls import path

from .views import (
    ShipmentListView, OrderListView, OrderDetailListView
)

urlpatterns = [

    path('shipment/', ShipmentListView.as_view(),
         name='shipment'),
    path('shipment/orders/<uuid:parent_task>/', OrderListView.as_view(),
         name='orders'),
    path('orders/<uuid:order>/', OrderDetailListView.as_view(),
         name='orders_detail'),
]
