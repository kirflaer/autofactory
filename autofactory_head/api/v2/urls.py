from django.urls import path, include

from api.v2.views import TasksChangeViewSet, MarksViewSet, PalletViewSet, MarkingListCreateViewSet, MarkingViewSet


urlpatterns = [
    path('tasks/<str:type_task>/<uuid:guid>/', TasksChangeViewSet.as_view({'patch': 'change_task'})),
    path('marks/', MarksViewSet.as_view({'get': 'marks_to_unload', 'put': 'confirm_unloading'})),
    path('pallets/', PalletViewSet.as_view()),
    path('marking/', MarkingListCreateViewSet.as_view()),
    path('marking/<uuid:pk>/', MarkingViewSet.as_view({'put': 'close'})),
    path('', include('api.v1.urls')),
]
