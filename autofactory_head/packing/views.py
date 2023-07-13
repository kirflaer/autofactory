from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods

from factory_core.models import Shift
from packing.forms import MarkingOperationForm, ShiftForm
from packing.marking_services import get_marking_filters, shift_close
from packing.models import (
    MarkingOperation,
    MarkingOperationMark,
)

from warehouse_management.models import PalletContent, Pallet, PalletStatus

from catalogs.models import Line

from django.views.generic import (
    ListView, DeleteView, UpdateView, CreateView,
)

from django.contrib.auth.mixins import LoginRequiredMixin

User = get_user_model()


class OperationBasicListView(LoginRequiredMixin, ListView):
    context_object_name = 'data'


class MarkingOperationListView(OperationBasicListView):
    model = MarkingOperation
    paginate_by = 50
    template_name = 'marking.html'
    ordering = '-date'
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
    template_name = 'confirm_pages/confirm_base.html'


class MarkingOperationUpdateView(LoginRequiredMixin, UpdateView):
    model = MarkingOperation
    form_class = MarkingOperationForm
    success_url = reverse_lazy('marking')
    template_name = 'new_base.html'


class MarkRemoveView(LoginRequiredMixin, DeleteView):
    model = MarkingOperationMark
    success_url = reverse_lazy('marking')
    template_name = 'confirm_pages/confirm_base.html'


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
    marks = MarkingOperationMark.objects.all().filter(operation=operation).order_by('product')

    if len(request.GET) and request.GET.get('mark') is not None:
        marks = marks.filter(mark__startswith=request.GET.get('mark'))

    marks = marks[:100]
    paginator = Paginator(marks, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'marking_detail.html',
                  {'page_obj': page_obj, 'paginator': paginator, 'pk': pk, 'mark': request.GET.get('mark')})


class ShiftListView(OperationBasicListView):
    model = Shift
    paginate_by = 50
    template_name = 'shift.html'
    ordering = '-creating_date'
    extra_context = {
        'title': 'Смена',
        'element_new_link': 'shift_new',
        'possibility_of_adding': True
    }

    def get_context_data(self, *, object_list=None, **kwargs):
        context_data = super().get_context_data(object_list=object_list, **kwargs)
        message = self.request.GET.get('message')
        if message is not None:
            context_data['messages'] = [message]
        return context_data

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_superuser or user.is_local_admin:
            return qs[:300]
        return qs.filter(line__storage=user.shop)[:300]


@login_required
@require_http_methods(['POST', 'GET'])
def shift_processing(request):
    if len(request.GET):
        instance = Shift.objects.get(guid=request.GET['shift'])
        pallet_count = Pallet.objects.filter(shift=instance, status=PalletStatus.COLLECTED).count()

        if instance.line.check_collect_pallet and not pallet_count:
            return redirect(
                f'{reverse_lazy("shifts")}?message={"Нет собранных паллет в смене. Закрытие смены невозможно"}')

        return render(request, 'confirm_shift.html', {'shift': request.GET['shift'], 'pallet_count': pallet_count})

    shift_guid = request.POST.get('shift')

    return shift_close(shift_guid)


class ShiftCreateView(LoginRequiredMixin, CreateView):
    model = Shift
    template_name = 'new_shift.html'
    form_class = ShiftForm
    success_url = reverse_lazy('shifts')
    extra_context = {'new_element_text': 'Открытие новой смены'}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        if not (self.request.user.is_superuser or self.request.user.is_local_admin):
            form.fields['line'].queryset = Line.objects.filter(storage=self.request.user.shop)
        return form

    def form_valid(self, form):
        type_shift = self.request.POST.get('type_shift')
        message = ''
        if not type_shift:
            message = f'Не передан тип смены.'

        form_line = form.cleaned_data['line']
        if Shift.objects.filter(line=form_line, closed=False, type=type_shift).exists():
            message = f'Невозможно открыть смену. На линии {form_line} уже открыта смена c типом {type_shift}.'

        if len(message):
            return redirect(f'{reverse_lazy("shifts")}?message={message}')

        shift = form.save(commit=False)
        shift.type = type_shift
        shift.author = self.request.user
        shift.save()
        return super().form_valid(form)
