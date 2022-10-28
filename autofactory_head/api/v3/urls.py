from django.urls import path, include

from api.v3.views import ShiftListViewSet, ShiftUpdateView, MarkingOnLineViewSet, MarkingOffLineViewSet

urlpatterns = [
    path('marking/', MarkingOnLineViewSet.as_view()),
    path('marking/offline/', MarkingOffLineViewSet.as_view()),
    path('shifts/', ShiftListViewSet.as_view()),
    path('shifts/<uuid:pk>/', ShiftUpdateView.as_view()),
    path('', include('api.v2.urls')),
]
