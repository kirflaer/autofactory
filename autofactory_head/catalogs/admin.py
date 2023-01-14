from django.contrib import admin

from .models import (ActivationKey, Client, Department, Device, Direction,
                     Line, LineProduct, Log, Organization, Product,
                     RegularExpression, Storage, TypeFactoryOperation, Unit, ExternalSource)


@admin.register(ExternalSource)
class ExternalSourceAdmin(admin.ModelAdmin):
    list_display = ('creation_date', 'date', 'number', 'external_key', 'name')
    search_fields = ('external_key', 'number')


@admin.register(ActivationKey)
class ActivationKeyAdmin(admin.ModelAdmin):
    list_display = (
        'number', 'type_activation', 'date',)


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('date', 'device', 'username', 'app_version', 'server_version')
    search_fields = ('username',)


@admin.register(TypeFactoryOperation)
class TypeFactoryOperationAdmin(admin.ModelAdmin):
    list_display = ('name', 'external_key')


@admin.register(LineProduct)
class LineProductAdmin(admin.ModelAdmin):
    list_display = ('line', 'product',)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'product',)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid', 'external_key')


@admin.register(Storage)
class StorageAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid', 'mode', 'activation_key', 'identifier')
    list_filter = ('mode',)


@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid', 'gtin', 'external_key')


@admin.register(RegularExpression)
class RegularExpressionAdmin(admin.ModelAdmin):
    list_display = ('value', 'type_expression')
