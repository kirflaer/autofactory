from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from factory_core.models import Shift, ShiftProduct
from .models import (
    RawMark,
    MarkingOperation,
    MarkingOperationMark
)


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('creating_date', 'closing_date', 'author', 'batch_number', 'line', 'closed')
    ordering = ('-creating_date',)
    search_fields = ('batch_number',)


@admin.register(ShiftProduct)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('shift', 'product')
    ordering = ('-shift__creating_date',)
    search_fields = ('shift__batch_number',)


@admin.register(RawMark)
class RawMarkAdmin(admin.ModelAdmin):
    list_display = ('operation', 'mark')
    list_filter = ('operation',)


@admin.register(MarkingOperation)
class MarkingOperationAdmin(admin.ModelAdmin):
    list_display = (
        'number', 'guid', 'date', 'author', 'device', 'is_offline_operation', 'batch_number',
        'closed', 'ready_to_unload', 'unloaded', 'line', 'shift')
    list_filter = (('date', DateRangeFilter), 'author', 'closed', 'ready_to_unload', 'unloaded', 'line',)
    search_fields = ('batch_number', 'number', 'guid', 'group')
    ordering = ('-date',)


@admin.register(MarkingOperationMark)
class MarkingOperationMarkAdmin(admin.ModelAdmin):
    list_display = (
        'operation', 'product', 'mark', 'aggregation_code',)
    list_filter = ('operation__line',)
    search_fields = ('operation__number',)
