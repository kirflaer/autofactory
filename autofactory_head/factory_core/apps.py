from django.apps import AppConfig

from .signals import operation_pre_close


class FactoryCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'factory_core'

    def ready(self):
        from warehouse_management import signals

        operation_pre_close.connect(signals.pre_close_movement_shipment)
