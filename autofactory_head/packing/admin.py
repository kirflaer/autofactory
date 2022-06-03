from django.contrib import admin
from .models import (
    RawMark,
    MarkingOperation,
    MarkingOperationMark,
    # PalletCode,
    # Pallet,
    # Task,
    # TaskProduct,
    # TaskPallet
)


@admin.register(RawMark)
class RawMarkAdmin(admin.ModelAdmin):
    list_display = ('operation', 'mark')
    list_filter = ('operation',)


@admin.register(MarkingOperation)
class MarkingOperationAdmin(admin.ModelAdmin):
    list_display = (
        'number', 'guid', 'date', 'author', 'device', 'manual_editing',
        'closed', 'ready_to_unload', 'unloaded', 'line', 'batch_number')
    list_filter = ('author', 'closed', 'ready_to_unload', 'unloaded', 'line',)
    search_fields = ('batch_number', 'number')


@admin.register(MarkingOperationMark)
class MarkingOperationMarkAdmin(admin.ModelAdmin):
    list_display = (
        'operation', 'product', 'mark', 'aggregation_code', )
    list_filter = ('operation__line',)
    search_fields = ('operation__number',)


# TODO: Вынести в отдельное приложение
# @admin.register(Pallet)
# class PalletAdmin(admin.ModelAdmin):
#     list_display = ('date', 'guid', 'id', 'product')
#     search_fields = ('id',)
#
#
# @admin.register(PalletCode)
# class PalletCodesAdmin(admin.ModelAdmin):
#     list_display = ('pallet', 'code',)
#     search_fields = ('pallet__guid',)
#
#
# @admin.register(Task)
# class TaskAdmin(admin.ModelAdmin):
#     list_display = (
#         'date', 'guid', 'number', 'type_task', 'status', 'external_source',
#         'closed', 'ready_to_unload', 'unloaded')
#
#
# @admin.register(TaskProduct)
# class TaskProductsAdmin(admin.ModelAdmin):
#     list_display = ('task', 'product', 'weight')
#
#
# @admin.register(TaskPallet)
# class TaskPalletsAdmin(admin.ModelAdmin):
#     list_display = ('task', 'pallet')
