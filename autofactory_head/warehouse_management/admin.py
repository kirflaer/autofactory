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
    PalletSource
)


@admin.register(Pallet)
class PalletAdmin(admin.ModelAdmin):
    list_display = ('creation_date', 'status', 'collector', 'product', 'id', 'external_key', 'guid')
    list_filter = (('creation_date', DateRangeFilter), 'status')
    ordering = ('-creation_date',)
    search_fields = ('id',)


@admin.register(PalletSource)
class PalletSourceAdmin(admin.ModelAdmin):
    list_display = ('pallet', 'pallet_source', 'product', 'weight', 'count', 'batch_number', 'production_date')


@admin.register(OperationPallet)
class OperationPalletAdmin(admin.ModelAdmin):
    list_display = ('operation', 'pallet', 'type_operation', 'external_source')
    list_filter = ('type_operation',)
    search_fields = ('pallet__id',)


@admin.register(OperationProduct)
class OperationPalletAdmin(admin.ModelAdmin):
    list_display = ('product', 'type_operation', 'external_source')


@admin.register(AcceptanceOperation)
class AcceptanceOperationAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'guid', 'user', 'number', 'type_task', 'status', 'external_source',
        'closed', 'ready_to_unload', 'unloaded')


@admin.register(PalletCollectOperation)
class PalletCollectOperationAdmin(admin.ModelAdmin):
    list_filter = ('type_collect',)
    list_display = (
        'date', 'guid', 'user', 'type_collect', 'number', 'status', 'external_source',
        'closed', 'ready_to_unload', 'unloaded')
    search_fields = ('guid',)


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
    list_display = (
        'date', 'guid', 'user', 'number', 'external_source', 'status', 'closed', 'ready_to_unload', 'unloaded')


@admin.register(OrderOperation)
class OrderOperationAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'guid', 'user', 'number', 'external_source', 'status', 'closed', 'ready_to_unload', 'unloaded')


@admin.register(PalletProduct)
class PalletProductAdmin(admin.ModelAdmin):
    list_display = ('pallet', 'product', 'weight', 'count', 'batch_number', 'production_date')
    search_fields = ('pallet__id',)
