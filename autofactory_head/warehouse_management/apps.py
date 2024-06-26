from django.apps import AppConfig


class WarehouseManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'warehouse_management'
    verbose_name = 'Управление складом'

    def ready(self):
        from . import signals
