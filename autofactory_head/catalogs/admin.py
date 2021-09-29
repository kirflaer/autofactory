from django.contrib import admin

from .models import (
    Organization,
    Storage,
    Department,
    Device,
    Line,
    Product,
)


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


class StorageAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


class LineAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'guid')


class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name',)


admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Storage, StorageAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(Line, LineAdmin)
admin.site.register(Product, ProductAdmin)
