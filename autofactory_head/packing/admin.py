from django.contrib import admin
from .models import (
    RawMark,
    MarkingOperation,
    MarkingOperationMark,
    CollectCode,
    CollectingOperation
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


class CollectingOperationAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'number', 'guid', 'date', 'author', 'closed',
                    'ready_to_unload', 'unloaded',)


admin.site.register(RawMark, RawMarkAdmin)
admin.site.register(MarkingOperation, MarkingOperationAdmin)
admin.site.register(MarkingOperationMark, MarkingOperationMarkAdmin)
admin.site.register(CollectingOperation, CollectingOperationAdmin)
