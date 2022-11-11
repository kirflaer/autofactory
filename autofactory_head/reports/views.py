from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from catalogs.models import Line, Storage
from reports.reports_services import get_report_data, ReportType


@login_required
def list_reports(request):
    return render(request, 'list_reports.html')


@login_required
def line_loads(request):
    return _get_line_loads_report_data(request, ReportType.LINE_LOAD, 'line_loads.html')


@login_required
def line_loads_detail(request):
    return _get_line_loads_report_data(request, ReportType.LINE_LOAD_BY_HOURS, 'line_loads_details.html')


def _get_line_loads_report_data(request, report_type: ReportType, template: str) -> HttpResponse:
    lines = Line.objects.all()
    stocks = Storage.objects.all()

    report_data = []
    if len(request.GET):
        report_data = get_report_data(request.GET, report_type)

    return render(request, template, {'lines': lines, 'stocks': stocks, 'report_data': report_data,
                                      'stock_filter': request.GET.get('stock'), 'line_filter': request.GET.get('line')})
