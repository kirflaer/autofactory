from django.urls import path, re_path, include

from .views import (DepartmentList, DeviceViewSet, DirectionListCreateView, LineListCreateView, LogCreateViewSet,
                    MarksViewSet, OrganizationList, PalletRetrieveUpdate,
                    ProductViewSet, RegExpList, StorageList, TasksViewSet, TypeFactoryOperationViewSet,
                    UnitsCreateListSet, UserRetrieve, StorageCellsListCreateViewSet, TasksContentViewSet)

urlpatterns = [
    re_path(r'v[1-9]/regexp/$', RegExpList.as_view()),
    re_path(r'v[1-9]/typefactoryoperation/$',
            TypeFactoryOperationViewSet.as_view()),
    re_path(r'v[1-9]/logs/$', LogCreateViewSet.as_view()),
    re_path(r'v[1-9]/organizations/$', OrganizationList.as_view()),
    re_path(r'v[1-9]/products/$', ProductViewSet.as_view()),
    re_path(r'v[1-9]/storages/$', StorageList.as_view()),
    re_path(r'v[1-9]/departments/$', DepartmentList.as_view()),
    re_path(r'v[1-9]/lines/$', LineListCreateView.as_view()),
    re_path(r'v[1-9]/users/$', UserRetrieve.as_view()),
    re_path(r'v[1-9]/cells/$', StorageCellsListCreateViewSet.as_view()),
    re_path(r'v[1-9]/direction/$', DirectionListCreateView.as_view()),
    re_path(r'v[1-9]/devices/$', DeviceViewSet.as_view(
        {'post': 'create', 'delete': 'remove'})),
    re_path(r'v[1-9]/scanners/$', DeviceViewSet.as_view(
        {'get': 'list_scanners'})),
    re_path(r'v[1-9]/units/$', UnitsCreateListSet.as_view()),
    re_path(r'v[1-9]/arks/add/', MarksViewSet.as_view({'post': 'add_marks'})),
    re_path(r'v[1-9]/marks/remove/', MarksViewSet.as_view({'post': 'remove_marks'})),
    re_path(r'^v[1-9]/pallets/(?P<id>.+)/$', PalletRetrieveUpdate.as_view()),
    re_path(r'^v[1-9]/tasks/(?P<type_task>\w+)/$', TasksViewSet.as_view({'get': 'list', 'post': 'create'})),
    re_path(r'^v[1-9]/tasks/(?P<type_task>\w+)/(?P<content_type>\w+)/$', TasksContentViewSet.as_view({'get': 'list'})),
    re_path(r'^v[2-9]/tasks/(?P<type_task>\w+)/(?P<guid>.{36})/take/$', TasksViewSet.as_view({'patch': 'take'})),

    path('v1/', include('api.v1.urls')),
    path('v2/', include('api.v2.urls')),
    path('v3/', include('api.v3.urls')),
]
