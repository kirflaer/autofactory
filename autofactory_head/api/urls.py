from django.urls import include, path, re_path

from .views import (
    MarkingViewSet,
    OrganizationList,
    ProductList,
    UserRetrieve,
    LineList,
    StorageList,
    DepartmentList,
    DeviceViewSet
)

urlpatterns = [
    re_path(r'v[0-9]/organizations/$', OrganizationList.as_view()),
    re_path(r'v[0-9]/products/$', ProductList.as_view()),
    re_path(r'v[0-9]/storages/$', StorageList.as_view()),
    re_path(r'v[0-9]/departments/$', DepartmentList.as_view()),
    re_path(r'v[0-9]/lines/$', LineList.as_view()),
    re_path(r'v[0-9]/users/$', UserRetrieve.as_view()),
    re_path(r'v[0-9]/devices/$', DeviceViewSet.as_view(
        {'get': 'list', 'post': 'create', 'delete': 'remove'})),
    path('v1/marking/',
         MarkingViewSet.as_view(
             {'get': 'list', 'post': 'create', 'put': 'confirm_unloading'})),
    path('v1/marking/<uuid:pk>/',
         MarkingViewSet.as_view({'put': 'close'})),

]
