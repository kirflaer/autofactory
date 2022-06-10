from django.urls import path, re_path

from .views import (DepartmentList, DeviceViewSet, DirectionListCreateView,
                    LineListCreateView, LogCreateViewSet,
                    MarkingListCreateViewSet, MarkingViewSet, MarksViewSet,
                    OrganizationList, PalletRetrieveUpdate, PalletViewSet,
                    ProductViewSet, RegExpList, StorageList, TasksViewSet,
                    TaskUpdate, TypeFactoryOperationViewSet,
                    UnitsCreateListSet, UserRetrieve)

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
    re_path(r'v[0-9]/direction/$', DirectionListCreateView.as_view()),
    re_path(r'v[0-9]/devices/$', DeviceViewSet.as_view(
        {'post': 'create', 'delete': 'remove'})),
    re_path(r'v[0-9]/scanners/$', DeviceViewSet.as_view(
        {'get': 'list_scanners'})),
    re_path(r'v[0-9]/units/$', UnitsCreateListSet.as_view()),
    path('v1/marking/', MarkingListCreateViewSet.as_view()),
    path('v1/marking/<uuid:pk>/', MarkingViewSet.as_view({'put': 'close'})),

    path('v1/marks/add/', MarksViewSet.as_view({'post': 'add_marks'})),
    path('v1/marks/remove/', MarksViewSet.as_view({'post': 'remove_marks'})),

    path('v1/marks/', MarksViewSet.as_view(
        {'get': 'marks_to_unload', 'put': 'confirm_unloading'})),

    path('v1/pallets/',
         PalletViewSet.as_view(
             {'get': 'list', 'post': 'create', 'patch': 'change_content'})),
    path('v1/pallets/<str:id>/', PalletRetrieveUpdate.as_view()),
    path('v1/tasks/<str:type_task>/', TasksViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('v1/tasks/<uuid:pk>/', TaskUpdate.as_view()),
]
