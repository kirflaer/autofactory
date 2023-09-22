from django.urls import path, include

from api.v4.views import (
    TasksViewSetV4, PalletCollectUpdate, UsersListViewSet, PalletDivideViewSet, PalletCollectStoryListView
)

urlpatterns = [
    path('tasks/<str:type_task>/<uuid:guid>/take/', TasksViewSetV4.as_view({'patch': 'take'})),
    path('tasks/<str:type_task>/', TasksViewSetV4.as_view({'get': 'list', 'post': 'create'})),
    path('tasks/<str:type_task>/<uuid:guid>/', TasksViewSetV4.as_view({'patch': 'change_task'})),
    path('tasks/<str:type_task>/<uuid:guid>/<str:method>/', TasksViewSetV4.as_view({'get': 'custom_method'})),
    path('pallets/<str:id>/collect/', PalletCollectUpdate.as_view()),
    path('pallets/divide/', PalletDivideViewSet.as_view({'patch': 'divide_pallets'})),
    path('users/list/', UsersListViewSet.as_view({'get': 'list'})),
    path('pallets/<uuid:guid>/story/', PalletCollectStoryListView.as_view()),
    path('', include('api.v3.urls')),
]
