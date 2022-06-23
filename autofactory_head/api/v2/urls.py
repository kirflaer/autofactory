from django.urls import path

from api.v2.views import TasksChangeViewSet

urlpatterns = [
    path('tasks/<str:type_task>/<uuid:guid>/', TasksChangeViewSet.as_view({'patch': 'change_task'})),
]
