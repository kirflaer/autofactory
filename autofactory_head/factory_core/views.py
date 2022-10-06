from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import render, get_object_or_404

from packing.marking_services import get_dashboard_data
from catalogs.models import (
    Device,
    Log
)

from django.views.generic import (
    ListView
)

from .log_services import logs_summary_data, log_line_decode

from django.contrib.auth.mixins import LoginRequiredMixin


@login_required
def index(request):
    dashboard_data = get_dashboard_data()
    dashboard_data['version'] = settings.VERSION
    return render(request, 'index.html', dashboard_data)


def check_status_view(request):
    return render(request, 'check_form.html')


class LogListView(LoginRequiredMixin, ListView):
    model = Log
    paginate_by = 50
    context_object_name = 'data'
    ordering = '-date'
    template_name = 'log.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(object_list=object_list, **kwargs)
        data['list_collapse'] = True
        data['possibility_of_adding'] = True
        data['devices'] = Device.objects.all()

        return data


@login_required
def logs_detail(request, pk):
    log = get_object_or_404(Log, pk=pk)
    log_data = log_line_decode(log.data[2:])
    return render(request, 'log_detail.html', {'data': (log_data,)})


@login_required
def logs_summary(request):
    device_guid = request.GET.get('device')
    device = get_object_or_404(Device, pk=device_guid)
    date_source = request.GET.get('date_source')
    return render(request, 'log_detail.html',
                  {'data': logs_summary_data(device, date_source)})
