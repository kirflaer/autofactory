from django.urls import path, re_path, include

from .views import (DepartmentList, DeviceViewSet, DirectionListCreateView, LineListCreateView, LogCreateViewSet,
                    MarkingListCreateViewSet, MarkingViewSet, MarksViewSet, OrganizationList, PalletRetrieveUpdate,
                    PalletViewSet, ProductViewSet, RegExpList, StorageList, TasksViewSet, TypeFactoryOperationViewSet,
                    UnitsCreateListSet, UserRetrieve, StorageCellsListCreateViewSet)

urlpatterns = [
    re_path(r'v[0-9]/regexp/$', RegExpList.as_view()),
    re_path(r'v[0-9]/typefactoryoperation/$',
            TypeFactoryOperationViewSet.as_view()),
    re_path(r'v[0-9]/logs/$', LogCreateViewSet.as_view()),
    re_path(r'v[0-9]/organizations/$', OrganizationList.as_view()),
    re_path(r'v[0-9]/products/$', ProductViewSet.as_view()),
    re_path(r'v[0-9]/storages/$', StorageList.as_view()),
    re_path(r'v[0-9]/departments/$', DepartmentList.as_view()),
    re_path(r'v[0-9]/lines/$', LineListCreateView.as_view()),
    re_path(r'v[0-9]/users/$', UserRetrieve.as_view()),
    re_path(r'v[0-9]/cells/$', StorageCellsListCreateViewSet.as_view()),
    re_path(r'v[0-9]/direction/$', DirectionListCreateView.as_view()),
    re_path(r'v[0-9]/devices/$', DeviceViewSet.as_view(
        {'post': 'create', 'delete': 'remove'})),
    re_path(r'v[0-9]/scanners/$', DeviceViewSet.as_view(
        {'get': 'list_scanners'})),
    re_path(r'v[0-9]/units/$', UnitsCreateListSet.as_view()),
    re_path(r'^v[0-9]/marking/(?P<pk>.{36})/$', MarkingViewSet.as_view({'put': 'close'})),
    re_path(r'v[0-9]/marking/', MarkingListCreateViewSet.as_view()),
    re_path(r'v[0-9]/arks/add/', MarksViewSet.as_view({'post': 'add_marks'})),
    re_path(r'v[0-9]/marks/remove/', MarksViewSet.as_view({'post': 'remove_marks'})),

    re_path(r'v[0-9]/marks/', MarksViewSet.as_view(
        {'get': 'marks_to_unload', 'put': 'confirm_unloading'})),

    re_path(r'^v[0-9]/pallets/$', PalletViewSet.as_view({'get': 'list', 'post': 'create'})),
    re_path(r'^v[0-9]/pallets/(?P<id>.+)/$', PalletRetrieveUpdate.as_view()),
    re_path(r'^v[0-9]/tasks/(?P<type_task>\w+)/$', TasksViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('v1/', include('api.v1.urls')),
    path('v2/', include('api.v2.urls')),
]
