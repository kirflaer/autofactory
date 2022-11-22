from django.urls import path

from api.v1.views import TasksChangeViewSet, MarksViewSet, PalletViewSet, TasksViewSet, TasksContentViewSet

urlpatterns = [
    path('tasks/<str:type_task>/<uuid:guid>/', TasksChangeViewSet.as_view({'patch': 'change_task'})),
    path('tasks/<str:type_task>/', TasksViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('tasks/<str:type_task>/<str:content_type>/', TasksContentViewSet.as_view({'get': 'list'})),
    path('tasks/<str:type_task>/<uuid:guid>/take/', TasksViewSet.as_view({'patch': 'take'})),
    path('marks/', MarksViewSet.as_view({'get': 'marks_to_unload', 'put': 'confirm_unloading'})),
    path('pallets/', PalletViewSet.as_view({'get': 'list', 'post': 'create'})),
]
