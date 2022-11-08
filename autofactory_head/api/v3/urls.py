from django.urls import path, include

from api.v3.views import ShiftListViewSet, ShiftUpdateView, MarkingOnLineViewSet, MarkingOffLineViewSet, MarkingViewSet

urlpatterns = [
    path('marking/', MarkingOnLineViewSet.as_view()),
    path('marking/<uuid:pk>/', MarkingViewSet.as_view({'put': 'close'})),
    path('marking/offline/', MarkingOffLineViewSet.as_view()),
    path('shifts/', ShiftListViewSet.as_view()),
    path('shifts/<uuid:pk>/', ShiftUpdateView.as_view()),
    path('', include('api.v2.urls')),
]