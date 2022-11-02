from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from warehouse_management.models import Pallet, ShipmentOperation, OrderOperation, PalletProduct, OperationPallet


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
    ordering = '-date'
    model = PalletProduct
    template_name = 'orders_detail.html'
    extra_context = {
        'title': 'Номенклатура заказа',
    }

    def get_queryset(self):
        return PalletProduct.objects.filter(order=self.kwargs['order'])
