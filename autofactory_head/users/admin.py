from django.contrib import admin

from .models import User, Setting, ConfigEvent


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'settings', 'line', 'role', 'scanner')


class ConfigEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'type_event', 'argument')


class SettingsAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'type_marking_close', 'collect_pallet_mode_is_active')


admin.site.register(Setting, SettingsAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(ConfigEvent, ConfigEventAdmin)
