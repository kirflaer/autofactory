from django.urls import path, include

urlpatterns = [
    path('', include('api.v3.urls')),
]
