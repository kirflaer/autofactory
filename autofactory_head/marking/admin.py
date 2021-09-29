from django.contrib import admin
from .models import DeviceSignal, RawMark, MarkingOperation, MarkingOperationMarks


class DeviceSignalAdmin(admin.ModelAdmin):
    list_display = ('date', 'device')


class RawMarkAdmin(admin.ModelAdmin):
    list_display = ('date', 'device', 'mark')


class MarkingOperationAdmin(admin.ModelAdmin):
    list_display = ('pk', 'date', 'author')


class MarkingOperationMarksAdmin(admin.ModelAdmin):
    list_display = ('operation', 'product', 'mark', 'encoded_mark',)


admin.site.register(DeviceSignal, DeviceSignalAdmin)
admin.site.register(RawMark, RawMarkAdmin)
admin.site.register(MarkingOperation, MarkingOperationAdmin)
admin.site.register(MarkingOperationMarks, MarkingOperationMarksAdmin)

