from django.contrib import admin

from .models import (
    Organization,
    Storage,
    Department,
    Device,
    Line,
    Product,
    Unit,
    LineProduct,
    Log,
    Client,
    Direction,
    TypeFactoryOperation
)


class LogAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'device', 'username', 'app_version', 'server_version')


class TypeFactoryOperationAdmin(admin.ModelAdmin):
    list_display = ('name', 'external_key')


class LineProductAdmin(admin.ModelAdmin):
    list_display = ('line', 'product',)


class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'product',)


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


class DirectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


class StorageAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid', 'mode')


class LineAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid', 'gtin', 'external_key')


class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name',)


admin.site.register(Organization, OrganizationAdmin)
admin.site.register(TypeFactoryOperation, TypeFactoryOperationAdmin)
admin.site.register(Storage, StorageAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(Line, LineAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Unit, UnitAdmin)
admin.site.register(LineProduct, LineProductAdmin)
admin.site.register(Log, LogAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Direction, DirectionAdmin)
