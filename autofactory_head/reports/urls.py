from django.urls import path
from .views import (
    list_reports,
    line_loads,
    line_loads_detail
)
urlpatterns = [

    path('reports/', list_reports, name='reports'),
    path('reports/report_line_loads/', line_loads, name='report_line_loads'),
    path('reports/report_line_loads_detail/', line_loads_detail, name='report_line_loads_detail'),

]
