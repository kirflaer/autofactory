from django.contrib import admin
from .models import ShiftOperation


class ShiftAdmin(admin.ModelAdmin):
    list_display = ('pk', 'date', 'guid', 'line', 'author', 'batch_number', 'closed')


admin.site.register(ShiftOperation, ShiftAdmin)
