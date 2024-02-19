from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views.generic import (
    ListView,
    UpdateView
)
from django.urls import reverse_lazy

from catalogs.models import (
    Device,
    Log
)
from packing.forms import ShiftForm
from packing.marking_services import get_dashboard_data
from .log_services import logs_summary_data, log_line_decode, get_log_filters
from .models import Shift


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

    def get_queryset(self):
        queryset = Log.objects.all()
        if len(self.request.GET):
            log_filter = get_log_filters(self.request.GET)
            # TODO: можеть быть ошибка если передан некорректный параметр. нужна проверка как в api
            if len(log_filter):
                queryset = queryset.filter(**log_filter)
        return queryset.order_by('-date')[:200]

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(object_list=object_list, **kwargs)
        data['list_collapse'] = True
        data['possibility_of_adding'] = True
        data['devices'] = Device.objects.all()

        data['device'] = self.request.GET.get('device')
        data['level'] = self.request.GET.get('level')
        data['app_version'] = self.request.GET.get('app_version')
        data['username'] = self.request.GET.get('username')

        return data


@login_required
def logs_detail(request, pk):
    log = get_object_or_404(Log, pk=pk)
    log_data = log_line_decode(log.data[2:])
    return render(request, 'log_detail.html', {'data': (log_data,), 'username': log.username, 'date': log.date})


@login_required
def logs_summary(request):
    device_guid = request.GET.get('device')
    device = get_object_or_404(Device, pk=device_guid)
    date_source = request.GET.get('date_source')
    return render(request, 'log_detail.html',
                  {'data': logs_summary_data(device, date_source)})


class ShiftUpdateView(LoginRequiredMixin, UpdateView):

    form_class = ShiftForm
    model = Shift
    template_name = 'shift_edit.html'
    success_url = reverse_lazy('shifts')
