from django.contrib import admin
from .models import RawMark, MarkingOperation, MarkingOperationMarks


class RawMarkAdmin(admin.ModelAdmin):
    list_display = ('operation', 'date', 'mark')


class MarkingOperationAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'guid', 'date', 'author', 'manual_editing', 'device', 'closed',
        'ready_to_unload', 'line', 'batch_number')


class MarkingOperationMarksAdmin(admin.ModelAdmin):
    list_display = ('operation', 'product', 'mark', 'encoded_mark',)


admin.site.register(RawMark, RawMarkAdmin)
admin.site.register(MarkingOperation, MarkingOperationAdmin)
admin.site.register(MarkingOperationMarks, MarkingOperationMarksAdmin)