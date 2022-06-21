from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('autofact-adm/', admin.site.urls),
    path('api/', include('api.urls')),
    path("auth/", include("django.contrib.auth.urls")),
    path("", include("factory_core.urls")),
    path("", include("catalogs.urls")),
    path("", include("packing.urls")),
    path("", include("warehouse_management.urls")),
]

handler404 = "autofactory_head.views.page_not_found"
handler500 = "autofactory_head.views.server_error"
