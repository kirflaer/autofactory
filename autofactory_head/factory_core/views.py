from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy

from packing.marking_services import get_dashboard_data
from catalogs.models import (
    Device,
    Log
)

from packing.models import (
    MarkingOperation,
    MarkingOperationMark,
    PalletCode,
    Pallet,
    Task
)

from catalogs.models import Line

from django.views.generic import (
    ListView, DeleteView,
)

from .log_services import logs_summary_data, log_line_decode

from django.contrib.auth.mixins import LoginRequiredMixin

User = get_user_model()


@login_required
def index(request):
    dashboard_data = get_dashboard_data()
    dashboard_data['version'] = settings.VERSION
    return render(request, 'index.html', dashboard_data)


class OperationBasicListView(LoginRequiredMixin, ListView):
    context_object_name = 'data'
    ordering = '-date'


class MarkingOperationListView(OperationBasicListView):
    model = MarkingOperation
    paginate_by = 40
    template_name = 'marking.html'
    extra_context = {
        'title': 'Маркировка',
        'element_new_link': 'organization_new',
        'lines': Line.objects.all()
    }


class MarkingOperationRemoveView(LoginRequiredMixin, DeleteView):
    model = MarkingOperation
    success_url = reverse_lazy('marking')
    template_name = 'confirm_base.html'


class MarkRemoveView(LoginRequiredMixin, DeleteView):
    model = MarkingOperationMark
    success_url = reverse_lazy('marking')
    template_name = 'confirm_base.html'


@login_required
def marking_detail(request, pk):
    operation = get_object_or_404(MarkingOperation, pk=pk)
    marks = MarkingOperationMark.objects.all().filter(operation=operation).order_by('product')[:100]

    paginator = Paginator(marks, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'marking_detail.html', {'page_obj': page_obj, 'paginator': paginator})


def check_status_view(request):
    return render(request, 'check_form.html')


class PalletListView(OperationBasicListView):
    model = Pallet
    template_name = 'pallet.html'
    extra_context = {
        'title': 'Собранные паллеты',
    }


class TaskListView(OperationBasicListView):
    model = Task
    template_name = 'tasks.html'
    extra_context = {
        'title': 'Задания',
    }


class LogListView(LoginRequiredMixin, ListView):
    model = Log
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
def pallet_detail(request, pk):
    pallet = get_object_or_404(Pallet, pk=pk)
    codes = PalletCode.objects.all().filter(pallet=pallet)
    return render(request, 'pallet_codes.html', {'data': codes})


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
