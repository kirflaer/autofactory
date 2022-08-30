from django.urls import path

from api.v2.views import TasksChangeViewSet, MarksViewSet, PalletViewSet

urlpatterns = [
    path('tasks/<str:type_task>/<uuid:guid>/', TasksChangeViewSet.as_view({'patch': 'change_task'})),
    path('marks/', MarksViewSet.as_view({'get': 'marks_to_unload', 'put': 'confirm_unloading'})),
    path('pallets/', PalletViewSet.as_view()),
]
