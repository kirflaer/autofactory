from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from warehouse_management.models import (
    AcceptanceOperation,
    Pallet,
    OperationPallet,
    OperationProduct,
    PalletCollectOperation,
    PlacementToCellsOperation,
    MovementBetweenCellsOperation,
    ShipmentOperation,
    PalletProduct,
    OrderOperation,
    PalletSource, ArrivalAtStockOperation, InventoryOperation, OperationCell, SelectionOperation, StorageCell,
    StorageArea, StorageCellContentState, RepackingOperation
)


@admin.action(description='Принять паллеты')
def make_pallet_confirmed(model, request, queryset):
    queryset.update(status='CONFIRMED')


@admin.register(Pallet)
class PalletAdmin(admin.ModelAdmin):
    list_display = ('creation_date', 'status', 'collector', 'product', 'id', 'external_key', 'guid')
    list_filter = (('creation_date', DateRangeFilter), 'status')
    ordering = ('-creation_date',)
    search_fields = ('id', 'marking_group', 'guid')
    actions = [make_pallet_confirmed]


@admin.register(PalletSource)
class PalletSourceAdmin(admin.ModelAdmin):
    list_display = ('pallet', 'pallet_source', 'product', 'weight', 'count', 'batch_number', 'production_date')


@admin.register(OperationPallet)
class OperationPalletAdmin(admin.ModelAdmin):
    list_display = ('operation', 'pallet', 'type_operation', 'number_operation', 'external_source')
    list_filter = ('type_operation',)
    search_fields = ('pallet__id', 'operation')


@admin.register(OperationProduct)
class OperationProductAdmin(admin.ModelAdmin):
    list_display = ('product', 'type_operation', 'external_source')
    list_filter = ('type_operation',)
    search_fields = ('operation',)


@admin.register(OperationCell)
class OperationPalletAdmin(admin.ModelAdmin):
    list_display = ('operation', 'cell_source', 'cell_destination', 'pallet')
    search_fields = ('operation',)


@admin.register(AcceptanceOperation)
class AcceptanceOperationAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'guid', 'user', 'number', 'type_task', 'status', 'external_source',
        'closed', 'ready_to_unload', 'unloaded')


@admin.register(PalletCollectOperation)
class PalletCollectOperationAdmin(admin.ModelAdmin):
    list_filter = (('date', DateRangeFilter), 'type_collect', 'ready_to_unload', 'unloaded')
    list_display = (
        'date', 'guid', 'user', 'type_collect', 'number', 'status', 'external_source',
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


@admin.register(OrderOperation)
class OrderOperationAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'guid', 'user', 'number', 'parent_task', 'external_source', 'status', 'closed', 'ready_to_unload',
        'unloaded')


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
    list_display = (
        'date', 'guid', 'number', 'status', 'external_source', 'closed', 'ready_to_unload', 'unloaded')


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


@admin.register(RepackingOperation)
class RepackingOperationAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'guid', 'user', 'number', 'external_source', 'status', 'closed', 'ready_to_unload', 'unloaded')
