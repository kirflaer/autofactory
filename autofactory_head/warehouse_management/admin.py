from django.contrib import admin
from django.db import transaction
from rangefilter.filters import DateRangeFilter
from rest_framework.exceptions import APIException
from django.contrib import messages

from tasks.models import TaskStatus
from warehouse_management.models import (
    AcceptanceOperation, Pallet, OperationPallet, OperationProduct, PalletCollectOperation, PlacementToCellsOperation,
    MovementBetweenCellsOperation, ShipmentOperation, PalletProduct, OrderOperation, PalletSource,
    ArrivalAtStockOperation, InventoryOperation, OperationCell, SelectionOperation, StorageCell, StorageArea,
    StorageCellContentState, RepackingOperation, SuitablePallets, WriteOffOperation, InventoryAddressWarehouseOperation,
    InventoryAddressWarehouseContent, CancelShipmentOperation, MovementShipmentOperation
)
from warehouse_management.warehouse_services import (get_unused_cells_for_placement,
                                                     create_inventory_with_placement_operation)


@admin.action(description='Отметить паллеты как принятые')
def make_pallet_confirmed(model, request, queryset):
    queryset.update(status='CONFIRMED')


@admin.action(description='Отметить паллеты как размещенные')
def make_pallet_placed(model, request, queryset):
    queryset.update(status='PLACED')


@admin.action(description='Сгенерировать документы инвентаризации')
@transaction.atomic
def create_inventory_operations(model, request, queryset):
    unused_cells = get_unused_cells_for_placement()

    if len(unused_cells) < queryset.count():
        messages.add_message(request, messages.ERROR, 'Свободных ячеек не хватит на выбранные паллеты')
        return

    for pallet in queryset:
        if not len(unused_cells):
            break
        cell = unused_cells.pop()
        data = {'cell': cell.external_key,
                'pallet': pallet.guid,
                'count': pallet.content_count,
                'weight': pallet.weight}
        create_inventory_with_placement_operation(serializer_data=data, user=request.user)
    messages.add_message(request, messages.INFO, 'Документы созданы успешно')


@admin.action(description='Переразместить ячейки')
def make_cells_placed(model, request, queryset):
    ids = list(queryset.values_list('guid', flat=True))
    cells = OperationCell.objects.filter(operation__in=ids)
    for row in cells:
        StorageCellContentState.objects.create(cell=row.cell_source, pallet=row.pallet)


@admin.action(description='Пометить задание как выгруженное')
def make_task_unloaded(model, request, queryset):
    queryset.update(unloaded=True)


@admin.action(description='Пометить задание как не выгруженное')
def make_task_loaded(model, request, queryset):
    queryset.update(unloaded=False)


@admin.action(description='Пометить задание как закрытое')
def make_task_closed(model, request, queryset):
    queryset.update(closed=True, status=TaskStatus.CLOSE)


@admin.register(Pallet)
class PalletAdmin(admin.ModelAdmin):
    list_display = ('creation_date', 'status', 'collector', 'product', 'id', 'external_key', 'guid')
    list_filter = (('creation_date', DateRangeFilter), 'status', 'product__semi_product', 'product__not_marked')
    ordering = ('-creation_date',)
    search_fields = ('id', 'marking_group', 'guid', 'external_task_key')
    actions = [make_pallet_confirmed, make_pallet_placed, create_inventory_operations]


@admin.register(PalletSource)
class PalletSourceAdmin(admin.ModelAdmin):
    list_display = ('pallet', 'pallet_source', 'product', 'weight', 'count', 'batch_number', 'production_date')
    search_fields = ('pallet_source__id', 'pallet_source__guid', 'related_task')
    list_filter = ('type_collect',)


@admin.register(OperationPallet)
class OperationPalletAdmin(admin.ModelAdmin):
    list_display = ('operation', 'pallet', 'type_operation', 'number_operation', 'external_source')
    list_filter = ('type_operation',)
    search_fields = ('pallet__guid', 'pallet__id', 'operation')


@admin.register(OperationProduct)
class OperationProductAdmin(admin.ModelAdmin):
    list_display = ('product', 'type_operation', 'external_source')
    list_filter = ('type_operation',)
    search_fields = ('operation',)


@admin.register(OperationCell)
class OperationPalletAdmin(admin.ModelAdmin):
    list_display = ('operation', 'type_operation', 'cell_source', 'cell_destination', 'pallet')
    search_fields = ('operation', 'pallet__id', 'pallet__guid')
    list_filter = ('type_operation',)


@admin.register(AcceptanceOperation)
class AcceptanceOperationAdmin(admin.ModelAdmin):
    ordering = ('-date',)
    list_filter = (('date', DateRangeFilter), 'unloaded', 'closed')
    list_display = (
        'date', 'guid', 'user', 'number', 'type_task', 'status', 'external_source',
        'closed', 'ready_to_unload', 'unloaded')
    actions = [make_task_unloaded, make_task_closed]


@admin.register(PalletCollectOperation)
class PalletCollectOperationAdmin(admin.ModelAdmin):
    list_filter = (('date', DateRangeFilter), 'type_collect', 'ready_to_unload', 'unloaded', 'user')
    list_display = (
        'date', 'guid', 'user', 'type_collect', 'parent_task', 'number', 'status', 'external_source',
        'closed', 'ready_to_unload', 'unloaded')
    search_fields = ('guid', 'parent_task')
    ordering = ('-date',)


@admin.register(PlacementToCellsOperation)
class PalletCollectOperationAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'guid', 'user', 'number', 'status', 'external_source',
        'closed', 'ready_to_unload', 'unloaded')


@admin.register(MovementBetweenCellsOperation)
class MovementBetweenCellsOperationAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'guid', 'user', 'number', 'status', 'closed', 'ready_to_unload', 'unloaded')


@admin.register(ShipmentOperation)
class ShipmentOperationAdmin(admin.ModelAdmin):
    ordering = ('-date',)
    list_display = (
        'date', 'guid', 'user', 'number', 'external_source', 'has_selection', 'status', 'closed', 'ready_to_unload',
        'unloaded')
    search_fields = ('guid', )


@admin.register(OrderOperation)
class OrderOperationAdmin(admin.ModelAdmin):
    ordering = ('-date',)
    list_display = (
        'date', 'guid', 'user', 'number', 'parent_task', 'external_source', 'status', 'closed', 'ready_to_unload',
        'unloaded')
    search_fields = ('parent_task',)


@admin.register(PalletProduct)
class PalletProductAdmin(admin.ModelAdmin):
    list_display = ('pallet', 'product', 'weight', 'count', 'batch_number', 'production_date')
    search_fields = ('pallet__id', 'pallet__guid')


@admin.register(ArrivalAtStockOperation)
class ArrivalAtStockOperationAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'guid', 'storage', 'number', 'status', 'external_source',
        'closed', 'ready_to_unload', 'unloaded')


@admin.register(InventoryOperation)
class InventoryOperationAdmin(admin.ModelAdmin):
    list_filter = (('date', DateRangeFilter), 'ready_to_unload', 'unloaded')
    list_display = (
        'date', 'guid', 'number', 'status', 'external_source', 'closed', 'ready_to_unload', 'unloaded')
    actions = [make_task_loaded, make_cells_placed]
    search_fields = ('number', 'guid')
    ordering = ('-date',)


@admin.register(SelectionOperation)
class SelectionOperationAdmin(admin.ModelAdmin):
    ordering = ('-date',)
    list_filter = (('date', DateRangeFilter), 'status')
    list_display = (
        'date', 'guid', 'user', 'number', 'external_source', 'status', 'closed', 'ready_to_unload', 'unloaded')


@admin.register(StorageCell)
class CellsAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid', 'external_key', 'storage_area')
    list_filter = ('storage_area',)
    search_fields = ('external_key', 'name')


@admin.register(StorageArea)
class StorageAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid', 'external_key')


@admin.register(StorageCellContentState)
class StorageCellContentStateAdmin(admin.ModelAdmin):
    list_display = ('creating_date', 'cell', 'pallet', 'status')
    search_fields = ('cell__name', 'pallet__id', 'pallet__guid')
    list_filter = ('status', ('creating_date', DateRangeFilter),)


@admin.register(RepackingOperation)
class RepackingOperationAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'guid', 'user', 'number', 'external_source', 'status', 'closed', 'ready_to_unload', 'unloaded')


@admin.register(SuitablePallets)
class SuitablePalletsAdmin(admin.ModelAdmin):
    list_display = ('pallet_product', 'pallet', 'count',)


@admin.register(WriteOffOperation)
class SuitablePalletsAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'guid', 'user', 'number', 'external_source', 'status', 'closed', 'ready_to_unload', 'unloaded')


@admin.register(InventoryAddressWarehouseOperation)
class InventoryAddressWarehouse(admin.ModelAdmin):
    list_display = (
        'date', 'guid', 'user', 'number', 'external_source', 'status', 'closed', 'ready_to_unload', 'unloaded')


@admin.register(InventoryAddressWarehouseContent)
class InventoryAddressWarehouseContentAdmin(admin.ModelAdmin):
    list_display = ('guid', 'product', 'pallet', 'cell')


@admin.register(CancelShipmentOperation)
class CancelShipmentOperationAdmin(admin.ModelAdmin):
    list_display = ('date', 'guid', 'user', 'number', 'status', 'closed', 'ready_to_unload', 'unloaded')


@admin.register(MovementShipmentOperation)
class MovementShipmentOperationAdmin(admin.ModelAdmin):
    list_display = ('date', 'guid', 'user', 'number', 'status', 'closed', 'ready_to_unload', 'unloaded')
