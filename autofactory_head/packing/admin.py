from django.contrib import admin
from rangefilter.filters import DateRangeFilter
from .models import (
    RawMark,
    MarkingOperation,
    MarkingOperationMark,
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
    list_filter = (('date', DateRangeFilter), 'author', 'closed', 'ready_to_unload', 'unloaded', 'line',)
    search_fields = ('batch_number', 'number')
    ordering = ('-date',)


@admin.register(MarkingOperationMark)
class MarkingOperationMarkAdmin(admin.ModelAdmin):
    list_display = (
        'operation', 'product', 'mark', 'aggregation_code',)
    list_filter = ('operation__line',)
    search_fields = ('operation__number',)
