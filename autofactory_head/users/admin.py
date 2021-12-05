from django.contrib import admin

from .models import User, Setting, ServiceEvent


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'settings', 'line', 'role', 'scanner')


class ServiceEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'type_event', 'argument')


class SettingsAdmin(admin.ModelAdmin):
    list_display = ('type_marking_close',)


admin.site.register(Setting, SettingsAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(ServiceEvent, ServiceEventAdmin)
