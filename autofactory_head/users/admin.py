from django.contrib import admin

from .models import User, Setting, ConfigEvent


@admin.action(description='Установить уровень логирования INFO')
def make_log_level_info(model, request, queryset):
    queryset.update(log_level='INFO')


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'settings', 'line', 'role', 'scanner', 'device', 'is_superuser', 'log_level')
    list_filter = ('role',)
    actions = [make_log_level_info]


class ConfigEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'type_event', 'argument')


class SettingsAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'type_marking_close', 'collect_pallet_mode_is_active')


admin.site.register(Setting, SettingsAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(ConfigEvent, ConfigEventAdmin)
