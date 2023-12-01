from django.urls import path
from .views import (
    list_reports,
    line_loads,
    line_loads_detail,
    efficiency_shipment,
    efficiency_placement_descent,
    efficiency_check_shipment,
)
urlpatterns = [

    path('reports/', list_reports, name='reports'),
    path('reports/report_line_loads/', line_loads, name='report_line_loads'),
    path('reports/report_line_loads_detail/', line_loads_detail, name='report_line_loads_detail'),
    path('reports/efficiency-shipment/', efficiency_shipment, name='efficiency-shipment'),
    path('reports/efficiency-placement-descent/', efficiency_placement_descent, name='efficiency-placement-descent'),
    path('reports/efficiency-check-shipment/', efficiency_check_shipment, name='efficiency-check-shipment'),
]
