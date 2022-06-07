from django.contrib import admin

from tasks.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'guid', 'number', 'type_task', 'status', 'external_source',
        'closed', 'ready_to_unload', 'unloaded')
