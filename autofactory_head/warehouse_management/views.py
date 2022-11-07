from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView, UpdateView

from warehouse_management.forms import PalletProductForm
from warehouse_management.models import Pallet, ShipmentOperation, OrderOperation, PalletProduct, OperationPallet, \
    PalletSource


class ShipmentListView(LoginRequiredMixin, ListView):
    context_object_name = 'data'
    ordering = '-date'
    model = ShipmentOperation
    template_name = 'shipment.html'
    extra_context = {
        'title': 'Заявки к отгрузке',
    }


class OrderListView(LoginRequiredMixin, ListView):
    context_object_name = 'data'
    ordering = '-date'
    model = OrderOperation
    template_name = 'orders.html'
    extra_context = {
        'title': 'Заказы',
    }

    def get_queryset(self):
        return OrderOperation.objects.filter(parent_task=self.kwargs['parent_task'])


class OrderDetailListView(LoginRequiredMixin, ListView):
    context_object_name = 'data'
    model = PalletProduct
    ordering = '-count'
    template_name = 'orders_detail.html'
    extra_context = {
        'title': 'Номенклатура заказа',
    }

    def get_queryset(self):
        return PalletProduct.objects.filter(order=self.kwargs['order'])


class PalletProductUpdateView(LoginRequiredMixin, UpdateView):
    model = PalletProduct
    form_class = PalletProductForm
    template_name = 'new_base.html'
    success_url = reverse_lazy('shipment')


class SourceListView(LoginRequiredMixin, ListView):
    context_object_name = 'data'
    model = PalletSource
    template_name = 'sources.html'
    extra_context = {
        'title': 'Данные сбора',
    }

    def get_queryset(self):
        return PalletSource.objects.filter(external_key=self.kwargs['key'])


class SourceRemoveView(LoginRequiredMixin, DeleteView):
    model = PalletSource
    template_name = 'confirm_base.html'
    success_url = reverse_lazy('shipment')
