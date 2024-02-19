from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView, UpdateView

from warehouse_management.forms import (
    PalletProductForm,
    PalletForm,
    PalletCollectOperationForm,
    OperationPalletForm,
    StorageCellContentStateForm,
    SelectionOperationForm,
    OrderOperationForm,
    ShipmentOperationForm,
    CancelShipmentOperationForm,
    MovementBetweenCellsForm,
    AcceptanceOperationForm,
    PlacementToCellsOperationForm,
    WriteOffOperationForm,
)
from warehouse_management.models import (
    Pallet, ShipmentOperation, OrderOperation, PalletProduct, PalletSource, OperationCell,
    OperationPallet, PalletCollectOperation, StorageCellContentState, SelectionOperation, CancelShipmentOperation,
    MovementBetweenCellsOperation, AcceptanceOperation, PlacementToCellsOperation, WriteOffOperation,
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


class ShipmentOperationUpdateView(LoginRequiredMixin, UpdateView):

    model = ShipmentOperation
    form_class = ShipmentOperationForm
    template_name = 'shipment_operation_edit.html'
    success_url = reverse_lazy('shipment')


class ShipmentOperationDeleteView(LoginRequiredMixin, DeleteView):

    model = ShipmentOperation
    template_name = 'confirm_base.html'
    success_url = reverse_lazy('shipment')


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


class OrderOperationListView(OrderListView):

    paginate_by = 50

    def get_queryset(self):
        return OrderOperation.objects.latest().order_by(self.get_ordering())[:500]


class OrderOperationUpdateView(LoginRequiredMixin, UpdateView):

    model = OrderOperation
    form_class = OrderOperationForm
    template_name = 'order_operation_edit.html'
    success_url = reverse_lazy('order_operation_list')

    def form_valid(self, form):
        return super().form_valid(form)


class OrderOperationDeleteView(LoginRequiredMixin, DeleteView):

    model = OrderOperation
    template_name = 'confirm_base.html'
    success_url = reverse_lazy('order_operation_list')


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


class PalletShipmentListView(LoginRequiredMixin, ListView):
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


class PalletListView(LoginRequiredMixin, ListView):

    context_object_name = 'data'
    model = Pallet
    template_name = 'pallets_list.html'
    ordering = ['-creation_date']
    paginate_by = 50
    extra_context = {
        'title': 'Паллеты',
    }

    def get_queryset(self):
        return Pallet.objects.all()[:500]


class PalletUpdateView(LoginRequiredMixin, UpdateView):

    model = Pallet
    template_name = 'pallet_detail.html'
    form_class = PalletForm
    success_url = reverse_lazy('pallets_list')


class PalletOperationListView(LoginRequiredMixin, ListView):

    context_object_name = 'data'
    model = OperationPallet
    template_name = 'pallet_operations.html'
    paginate_by = 50
    extra_context = {
        'title': OperationPallet._meta.verbose_name_plural
    }

    def get_queryset(self):
        queryset = OperationPallet.objects.all().order_by('-guid')
        if len(self.request.GET):
            filter_set = self.validate(OperationPalletForm(self.request.GET))
            if filter_set:
                queryset = queryset.filter(**filter_set)

        return queryset[:500]

    @staticmethod
    def validate(form: OperationPalletForm) -> dict | None:
        if form.is_valid():
            filter_set = {k: v for k, v in form.cleaned_data.items() if v is not None}
            if len(filter_set):
                return filter_set

    def get_context_data(self, *, object_list=None, **kwargs):

        context = super().get_context_data(object_list=object_list, **kwargs)
        context['form'] = OperationPalletForm(initial=self.request.GET)
        return context


class PalletCollectOperationListView(LoginRequiredMixin, ListView):

    context_object_name = 'data'
    model = PalletCollectOperation
    template_name = 'pallet_collect_operation_list.html'
    paginate_by = 50
    extra_context = {
        'title': PalletCollectOperation._meta.verbose_name_plural
    }

    def get_queryset(self):
        return PalletCollectOperation.objects.all().order_by('-guid')[:500]


class PalletCollectOperationUpdateView(LoginRequiredMixin, UpdateView):

    model = PalletCollectOperation
    template_name = 'pallet_collect_operation_edit.html'
    form_class = PalletCollectOperationForm
    success_url = reverse_lazy('pallet_collect_operation_list')


class StorageCellContentStateListView(LoginRequiredMixin, ListView):

    context_object_name = 'data'
    model = StorageCellContentState
    template_name = 'storage_cell_content_state_list.html'
    paginate_by = 50
    extra_context = {
        'title': StorageCellContentState._meta.verbose_name_plural,
        'catalog_edit_link': 'storage_cell_content_state_edit',
        'catalog_remove_link': 'storage_cell_content_state_delete',
    }

    def get_queryset(self):
        return StorageCellContentState.objects.all().order_by('-creating_date')[:500]


class StorageCellContentStateUpdateView(LoginRequiredMixin, UpdateView):

    model = StorageCellContentState
    template_name = 'storage_cell_content_state_edit.html'
    form_class = StorageCellContentStateForm
    success_url = reverse_lazy('storage_cell_content_state_list')


class StorageCellContentStateDeleteView(LoginRequiredMixin, DeleteView):

    model = StorageCellContentState
    template_name = 'confirm_base.html'
    success_url = reverse_lazy('storage_cell_content_state_list')


class SelectionOperationListView(LoginRequiredMixin, ListView):

    context_object_name = 'data'
    model = SelectionOperation
    template_name = 'selection_operation_list.html'
    paginate_by = 50
    ordering = ['-date']
    extra_context = {
        'title': SelectionOperation._meta.verbose_name_plural
    }


class SelectionOperationUpdateView(LoginRequiredMixin, UpdateView):

    model = SelectionOperation
    form_class = SelectionOperationForm
    template_name = 'selection_operation_edit.html'
    success_url = reverse_lazy('selection_operation_list')


class SelectionOperationDeleteView(LoginRequiredMixin, DeleteView):

    model = SelectionOperation
    template_name = 'confirm_base.html'
    success_url = reverse_lazy('selection_operation_list')


class CancelShipmentOperationListView(LoginRequiredMixin, ListView):

    context_object_name = 'data'
    model = CancelShipmentOperation
    template_name = 'cancel_shipment_operation_list.html'
    paginate_by = 50
    ordering = ['-date']
    extra_context = {
        'title': CancelShipmentOperation._meta.verbose_name_plural
    }


class CancelShipmentOperationUpdateView(LoginRequiredMixin, UpdateView):

    model = CancelShipmentOperation
    form_class = CancelShipmentOperationForm
    template_name = 'cancel_shipment_operation_edit.html'
    success_url = reverse_lazy('cancel_shipment_operation_list')


class CancelShipmentOperationDeleteView(LoginRequiredMixin, DeleteView):

    model = CancelShipmentOperation
    template_name = 'confirm_base.html'
    success_url = reverse_lazy('cancel_shipment_operation_list')


class MovementBetweenCellsListView(LoginRequiredMixin, ListView):

    context_object_name = 'data'
    model = MovementBetweenCellsOperation
    template_name = 'movement_between_cells_list.html'
    paginate_by = 50
    ordering = ['-date']
    extra_context = {
        'title': MovementBetweenCellsOperation._meta.verbose_name_plural,
        'catalog_edit_link': 'movement_between_cells_edit',
        'catalog_remove_link': 'movement_between_cells_delete',
    }


class MovementBetweenCellsUpdateView(LoginRequiredMixin, UpdateView):

    model = MovementBetweenCellsOperation
    form_class = MovementBetweenCellsForm
    template_name = 'movement_between_cells_edit.html'
    success_url = reverse_lazy('movement_between_cells_list')

    def form_invalid(self, form):
        f = 1
        return super().form_invalid(form)

    def form_valid(self, form):
        a = 1
        return super().form_valid(form)


class MovementBetweenCellsDeleteView(LoginRequiredMixin, DeleteView):

    model = MovementBetweenCellsOperation
    template_name = 'confirm_base.html'
    success_url = reverse_lazy('movement_between_cells_list')


class AcceptanceOperationListView(LoginRequiredMixin, ListView):

    context_object_name = 'data'
    model = AcceptanceOperation
    template_name = 'acceptance_operation_list.html'
    paginate_by = 50
    ordering = ['-date']
    extra_context = {
        'title': AcceptanceOperation._meta.verbose_name_plural,
        'catalog_edit_link': 'acceptance_operation_edit',
        'catalog_remove_link': 'acceptance_operation_delete',
    }


class AcceptanceOperationUpdateView(LoginRequiredMixin, UpdateView):

    model = AcceptanceOperation
    form_class = AcceptanceOperationForm
    template_name = 'acceptance_operation_edit.html'
    success_url = reverse_lazy('acceptance_operation_list')


class AcceptanceOperationDeleteView(LoginRequiredMixin, DeleteView):

    model = AcceptanceOperation
    template_name = 'confirm_base.html'
    success_url = reverse_lazy('acceptance_operation_list')


class PlacementToCellsOperationListView(LoginRequiredMixin, ListView):

    context_object_name = 'data'
    model = PlacementToCellsOperation
    template_name = 'placement_to_cell_operation_list.html'
    paginate_by = 50
    ordering = ['-date']
    extra_context = {
        'title': PlacementToCellsOperation._meta.verbose_name_plural,
        'catalog_edit_link': 'placement_to_cell_operation_edit',
        'catalog_remove_link': 'placement_to_cell_operation_delete',
    }


class PlacementToCellsOperationUpdateView(LoginRequiredMixin, UpdateView):

    model = PlacementToCellsOperation
    form_class = PlacementToCellsOperationForm
    template_name = 'placement_to_cell_operation_edit.html'
    success_url = reverse_lazy('placement_to_cell_operation_list')


class PlacementToCellsOperationDeleteView(LoginRequiredMixin, DeleteView):

    model = PlacementToCellsOperation
    template_name = 'confirm_base.html'
    success_url = reverse_lazy('placement_to_cell_operation_list')


class WriteOffOperationListView(LoginRequiredMixin, ListView):

    context_object_name = 'data'
    model = WriteOffOperation
    template_name = 'selection_operation_list.html'
    paginate_by = 50
    ordering = ['-date']
    extra_context = {
        'title': WriteOffOperation._meta.verbose_name_plural,
        'catalog_edit_link': 'write_off_operation_edit',
        'catalog_remove_link': 'write_off_operation_delete',
    }


class WriteOffOperationUpdateView(LoginRequiredMixin, UpdateView):

    model = WriteOffOperation
    form_class = WriteOffOperationForm
    template_name = 'write_off_operation_edit.html'
    success_url = reverse_lazy('write_off_operation_list')


class WriteOffOperationDeleteView(LoginRequiredMixin, DeleteView):

    model = WriteOffOperation
    template_name = 'confirm_base.html'
    success_url = reverse_lazy('write_off_operation_list')
