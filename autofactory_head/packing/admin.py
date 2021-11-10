from django.contrib import admin
from .models import RawMark, MarkingOperation, MarkingOperationMarks


class RawMarkAdmin(admin.ModelAdmin):
    list_display = ('operation', 'date', 'mark')


class MarkingOperationAdmin(admin.ModelAdmin):
    list_display = (
        'number', 'guid', 'date', 'author', 'device', 'manual_editing',
        'closed', 'ready_to_unload', 'unloaded', 'line', 'batch_number')


class MarkingOperationMarksAdmin(admin.ModelAdmin):
    list_display = ('operation', 'product', 'mark', 'encoded_mark',)


admin.site.register(RawMark, RawMarkAdmin)
admin.site.register(MarkingOperation, MarkingOperationAdmin)
admin.site.register(MarkingOperationMarks, MarkingOperationMarksAdmin)
