from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count
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
    paginate_by = 50
    template_name = 'marking.html'
    extra_context = {
        'title': 'Маркировка',
        'element_new_link': 'organization_new',
    }

    def get_queryset(self):
        queryset = MarkingOperation.objects.all()
        if len(self.request.GET):
            marking_filter = {}
            user = self.request.GET.get('user')
            date_source = self.request.GET.get('date_source')
            if user is not None and user != 'none':
                marking_filter['author_id'] = user
            if date_source is not None and len(date_source):
                date_parse = date_source.split('-')
                marking_filter['date__year'] = int(date_parse[0])
                marking_filter['date__month'] = int(date_parse[1])
                marking_filter['date__day'] = int(date_parse[2])

            if len(marking_filter):
                queryset = queryset.filter(**marking_filter)
        return queryset.order_by('-date')[:100]

    def get_context_data(self, *, object_list=None, **kwargs):
        context_data = super().get_context_data(object_list=object_list, **kwargs)
        context_data['users'] = User.objects.filter(is_local_admin=False, is_active=True, is_superuser=False).order_by(
            'username')
        context_data['user_filter'] = self.request.GET.get('user')
        return context_data


class MarkingOperationRemoveView(LoginRequiredMixin, DeleteView):
    model = MarkingOperation
    success_url = reverse_lazy('marking')
    template_name = 'confirm_base.html'


class MarkRemoveView(LoginRequiredMixin, DeleteView):
    model = MarkingOperationMark
    success_url = reverse_lazy('marking')
    template_name = 'confirm_base.html'


@login_required
def marking_pallets(request, operation):
    operation = get_object_or_404(MarkingOperation, pk=operation)
    codes = MarkingOperationMark.objects.filter(operation=operation).values_list('aggregation_code', flat=True)
    pallets = PalletCode.objects.filter(code__in=codes).values('pallet__id').annotate(count=Count('code'))
    paginator = Paginator(pallets, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'marking_pallets.html',
                  {'page_obj': page_obj, 'paginator': paginator, 'operation': operation.guid})


@login_required
def marking_pallets_detail(request, operation, pallet):
    operation = get_object_or_404(MarkingOperation, pk=operation)
    aggregation_code = PalletCode.objects.filter(pallet__id=pallet).values_list('code', flat=True)
    marks = MarkingOperationMark.objects.filter(operation=operation, aggregation_code__in=aggregation_code).values(
        'aggregation_code').annotate(count=Count('mark'))

    paginator = Paginator(marks, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'marking_pallets_detail.html', {'page_obj': page_obj, 'paginator': paginator})


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
