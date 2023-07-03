from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView, UpdateView

from warehouse_management.forms import PalletProductForm
from warehouse_management.models import (
    Pallet, ShipmentOperation, OrderOperation, PalletProduct, PalletSource, OperationCell,
    InventoryAddressWarehouseOperation
)


class ShipmentListView(LoginRequiredMixin, ListView):
    context_object_name = 'data'
    ordering = '-date'
    paginate_by = 50
    model = ShipmentOperation
    template_name = 'shipment.html'
    extra_context = {
        'title': 'Заявки к отгрузке',
    }

    def get_queryset(self):
        return super().get_queryset()[:200]


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
    template_name = 'orders_detail.html'
    extra_context = {
        'title': 'Номенклатура заказа',
    }

    def get_queryset(self):
        return PalletProduct.objects.filter(order=self.kwargs['order']).order_by('pallet__name')


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


class PalletListView(LoginRequiredMixin, ListView):
    context_object_name = 'data'
    model = Pallet
    template_name = 'shipment_pallet.html'
    extra_context = {
        'title': 'Паллеты заявки',
    }

    def get_queryset(self):
        pallet_ids = OperationCell.objects.filter(operation=self.kwargs['parent_task']).values_list('pallet__guid',
                                                                                                    flat=True)
        return Pallet.objects.filter(guid__in=list(pallet_ids))


class PalletDetailView(LoginRequiredMixin, ListView):
    context_object_name = 'data'
    model = PalletSource
    template_name = 'shipment_pallet_sources.html'
    extra_context = {
        'title': 'Паллеты назначения',
    }

    def get_queryset(self):
        return PalletSource.objects.filter(pallet_source=self.kwargs['pallet'])
