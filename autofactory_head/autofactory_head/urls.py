from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path("", include("factory_core.urls")),

    #1C support
    path('<str:basename>/<str:routname>/api/', include('api.urls')),

]
