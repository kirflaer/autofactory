from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy

from packing.forms import MarkingOperationForm
from packing.marking_services import get_marking_filters
from packing.models import (
    MarkingOperation,
    MarkingOperationMark,
)

from warehouse_management.models import PalletContent

from catalogs.models import Line

from django.views.generic import (
    ListView, DeleteView, UpdateView,
)

from django.contrib.auth.mixins import LoginRequiredMixin

User = get_user_model()


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
            marking_filter = get_marking_filters(self.request.GET)
            # TODO: можеть быть ошибка если передан некорректный параметр. нужна проверка как в api
            if len(marking_filter):
                queryset = queryset.filter(**marking_filter)
        return queryset.order_by('-date')[:200]

    def get_context_data(self, *, object_list=None, **kwargs):
        context_data = super().get_context_data(object_list=object_list, **kwargs)
        context_data['users'] = User.objects.filter(is_local_admin=False, is_active=True, is_superuser=False).order_by(
            'username')
        context_data['lines'] = Line.objects.all().order_by('name')
        context_data['line_filter'] = self.request.GET.get('line')
        context_data['batch_number'] = self.request.GET.get('batch_number')
        context_data['user_filter'] = self.request.GET.get('user')
        return context_data


class MarkingOperationRemoveView(LoginRequiredMixin, DeleteView):
    model = MarkingOperation
    success_url = reverse_lazy('marking')
    template_name = 'confirm_base.html'


class MarkingOperationUpdateView(LoginRequiredMixin, UpdateView):
    model = MarkingOperation
    form_class = MarkingOperationForm
    success_url = reverse_lazy('marking')
    template_name = 'new_base.html'


class MarkRemoveView(LoginRequiredMixin, DeleteView):
    model = MarkingOperationMark
    success_url = reverse_lazy('marking')
    template_name = 'confirm_base.html'


@login_required
def marking_pallets(request, operation):
    operation = get_object_or_404(MarkingOperation, pk=operation)
    aggregation_codes = MarkingOperationMark.objects.filter(operation=operation).values_list('aggregation_code',
                                                                                             flat=True)
    pallets = PalletContent.objects.filter(aggregation_code__in=aggregation_codes).values(
        'pallet__id').annotate(count=Count('aggregation_code'))
    paginator = Paginator(pallets, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'marking_pallets.html',
                  {'page_obj': page_obj, 'paginator': paginator, 'operation': operation.guid})


@login_required
def marking_pallets_detail(request, operation, pallet):
    operation = get_object_or_404(MarkingOperation, pk=operation)
    aggregation_code = PalletContent.objects.filter(pallet__id=pallet).values_list('code', flat=True)
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


