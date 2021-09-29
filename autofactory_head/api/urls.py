from django.urls import include, path

from .views import (
    OrganizationList,
    ProductList,
    ShiftList,
    shift_open,
    shift_close,
    devices_status,
    devices_marking
)

urlpatterns = [
    path('v1/organizations/', OrganizationList.as_view()),
    path('v1/catalogs/', ProductList.as_view()),
    path('v1/products/', ProductList.as_view()),
    path('v1/shifts/', ShiftList.as_view()),
    path('v1/shift-open/', shift_open),
    path('v1/shift-close/', shift_close),
    path('v1/devices-status/', devices_status),
    path('v1/marking/', devices_marking),
]
