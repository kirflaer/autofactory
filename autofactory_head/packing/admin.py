from django.contrib import admin
from .models import (
    RawMark,
    MarkingOperation,
    MarkingOperationMark,
    PalletCode,
    Pallet,
    Task,
    TaskProduct,
    TaskPallet
)


class RawMarkAdmin(admin.ModelAdmin):
    list_display = ('operation', 'mark')
    list_filter = ('operation',)


class MarkingOperationAdmin(admin.ModelAdmin):
    list_display = (
        'number', 'guid', 'date', 'author', 'device', 'manual_editing',
        'closed', 'ready_to_unload', 'unloaded', 'line', 'batch_number')


class MarkingOperationMarkAdmin(admin.ModelAdmin):
    list_display = ('operation', 'product', 'mark', 'encoded_mark',)
    list_filter = ('operation',)


class PalletAdmin(admin.ModelAdmin):
    list_display = ('date', 'guid', 'id',)


class PalletCodesAdmin(admin.ModelAdmin):
    list_display = ('pallet', 'code')


class TaskAdmin(admin.ModelAdmin):
    list_display = ('date', 'number', 'type_task', 'status')


class TaskProductsAdmin(admin.ModelAdmin):
    list_display = ('task', 'product', 'weight')


class TaskPalletsAdmin(admin.ModelAdmin):
    list_display = ('task', 'pallet')


admin.site.register(MarkingOperation, MarkingOperationAdmin)
admin.site.register(MarkingOperationMark, MarkingOperationMarkAdmin)
admin.site.register(Pallet, PalletAdmin)
admin.site.register(PalletCode, PalletCodesAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(TaskProduct, TaskProductsAdmin)
admin.site.register(TaskPallet, TaskPalletsAdmin)
admin.site.register(RawMark, RawMarkAdmin)
