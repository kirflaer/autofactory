from django.urls import path, include

from api.v4.views import TasksViewSet

urlpatterns = [
    path('tasks/<str:type_task>/', TasksViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('', include('api.v3.urls')),
]
