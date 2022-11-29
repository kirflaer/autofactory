from django.urls import path, include

from api.v3.views import (ShiftListViewSet, ShiftUpdateView, MarkingOnLineViewSet, MarkingOffLineViewSet,
                          MarkingViewSet,
                          TasksViewSet)

urlpatterns = [
    path('tasks/<str:type_task>/', TasksViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('tasks/<str:type_task>/<uuid:guid>/', TasksViewSet.as_view({'patch': 'change_task'})),
    path('marking/', MarkingOnLineViewSet.as_view()),
    path('marking/<uuid:pk>/', MarkingViewSet.as_view({'put': 'close'})),
    path('marking/offline/', MarkingOffLineViewSet.as_view()),
    path('shifts/', ShiftListViewSet.as_view()),
    path('shifts/<uuid:pk>/', ShiftUpdateView.as_view()),
    path('', include('api.v2.urls')),
]
