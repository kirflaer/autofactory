from django.urls import include, path, re_path

from .views import (
    OrganizationList,
    ProductList,
    ShiftList,
    shift_open,
    shift_close,
    devices_status,
    devices_marking,
    add_marks,
    remove_marks,
    unload_marks
)

urlpatterns = [
    re_path(r'v[0-9]/organizations/$', OrganizationList.as_view()),
    re_path(r'v[0-9]/catalogs/$', ProductList.as_view()),
    re_path(r'v[0-9]/products/$', ProductList.as_view()),
    path('v1/shifts/', ShiftList.as_view()),
    path('v1/shift-open/', shift_open),
    path('v1/shift-close/', shift_close),
    path('v1/shift/update/', shift_open),
    path('v1/devices-status/', devices_status),
    path('v1/add-marks/', add_marks),
    path('v1/delete-marks/', remove_marks),
    path('v1/marking/', devices_marking),
    path('v1/unload-marks/', unload_marks),
]
