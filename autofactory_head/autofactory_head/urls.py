from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path("auth/", include("django.contrib.auth.urls")),
    path("", include("factory_core.urls")),

    #1C support
    path('<str:basename>/<str:routname>/api/', include('api.urls')),

]

handler404 = "autofactory_head.views.page_not_found"
handler500 = "autofactory_head.views.server_error"
