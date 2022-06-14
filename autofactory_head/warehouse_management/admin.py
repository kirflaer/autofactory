from django.contrib import admin

from warehouse_management.models import (
    AcceptanceOperation,
    Pallet,
    OperationPallet,
    OperationProduct,
    PalletCollectOperation
)


@admin.register(AcceptanceOperation)
class AcceptanceOperationAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'guid', 'user', 'number', 'type_task', 'status', 'external_source',
        'closed', 'ready_to_unload', 'unloaded')


@admin.register(PalletCollectOperation)
class PalletCollectOperationAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'guid', 'user', 'number', 'type_task', 'status', 'external_source',
        'closed', 'ready_to_unload', 'unloaded')


@admin.register(Pallet)
class PalletAdmin(admin.ModelAdmin):
    list_display = ('creation_date', 'status', 'collector', 'product', 'id')


@admin.register(OperationPallet)
class OperationPalletAdmin(admin.ModelAdmin):
    list_display = ('pallet', 'type_operation', 'external_source')


@admin.register(OperationProduct)
class OperationPalletAdmin(admin.ModelAdmin):
    list_display = ('product', 'type_operation', 'external_source')
