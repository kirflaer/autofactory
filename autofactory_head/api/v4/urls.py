from django.urls import path, include

from api.v4.views import TasksViewSetV4, PalletCollectUpdate, UsersListViewSet

urlpatterns = [
    path('tasks/<str:type_task>/', TasksViewSetV4.as_view({'get': 'list', 'post': 'create'})),
    path('tasks/<str:type_task>/<uuid:guid>/', TasksViewSetV4.as_view({'patch': 'change_task'})),
    path('pallets/<str:id>/collect/', PalletCollectUpdate.as_view()),
    path('users/list/', UsersListViewSet.as_view()),
    path('', include('api.v3.urls')),
]
